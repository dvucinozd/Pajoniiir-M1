#![no_std]
#![forbid(unsafe_code)]

use core::fmt;
use core::num::NonZeroU32;

use pajoniiir_media_block::{BlockDevice, BlockGeometry, TransferError, WritableBlockDevice};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UsbMscCapacity {
    pub block_size: u32,
    pub block_count: u64,
}

impl UsbMscCapacity {
    pub const fn from_block_count(block_size: u32, block_count: u64) -> Option<Self> {
        if block_size == 0 || block_count == 0 {
            None
        } else {
            Some(Self {
                block_size,
                block_count,
            })
        }
    }

    /// Convert SCSI READ CAPACITY's last logical block address into a count.
    pub const fn from_last_lba(block_size: u32, last_lba: u64) -> Option<Self> {
        match last_lba.checked_add(1) {
            Some(block_count) => Self::from_block_count(block_size, block_count),
            None => None,
        }
    }

    pub const fn geometry(self) -> BlockGeometry {
        BlockGeometry {
            block_size: self.block_size,
            block_count: self.block_count,
        }
    }
}

/// Completed USB mass-storage command transport.
///
/// The ESP32-P4 binding may be driven by an async USB host task. This trait is
/// intentionally the synchronous completion boundary consumed by the media
/// worker; USB endpoint/DMA ownership must not leak into filesystem code.
pub trait UsbMscTransport {
    type Error;

    fn read_blocks(
        &mut self,
        lun: u8,
        first_block: u64,
        block_count: u32,
        output: &mut [u8],
    ) -> Result<(), Self::Error>;
}

pub trait WritableUsbMscTransport: UsbMscTransport {
    fn write_blocks(
        &mut self,
        lun: u8,
        first_block: u64,
        block_count: u32,
        input: &[u8],
    ) -> Result<(), Self::Error>;

    fn synchronize_cache(&mut self, lun: u8) -> Result<(), Self::Error>;
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UsbMscConfigError {
    InvalidGeometry,
}

impl fmt::Display for UsbMscConfigError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidGeometry => formatter.write_str("invalid USB MSC block geometry"),
        }
    }
}

impl core::error::Error for UsbMscConfigError {}

#[derive(Debug, Eq, PartialEq)]
pub enum UsbMscError<E> {
    Disconnected,
    TooManyBlocks { requested: u32, maximum: u32 },
    Transfer(TransferError),
    Backend(E),
}

impl<E: fmt::Display> fmt::Display for UsbMscError<E> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Disconnected => formatter.write_str("USB mass-storage device disconnected"),
            Self::TooManyBlocks { requested, maximum } => {
                write!(
                    formatter,
                    "USB MSC transfer requests {requested} blocks; maximum is {maximum}"
                )
            }
            Self::Transfer(error) => {
                write!(formatter, "USB MSC transfer contract error: {error:?}")
            }
            Self::Backend(error) => write!(formatter, "USB MSC transport error: {error}"),
        }
    }
}

impl<E> core::error::Error for UsbMscError<E> where E: core::error::Error + 'static {}

/// Generation-local USB mass-storage block adapter.
///
/// Once `disconnect` is called this adapter is terminal. Re-enumeration must
/// construct a new adapter so stale filesystem owners cannot silently become
/// valid against a different device that reused the same USB address.
pub struct UsbMscBlockDevice<T> {
    transport: T,
    lun: u8,
    geometry: BlockGeometry,
    max_blocks_per_transfer: NonZeroU32,
    connected: bool,
}

impl<T> UsbMscBlockDevice<T> {
    pub fn new(
        transport: T,
        lun: u8,
        capacity: UsbMscCapacity,
        max_blocks_per_transfer: NonZeroU32,
    ) -> Result<Self, UsbMscConfigError> {
        let geometry = capacity.geometry();
        if !geometry.is_valid() {
            return Err(UsbMscConfigError::InvalidGeometry);
        }

        Ok(Self {
            transport,
            lun,
            geometry,
            max_blocks_per_transfer,
            connected: true,
        })
    }

    pub const fn lun(&self) -> u8 {
        self.lun
    }

    pub const fn is_connected(&self) -> bool {
        self.connected
    }

    pub const fn max_blocks_per_transfer(&self) -> NonZeroU32 {
        self.max_blocks_per_transfer
    }

    pub fn disconnect(&mut self) {
        self.connected = false;
    }

    pub const fn transport(&self) -> &T {
        &self.transport
    }

    pub fn transport_mut(&mut self) -> &mut T {
        &mut self.transport
    }

    pub fn into_transport(self) -> T {
        self.transport
    }

    fn validate_transfer<E>(
        &self,
        first_block: u64,
        block_count: u32,
        buffer_len: usize,
    ) -> Result<(), UsbMscError<E>> {
        if !self.connected {
            return Err(UsbMscError::Disconnected);
        }
        if block_count > self.max_blocks_per_transfer.get() {
            return Err(UsbMscError::TooManyBlocks {
                requested: block_count,
                maximum: self.max_blocks_per_transfer.get(),
            });
        }

        self.geometry
            .validate_transfer(first_block, block_count, buffer_len)
            .map_err(UsbMscError::Transfer)
    }
}

impl<T: UsbMscTransport> BlockDevice for UsbMscBlockDevice<T> {
    type Error = UsbMscError<T::Error>;

    fn geometry(&self) -> BlockGeometry {
        self.geometry
    }

    fn read_blocks(
        &mut self,
        first_block: u64,
        block_count: u32,
        output: &mut [u8],
    ) -> Result<(), Self::Error> {
        self.validate_transfer(first_block, block_count, output.len())?;
        self.transport
            .read_blocks(self.lun, first_block, block_count, output)
            .map_err(UsbMscError::Backend)
    }
}

impl<T: WritableUsbMscTransport> WritableBlockDevice for UsbMscBlockDevice<T> {
    fn write_blocks(
        &mut self,
        first_block: u64,
        block_count: u32,
        input: &[u8],
    ) -> Result<(), Self::Error> {
        self.validate_transfer(first_block, block_count, input.len())?;
        self.transport
            .write_blocks(self.lun, first_block, block_count, input)
            .map_err(UsbMscError::Backend)
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        if !self.connected {
            return Err(UsbMscError::Disconnected);
        }
        self.transport
            .synchronize_cache(self.lun)
            .map_err(UsbMscError::Backend)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestError {
        Failed,
    }

    impl fmt::Display for TestError {
        fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
            formatter.write_str("test transport failed")
        }
    }

    impl core::error::Error for TestError {}

    #[derive(Default)]
    struct TestTransport {
        read_calls: u32,
        write_calls: u32,
        flush_calls: u32,
        last_lun: u8,
        last_lba: u64,
        last_blocks: u32,
        fail: bool,
    }

    impl UsbMscTransport for TestTransport {
        type Error = TestError;

        fn read_blocks(
            &mut self,
            lun: u8,
            first_block: u64,
            block_count: u32,
            output: &mut [u8],
        ) -> Result<(), Self::Error> {
            if self.fail {
                return Err(TestError::Failed);
            }
            self.read_calls += 1;
            self.last_lun = lun;
            self.last_lba = first_block;
            self.last_blocks = block_count;
            output.fill(0xa5);
            Ok(())
        }
    }

    impl WritableUsbMscTransport for TestTransport {
        fn write_blocks(
            &mut self,
            lun: u8,
            first_block: u64,
            block_count: u32,
            _input: &[u8],
        ) -> Result<(), Self::Error> {
            if self.fail {
                return Err(TestError::Failed);
            }
            self.write_calls += 1;
            self.last_lun = lun;
            self.last_lba = first_block;
            self.last_blocks = block_count;
            Ok(())
        }

        fn synchronize_cache(&mut self, lun: u8) -> Result<(), Self::Error> {
            if self.fail {
                return Err(TestError::Failed);
            }
            self.flush_calls += 1;
            self.last_lun = lun;
            Ok(())
        }
    }

    fn device(max_blocks: u32) -> UsbMscBlockDevice<TestTransport> {
        UsbMscBlockDevice::new(
            TestTransport::default(),
            2,
            UsbMscCapacity::from_block_count(512, 1_000).unwrap(),
            NonZeroU32::new(max_blocks).unwrap(),
        )
        .unwrap()
    }

    #[test]
    fn capacity_converts_last_lba_without_overflow() {
        assert_eq!(
            UsbMscCapacity::from_last_lba(512, 999),
            Some(UsbMscCapacity {
                block_size: 512,
                block_count: 1_000,
            })
        );
        assert_eq!(UsbMscCapacity::from_last_lba(512, u64::MAX), None);
        assert_eq!(UsbMscCapacity::from_block_count(0, 1), None);
    }

    #[test]
    fn read_is_bounded_and_preserves_lun_and_u64_lba() {
        let lba = u32::MAX as u64 + 32;
        let mut device = UsbMscBlockDevice::new(
            TestTransport::default(),
            2,
            UsbMscCapacity::from_block_count(512, lba + 2).unwrap(),
            NonZeroU32::new(8).unwrap(),
        )
        .unwrap();
        let mut output = [0u8; 1_024];

        device.read_blocks(lba, 2, &mut output).unwrap();

        assert!(output.iter().all(|byte| *byte == 0xa5));
        assert_eq!(device.transport().read_calls, 1);
        assert_eq!(device.transport().last_lun, 2);
        assert_eq!(device.transport().last_lba, lba);
        assert_eq!(device.transport().last_blocks, 2);
    }

    #[test]
    fn invalid_buffer_and_transfer_window_fail_before_transport() {
        let mut device = device(2);

        assert_eq!(
            device.read_blocks(0, 3, &mut [0u8; 1_536]),
            Err(UsbMscError::TooManyBlocks {
                requested: 3,
                maximum: 2,
            })
        );
        assert_eq!(
            device.read_blocks(0, 1, &mut [0u8; 511]),
            Err(UsbMscError::Transfer(TransferError::InvalidBufferLength))
        );
        assert_eq!(device.transport().read_calls, 0);
    }

    #[test]
    fn disconnect_is_terminal_and_fail_closed() {
        let mut device = device(4);
        device.disconnect();

        assert!(!device.is_connected());
        assert_eq!(
            device.read_blocks(0, 1, &mut [0u8; 512]),
            Err(UsbMscError::Disconnected)
        );
        assert_eq!(device.flush(), Err(UsbMscError::Disconnected));
        assert_eq!(device.transport().read_calls, 0);
        assert_eq!(device.transport().flush_calls, 0);
    }

    #[test]
    fn write_and_flush_delegate_only_after_contract_validation() {
        let mut device = device(4);
        let input = [0x5au8; 1_024];

        device.write_blocks(7, 2, &input).unwrap();
        device.flush().unwrap();

        assert_eq!(device.transport().write_calls, 1);
        assert_eq!(device.transport().last_lba, 7);
        assert_eq!(device.transport().last_blocks, 2);
        assert_eq!(device.transport().flush_calls, 1);
    }

    #[test]
    fn backend_errors_are_not_misreported_as_disconnects() {
        let transport = TestTransport {
            fail: true,
            ..TestTransport::default()
        };
        let mut device = UsbMscBlockDevice::new(
            transport,
            0,
            UsbMscCapacity::from_block_count(4_096, 16).unwrap(),
            NonZeroU32::new(1).unwrap(),
        )
        .unwrap();

        assert_eq!(
            device.read_blocks(0, 1, &mut [0u8; 4_096]),
            Err(UsbMscError::Backend(TestError::Failed))
        );
    }
}
