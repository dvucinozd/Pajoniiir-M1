#![no_std]
#![forbid(unsafe_code)]

#[cfg(test)]
extern crate std;

use exfat_embedded::BlockDevice as ExFatBlockDevice;
use pajoniiir_media_block::{BlockGeometry, WritableBlockDevice};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ExFatBlockError<E> {
    InvalidGeometry(BlockGeometry),
    InvalidTransfer,
    Backend(E),
}

pub struct ExFatBlockAdapter<D> {
    inner: D,
}

impl<D> ExFatBlockAdapter<D> {
    pub const fn new(inner: D) -> Self {
        Self { inner }
    }

    pub const fn inner(&self) -> &D {
        &self.inner
    }

    pub fn inner_mut(&mut self) -> &mut D {
        &mut self.inner
    }

    pub fn into_inner(self) -> D {
        self.inner
    }
}

impl<D> ExFatBlockAdapter<D>
where
    D: WritableBlockDevice,
{
    pub fn validate_geometry(&self) -> Result<BlockGeometry, ExFatBlockError<D::Error>> {
        let geometry = self.inner.geometry();
        if geometry.block_count == 0 || !matches!(geometry.block_size, 512 | 1_024 | 2_048 | 4_096)
        {
            return Err(ExFatBlockError::InvalidGeometry(geometry));
        }
        Ok(geometry)
    }
}

impl<D> ExFatBlockDevice for ExFatBlockAdapter<D>
where
    D: WritableBlockDevice,
{
    type Error = ExFatBlockError<D::Error>;

    fn sector_size(&self) -> usize {
        self.inner.geometry().block_size as usize
    }

    fn sector_count(&self) -> u64 {
        self.inner.geometry().block_count
    }

    fn read_sector(&mut self, lba: u64, output: &mut [u8]) -> Result<(), Self::Error> {
        let geometry = self.validate_geometry()?;
        geometry
            .validate_transfer(lba, 1, output.len())
            .map_err(|_| ExFatBlockError::InvalidTransfer)?;
        self.inner
            .read_blocks(lba, 1, output)
            .map_err(ExFatBlockError::Backend)
    }

    fn write_sector(&mut self, lba: u64, input: &[u8]) -> Result<(), Self::Error> {
        let geometry = self.validate_geometry()?;
        geometry
            .validate_transfer(lba, 1, input.len())
            .map_err(|_| ExFatBlockError::InvalidTransfer)?;
        self.inner
            .write_blocks(lba, 1, input)
            .map_err(ExFatBlockError::Backend)
    }

    fn flush(&mut self) -> Result<(), Self::Error> {
        self.validate_geometry()?;
        self.inner.flush().map_err(ExFatBlockError::Backend)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pajoniiir_media_block::{BlockDevice, TransferError};

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestError {
        Transfer(TransferError),
    }

    struct MemoryDevice<const N: usize> {
        geometry: BlockGeometry,
        bytes: [u8; N],
        reads: u32,
        writes: u32,
        flushes: u32,
    }

    impl<const N: usize> MemoryDevice<N> {
        fn new(block_size: u32, block_count: u64) -> Self {
            Self {
                geometry: BlockGeometry {
                    block_size,
                    block_count,
                },
                bytes: [0; N],
                reads: 0,
                writes: 0,
                flushes: 0,
            }
        }
    }

    impl<const N: usize> BlockDevice for MemoryDevice<N> {
        type Error = TestError;

        fn geometry(&self) -> BlockGeometry {
            self.geometry
        }

        fn read_blocks(
            &mut self,
            first_block: u64,
            block_count: u32,
            output: &mut [u8],
        ) -> Result<(), Self::Error> {
            self.geometry
                .validate_transfer(first_block, block_count, output.len())
                .map_err(TestError::Transfer)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let end = start
                .checked_add(output.len())
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let source = self
                .bytes
                .get(start..end)
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            output.copy_from_slice(source);
            self.reads += 1;
            Ok(())
        }
    }

    impl<const N: usize> WritableBlockDevice for MemoryDevice<N> {
        fn write_blocks(
            &mut self,
            first_block: u64,
            block_count: u32,
            input: &[u8],
        ) -> Result<(), Self::Error> {
            self.geometry
                .validate_transfer(first_block, block_count, input.len())
                .map_err(TestError::Transfer)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let end = start
                .checked_add(input.len())
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let destination = self
                .bytes
                .get_mut(start..end)
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            destination.copy_from_slice(input);
            self.writes += 1;
            Ok(())
        }

        fn flush(&mut self) -> Result<(), Self::Error> {
            self.flushes += 1;
            Ok(())
        }
    }

    #[test]
    fn bridge_accepts_all_exfat_sector_sizes() {
        for size in [512, 1_024, 2_048, 4_096] {
            let adapter = ExFatBlockAdapter::new(MemoryDevice::<4096>::new(size, 1));
            assert_eq!(
                adapter.validate_geometry(),
                Ok(BlockGeometry {
                    block_size: size,
                    block_count: 1,
                })
            );
            assert_eq!(ExFatBlockDevice::sector_size(&adapter), size as usize);
            assert_eq!(ExFatBlockDevice::sector_count(&adapter), 1);
        }
    }

    #[test]
    fn bridge_rejects_invalid_sector_size_and_empty_device() {
        let invalid = ExFatBlockAdapter::new(MemoryDevice::<4096>::new(768, 1));
        assert_eq!(
            invalid.validate_geometry(),
            Err(ExFatBlockError::InvalidGeometry(BlockGeometry {
                block_size: 768,
                block_count: 1,
            }))
        );

        let empty = ExFatBlockAdapter::new(MemoryDevice::<4096>::new(512, 0));
        assert_eq!(
            empty.validate_geometry(),
            Err(ExFatBlockError::InvalidGeometry(BlockGeometry {
                block_size: 512,
                block_count: 0,
            }))
        );
    }

    #[test]
    fn single_sector_read_write_and_flush_reach_transport() {
        let mut adapter = ExFatBlockAdapter::new(MemoryDevice::<2048>::new(512, 4));
        let write = [0x5au8; 512];
        ExFatBlockDevice::write_sector(&mut adapter, 2, &write).unwrap();

        let mut read = [0u8; 512];
        ExFatBlockDevice::read_sector(&mut adapter, 2, &mut read).unwrap();
        ExFatBlockDevice::flush(&mut adapter).unwrap();

        assert_eq!(read, write);
        assert_eq!(adapter.inner().reads, 1);
        assert_eq!(adapter.inner().writes, 1);
        assert_eq!(adapter.inner().flushes, 1);
    }

    #[test]
    fn bridge_rejects_wrong_buffer_size_and_out_of_range_lba() {
        let mut adapter = ExFatBlockAdapter::new(MemoryDevice::<2048>::new(512, 4));

        assert_eq!(
            ExFatBlockDevice::read_sector(&mut adapter, 0, &mut [0u8; 511]),
            Err(ExFatBlockError::InvalidTransfer)
        );
        assert_eq!(
            ExFatBlockDevice::write_sector(&mut adapter, 4, &[0u8; 512]),
            Err(ExFatBlockError::InvalidTransfer)
        );
        assert_eq!(adapter.inner().reads, 0);
        assert_eq!(adapter.inner().writes, 0);
    }

    struct HeapDevice {
        geometry: BlockGeometry,
        bytes: std::vec::Vec<u8>,
    }

    impl HeapDevice {
        fn new(block_size: u32, block_count: u64) -> Self {
            let byte_len = usize::try_from(block_size as u64 * block_count).unwrap();
            Self {
                geometry: BlockGeometry {
                    block_size,
                    block_count,
                },
                bytes: std::vec![0; byte_len],
            }
        }
    }

    impl BlockDevice for HeapDevice {
        type Error = TestError;

        fn geometry(&self) -> BlockGeometry {
            self.geometry
        }

        fn read_blocks(
            &mut self,
            first_block: u64,
            block_count: u32,
            output: &mut [u8],
        ) -> Result<(), Self::Error> {
            self.geometry
                .validate_transfer(first_block, block_count, output.len())
                .map_err(TestError::Transfer)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let end = start
                .checked_add(output.len())
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            output.copy_from_slice(
                self.bytes
                    .get(start..end)
                    .ok_or(TestError::Transfer(TransferError::OutOfRange))?,
            );
            Ok(())
        }
    }

    impl WritableBlockDevice for HeapDevice {
        fn write_blocks(
            &mut self,
            first_block: u64,
            block_count: u32,
            input: &[u8],
        ) -> Result<(), Self::Error> {
            self.geometry
                .validate_transfer(first_block, block_count, input.len())
                .map_err(TestError::Transfer)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            let end = start
                .checked_add(input.len())
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?;
            self.bytes
                .get_mut(start..end)
                .ok_or(TestError::Transfer(TransferError::OutOfRange))?
                .copy_from_slice(input);
            Ok(())
        }

        fn flush(&mut self) -> Result<(), Self::Error> {
            Ok(())
        }
    }

    #[test]
    fn format_mount_append_reopen_and_read_round_trip() {
        use exfat_embedded::{FileSystem, Scratch, format_exfat};

        const BLOCK_SIZE: u32 = 512;
        const BLOCK_COUNT: u64 = 16_384;

        let device = HeapDevice::new(BLOCK_SIZE, BLOCK_COUNT);
        let mut adapter = ExFatBlockAdapter::new(device);
        let mut scratch_bytes = [0u8; BLOCK_SIZE as usize];
        let mut scratch = Scratch::new(&mut scratch_bytes);

        format_exfat(&mut adapter, &mut scratch).unwrap();

        let mut filesystem = FileSystem::mount(adapter, &mut scratch).unwrap();
        let mut created = filesystem.create("TRACK.BIN", &mut scratch).unwrap();
        let payload = b"Pajoniiir-M1 exFAT round-trip";
        assert_eq!(
            filesystem.append(&mut created, payload, &mut scratch),
            Ok(payload.len())
        );
        filesystem.flush(&mut scratch).unwrap();

        let mut reopened = filesystem.open("TRACK.BIN", &mut scratch).unwrap();
        assert_eq!(reopened.len(), payload.len() as u64);
        assert_eq!(reopened.position(), 0);

        let mut output = [0u8; 30];
        let read = filesystem.read(&mut reopened, &mut output, &mut scratch).unwrap();
        assert_eq!(read, payload.len());
        assert_eq!(&output[..read], payload);
    }

    #[test]
    fn four_kib_sector_transfer_remains_single_backend_block() {
        let mut adapter = ExFatBlockAdapter::new(MemoryDevice::<8192>::new(4_096, 2));
        let write = [0xa5u8; 4_096];

        ExFatBlockDevice::write_sector(&mut adapter, 1, &write).unwrap();
        let mut read = [0u8; 4_096];
        ExFatBlockDevice::read_sector(&mut adapter, 1, &mut read).unwrap();

        assert_eq!(read, write);
        assert_eq!(adapter.inner().writes, 1);
        assert_eq!(adapter.inner().reads, 1);
    }
}
