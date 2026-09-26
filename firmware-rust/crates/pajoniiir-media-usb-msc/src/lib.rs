#![no_std]
#![forbid(unsafe_code)]

use core::fmt;
use core::num::NonZeroU32;

use pajoniiir_media_block::{BlockDevice, BlockGeometry, TransferError, WritableBlockDevice};
use pajoniiir_media_session::{MediaHandle, MediaLease, MediaSession, MediaSourceId};

#[derive(Clone, Copy, Debug, Eq, PartialEq, Ord, PartialOrd, Hash)]
pub struct UsbMscRequestId(NonZeroU32);

impl UsbMscRequestId {
    pub const fn new(value: u32) -> Option<Self> {
        match NonZeroU32::new(value) {
            Some(value) => Some(Self(value)),
            None => None,
        }
    }

    pub const fn get(self) -> u32 {
        self.0.get()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UsbMscRequestKind {
    Read { first_block: u64, block_count: u32 },
    Write { first_block: u64, block_count: u32 },
    Flush,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UsbMscRequestTicket {
    pub id: UsbMscRequestId,
    pub lease: MediaLease,
    pub lun: u8,
    pub kind: UsbMscRequestKind,
}

impl UsbMscRequestTicket {
    pub const fn first_block(self) -> Option<u64> {
        match self.kind {
            UsbMscRequestKind::Read { first_block, .. }
            | UsbMscRequestKind::Write { first_block, .. } => Some(first_block),
            UsbMscRequestKind::Flush => None,
        }
    }

    pub const fn block_count(self) -> Option<u32> {
        match self.kind {
            UsbMscRequestKind::Read { block_count, .. }
            | UsbMscRequestKind::Write { block_count, .. } => Some(block_count),
            UsbMscRequestKind::Flush => None,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UsbMscRequestSequencer {
    next: u32,
}

impl UsbMscRequestSequencer {
    pub const fn new() -> Self {
        Self { next: 1 }
    }

    pub fn issue(
        &mut self,
        lease: MediaLease,
        lun: u8,
        kind: UsbMscRequestKind,
    ) -> UsbMscRequestTicket {
        let id = UsbMscRequestId::new(self.next).expect("request sequence never emits zero");
        self.next = self.next.wrapping_add(1);
        if self.next == 0 {
            self.next = 1;
        }
        UsbMscRequestTicket {
            id,
            lease,
            lun,
            kind,
        }
    }
}

impl Default for UsbMscRequestSequencer {
    fn default() -> Self {
        Self::new()
    }
}

/// Gate applied after an async USB command completes.
///
/// Dispatch-time validation is necessary but insufficient because disconnect
/// and re-enumeration may advance MediaSession while the owner task is awaiting
/// the USB command. A completion is publishable only while its original lease
/// is still the session's current generation/source lease.
pub struct UsbMscCompletionGate;

impl UsbMscCompletionGate {
    pub const fn accepts(session: &MediaSession, ticket: UsbMscRequestTicket) -> bool {
        session.validate(ticket.lease)
    }
}

pub const fn usb_address_source(device_address: u8) -> Option<MediaSourceId> {
    MediaSourceId::new(device_address as u32)
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct UsbMscHandleSequencer {
    next: u64,
}

impl UsbMscHandleSequencer {
    pub const fn new() -> Self {
        Self { next: 1 }
    }

    pub fn issue(&mut self) -> MediaHandle {
        let handle = MediaHandle::new(self.next).expect("handle sequence never emits zero");
        self.next = self.next.wrapping_add(1);
        if self.next == 0 {
            self.next = 1;
        }
        handle
    }
}

impl Default for UsbMscHandleSequencer {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum UsbMscSessionError {
    NoActiveMedia,
    SecondaryDevice,
    HandleRejected,
}

pub struct UsbMscSessionBridge {
    session: MediaSession,
    requests: UsbMscRequestSequencer,
}

impl UsbMscSessionBridge {
    pub const fn new() -> Self {
        Self {
            session: MediaSession::new(),
            requests: UsbMscRequestSequencer::new(),
        }
    }

    pub fn on_enumerated(
        &mut self,
        source: pajoniiir_media_session::MediaSourceId,
        handle: pajoniiir_media_session::MediaHandle,
    ) -> Result<MediaLease, UsbMscSessionError> {
        let lease = match self.session.on_connect(source) {
            pajoniiir_media_session::ConnectResult::Accepted(lease)
            | pajoniiir_media_session::ConnectResult::Duplicate(lease) => lease,
            pajoniiir_media_session::ConnectResult::IgnoredSecondary(_) => {
                return Err(UsbMscSessionError::SecondaryDevice);
            }
        };

        if !self.session.bind_handle(lease, handle) {
            return Err(UsbMscSessionError::HandleRejected);
        }
        Ok(lease)
    }

    pub fn on_disconnect(
        &mut self,
        handle: pajoniiir_media_session::MediaHandle,
    ) -> pajoniiir_media_session::DisconnectResult {
        self.session.on_disconnect(Some(handle))
    }

    pub fn issue(
        &mut self,
        lun: u8,
        kind: UsbMscRequestKind,
    ) -> Result<UsbMscRequestTicket, UsbMscSessionError> {
        let Some(lease) = self.session.lease() else {
            return Err(UsbMscSessionError::NoActiveMedia);
        };
        if self.session.handle().is_none() {
            return Err(UsbMscSessionError::NoActiveMedia);
        }
        Ok(self.requests.issue(lease, lun, kind))
    }

    pub const fn session(&self) -> &MediaSession {
        &self.session
    }

    pub fn session_mut(&mut self) -> &mut MediaSession {
        &mut self.session
    }

    pub const fn lease(&self) -> Option<MediaLease> {
        self.session.lease()
    }

    pub const fn accepts_completion(&self, ticket: UsbMscRequestTicket) -> bool {
        UsbMscCompletionGate::accepts(&self.session, ticket)
    }
}

impl Default for UsbMscSessionBridge {
    fn default() -> Self {
        Self::new()
    }
}

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

    fn lease(session: &mut MediaSession, source: u32) -> MediaLease {
        let source = pajoniiir_media_session::MediaSourceId::new(source).unwrap();
        match session.on_connect(source) {
            pajoniiir_media_session::ConnectResult::Accepted(lease) => lease,
            other => panic!("unexpected connect result: {other:?}"),
        }
    }

    #[test]
    fn request_ids_skip_zero_across_wrap() {
        let mut session = MediaSession::new();
        let lease = lease(&mut session, 1);
        let mut ids = UsbMscRequestSequencer { next: u32::MAX };

        let last = ids.issue(lease, 0, UsbMscRequestKind::Flush);
        let wrapped = ids.issue(lease, 0, UsbMscRequestKind::Flush);

        assert_eq!(last.id.get(), u32::MAX);
        assert_eq!(wrapped.id.get(), 1);
    }

    #[test]
    fn reconnect_same_source_rejects_old_completion_ticket() {
        let mut session = MediaSession::new();
        let old_lease = lease(&mut session, 7);
        let mut ids = UsbMscRequestSequencer::new();
        let old_ticket = ids.issue(
            old_lease,
            0,
            UsbMscRequestKind::Read {
                first_block: 42,
                block_count: 2,
            },
        );
        assert!(UsbMscCompletionGate::accepts(&session, old_ticket));

        assert_eq!(
            session.on_disconnect(None),
            pajoniiir_media_session::DisconnectResult::Accepted
        );
        let fresh_lease = lease(&mut session, 7);
        let fresh_ticket = ids.issue(
            fresh_lease,
            0,
            UsbMscRequestKind::Read {
                first_block: 42,
                block_count: 2,
            },
        );

        assert_ne!(old_lease.generation, fresh_lease.generation);
        assert!(!UsbMscCompletionGate::accepts(&session, old_ticket));
        assert!(UsbMscCompletionGate::accepts(&session, fresh_ticket));
        assert_ne!(old_ticket.id, fresh_ticket.id);
    }

    #[test]
    fn ticket_preserves_u64_lba_block_count_lun_and_operation() {
        let mut session = MediaSession::new();
        let lease = lease(&mut session, 3);
        let mut ids = UsbMscRequestSequencer::new();
        let lba = u32::MAX as u64 + 77;
        let ticket = ids.issue(
            lease,
            4,
            UsbMscRequestKind::Write {
                first_block: lba,
                block_count: 8,
            },
        );

        assert_eq!(ticket.lun, 4);
        assert_eq!(ticket.first_block(), Some(lba));
        assert_eq!(ticket.block_count(), Some(8));
        assert!(matches!(ticket.kind, UsbMscRequestKind::Write { .. }));
    }

    #[test]
    fn usb_device_address_is_session_local_source_and_zero_is_rejected() {
        assert_eq!(usb_address_source(0), None);
        assert_eq!(usb_address_source(1).unwrap().get(), 1);
        assert_eq!(usb_address_source(127).unwrap().get(), 127);
    }

    #[test]
    fn media_handle_sequence_skips_zero_and_does_not_reuse_usb_address() {
        let mut handles = UsbMscHandleSequencer { next: u64::MAX };
        let last = handles.issue();
        let wrapped = handles.issue();

        assert_eq!(last.get(), u64::MAX);
        assert_eq!(wrapped.get(), 1);

        let source = usb_address_source(5).unwrap();
        assert_ne!(last.get(), source.get() as u64);
    }

    fn media_source(value: u32) -> pajoniiir_media_session::MediaSourceId {
        pajoniiir_media_session::MediaSourceId::new(value).unwrap()
    }

    fn media_handle(value: u64) -> pajoniiir_media_session::MediaHandle {
        pajoniiir_media_session::MediaHandle::new(value).unwrap()
    }

    #[test]
    fn enumeration_binds_owner_and_admits_requests_only_while_connected() {
        let mut bridge = UsbMscSessionBridge::new();
        assert_eq!(
            bridge.issue(
                0,
                UsbMscRequestKind::Read {
                    first_block: 0,
                    block_count: 1,
                },
            ),
            Err(UsbMscSessionError::NoActiveMedia)
        );

        let lease = bridge
            .on_enumerated(media_source(4), media_handle(11))
            .unwrap();
        let ticket = bridge
            .issue(
                0,
                UsbMscRequestKind::Read {
                    first_block: 0,
                    block_count: 1,
                },
            )
            .unwrap();

        assert_eq!(ticket.lease, lease);
        assert!(bridge.accepts_completion(ticket));
        assert_eq!(
            bridge.on_disconnect(media_handle(11)),
            pajoniiir_media_session::DisconnectResult::Accepted
        );
        assert!(!bridge.accepts_completion(ticket));
        assert_eq!(
            bridge.issue(0, UsbMscRequestKind::Flush),
            Err(UsbMscSessionError::NoActiveMedia)
        );
    }

    #[test]
    fn same_source_reenumeration_never_revalidates_old_ticket() {
        let mut bridge = UsbMscSessionBridge::new();
        let old_lease = bridge
            .on_enumerated(media_source(4), media_handle(11))
            .unwrap();
        let old_ticket = bridge
            .issue(
                0,
                UsbMscRequestKind::Read {
                    first_block: 7,
                    block_count: 2,
                },
            )
            .unwrap();

        assert_eq!(
            bridge.on_disconnect(media_handle(11)),
            pajoniiir_media_session::DisconnectResult::Accepted
        );
        let fresh_lease = bridge
            .on_enumerated(media_source(4), media_handle(12))
            .unwrap();
        let fresh_ticket = bridge
            .issue(
                0,
                UsbMscRequestKind::Read {
                    first_block: 7,
                    block_count: 2,
                },
            )
            .unwrap();

        assert_ne!(old_lease.generation, fresh_lease.generation);
        assert!(!bridge.accepts_completion(old_ticket));
        assert!(bridge.accepts_completion(fresh_ticket));
    }

    #[test]
    fn foreign_disconnect_and_secondary_enumeration_do_not_steal_owner() {
        let mut bridge = UsbMscSessionBridge::new();
        let primary = bridge
            .on_enumerated(media_source(4), media_handle(11))
            .unwrap();
        assert_eq!(
            bridge.on_enumerated(media_source(9), media_handle(99)),
            Err(UsbMscSessionError::SecondaryDevice)
        );
        assert_eq!(
            bridge.on_disconnect(media_handle(99)),
            pajoniiir_media_session::DisconnectResult::IgnoredForeign
        );

        let ticket = bridge.issue(0, UsbMscRequestKind::Flush).unwrap();
        assert_eq!(ticket.lease, primary);
        assert!(bridge.accepts_completion(ticket));
    }

    #[test]
    fn delayed_old_handle_disconnect_cannot_drop_fresh_generation() {
        let mut bridge = UsbMscSessionBridge::new();
        let old_handle = media_handle(11);
        let fresh_handle = media_handle(12);

        bridge.on_enumerated(media_source(4), old_handle).unwrap();
        assert_eq!(
            bridge.on_disconnect(old_handle),
            pajoniiir_media_session::DisconnectResult::Accepted
        );
        let fresh_lease = bridge.on_enumerated(media_source(4), fresh_handle).unwrap();
        let fresh_ticket = bridge.issue(0, UsbMscRequestKind::Flush).unwrap();

        assert_eq!(
            bridge.on_disconnect(old_handle),
            pajoniiir_media_session::DisconnectResult::IgnoredForeign
        );
        assert_eq!(bridge.lease(), Some(fresh_lease));
        assert!(bridge.accepts_completion(fresh_ticket));
    }

    #[test]
    fn duplicate_enumeration_cannot_replace_bound_handle() {
        let mut bridge = UsbMscSessionBridge::new();
        let lease = bridge
            .on_enumerated(media_source(4), media_handle(11))
            .unwrap();

        assert_eq!(
            bridge.on_enumerated(media_source(4), media_handle(12)),
            Err(UsbMscSessionError::HandleRejected)
        );
        assert_eq!(bridge.lease(), Some(lease));
        assert_eq!(bridge.session().handle(), Some(media_handle(11)));
    }

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
