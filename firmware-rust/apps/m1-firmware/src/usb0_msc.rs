use embassy_sync::{
    blocking_mutex::raw::CriticalSectionRawMutex,
    channel::Channel,
};
use embassy_usb_driver::host::UsbHostAllocator;
use embassy_usb_host::class::msc::{BlockCapacity, MscError, MscLun};
use pajoniiir_media_session::{MediaLease, MediaSession};
use pajoniiir_media_usb_msc::{
    UsbMscCapacity, UsbMscCompletionGate, UsbMscRequestKind, UsbMscRequestTicket,
};

pub(crate) const USB0_MSC_QUEUE_DEPTH: usize = 4;

pub(crate) static USB0_MSC_REQUESTS: Channel<
    CriticalSectionRawMutex,
    Usb0MscRequest,
    USB0_MSC_QUEUE_DEPTH,
> = Channel::new();

pub(crate) static USB0_MSC_COMPLETIONS: Channel<
    CriticalSectionRawMutex,
    Usb0MscCompletion,
    USB0_MSC_QUEUE_DEPTH,
> = Channel::new();

#[derive(Debug)]
pub(crate) enum Usb0MscError {
    Host(MscError),
    InvalidCapacity,
}

impl From<MscError> for Usb0MscError {
    fn from(error: MscError) -> Self {
        Self::Host(error)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) enum Usb0MscCompletionStatus {
    Success,
    StaleLease,
    WrongLun,
    InvalidTransfer,
    HostError,
}

#[derive(Debug)]
pub(crate) enum Usb0MscRequest {
    Read {
        ticket: UsbMscRequestTicket,
        buffer: &'static mut [u8],
    },
    Write {
        ticket: UsbMscRequestTicket,
        buffer: &'static mut [u8],
    },
    Flush {
        ticket: UsbMscRequestTicket,
    },
}

impl Usb0MscRequest {
    pub(crate) const fn ticket(&self) -> UsbMscRequestTicket {
        match self {
            Self::Read { ticket, .. }
            | Self::Write { ticket, .. }
            | Self::Flush { ticket } => *ticket,
        }
    }
}

#[derive(Debug)]
pub(crate) enum Usb0MscCompletion {
    Read {
        ticket: UsbMscRequestTicket,
        buffer: &'static mut [u8],
        status: Usb0MscCompletionStatus,
    },
    Write {
        ticket: UsbMscRequestTicket,
        buffer: &'static mut [u8],
        status: Usb0MscCompletionStatus,
    },
    Flush {
        ticket: UsbMscRequestTicket,
        status: Usb0MscCompletionStatus,
    },
}

impl Usb0MscCompletion {
    pub(crate) const fn ticket(&self) -> UsbMscRequestTicket {
        match self {
            Self::Read { ticket, .. }
            | Self::Write { ticket, .. }
            | Self::Flush { ticket, .. } => *ticket,
        }
    }

    pub(crate) const fn status(&self) -> Usb0MscCompletionStatus {
        match self {
            Self::Read { status, .. }
            | Self::Write { status, .. }
            | Self::Flush { status, .. } => *status,
        }
    }

    pub(crate) fn is_current(&self, session: &MediaSession) -> bool {
        self.status() == Usb0MscCompletionStatus::Success
            && UsbMscCompletionGate::accepts(session, self.ticket())
    }
}

pub(crate) fn capacity_from_embassy(capacity: BlockCapacity) -> Option<UsbMscCapacity> {
    UsbMscCapacity::from_block_count(capacity.block_size, capacity.block_count)
}

pub(crate) async fn probe_capacity<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
) -> Result<UsbMscCapacity, Usb0MscError>
where
    A: UsbHostAllocator<'d>,
{
    let capacity = lun.capacity().await?;
    capacity_from_embassy(capacity).ok_or(Usb0MscError::InvalidCapacity)
}

pub(crate) async fn test_unit_ready<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
) -> Result<bool, MscError>
where
    A: UsbHostAllocator<'d>,
{
    lun.test_unit_ready().await
}

pub(crate) async fn read_blocks<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
    lba: u64,
    output: &mut [u8],
) -> Result<(), MscError>
where
    A: UsbHostAllocator<'d>,
{
    lun.read_blocks(lba, output).await
}

pub(crate) async fn write_blocks<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
    lba: u64,
    input: &[u8],
) -> Result<(), MscError>
where
    A: UsbHostAllocator<'d>,
{
    lun.write_blocks(lba, input).await
}

pub(crate) async fn flush<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
) -> Result<(), MscError>
where
    A: UsbHostAllocator<'d>,
{
    lun.flush().await
}

/// Execute one bounded queued request on the task that owns the Embassy MSC LUN.
///
/// The dispatch lease is checked before I/O. The returned completion still
/// carries the original request ticket and must be revalidated against the
/// current MediaSession after the await.
pub(crate) async fn owner_step<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
    lease_at_dispatch: MediaLease,
) where
    A: UsbHostAllocator<'d>,
{
    let request = USB0_MSC_REQUESTS.receive().await;
    let completion = execute_request(lun, lease_at_dispatch, request).await;
    USB0_MSC_COMPLETIONS.send(completion).await;
}

pub(crate) async fn execute_request<'dev, 'd, A>(
    lun: &mut MscLun<'dev, 'd, A>,
    lease_at_dispatch: MediaLease,
    request: Usb0MscRequest,
) -> Usb0MscCompletion
where
    A: UsbHostAllocator<'d>,
{
    let ticket = request.ticket();
    if ticket.lease != lease_at_dispatch {
        return complete_with_status(request, Usb0MscCompletionStatus::StaleLease);
    }
    if ticket.lun != lun.lun() {
        return complete_with_status(request, Usb0MscCompletionStatus::WrongLun);
    }

    match request {
        Usb0MscRequest::Read { ticket, buffer } => {
            if !buffer_matches_ticket(lun, ticket, buffer.len(), true) {
                return Usb0MscCompletion::Read {
                    ticket,
                    buffer,
                    status: Usb0MscCompletionStatus::InvalidTransfer,
                };
            }
            let status = match lun.read_blocks(ticket.first_block().unwrap(), buffer).await {
                Ok(()) => Usb0MscCompletionStatus::Success,
                Err(_) => Usb0MscCompletionStatus::HostError,
            };
            Usb0MscCompletion::Read {
                ticket,
                buffer,
                status,
            }
        }
        Usb0MscRequest::Write { ticket, buffer } => {
            if !buffer_matches_ticket(lun, ticket, buffer.len(), false) {
                return Usb0MscCompletion::Write {
                    ticket,
                    buffer,
                    status: Usb0MscCompletionStatus::InvalidTransfer,
                };
            }
            let status = match lun.write_blocks(ticket.first_block().unwrap(), buffer).await {
                Ok(()) => Usb0MscCompletionStatus::Success,
                Err(_) => Usb0MscCompletionStatus::HostError,
            };
            Usb0MscCompletion::Write {
                ticket,
                buffer,
                status,
            }
        }
        Usb0MscRequest::Flush { ticket } => {
            if ticket.kind != UsbMscRequestKind::Flush {
                return Usb0MscCompletion::Flush {
                    ticket,
                    status: Usb0MscCompletionStatus::InvalidTransfer,
                };
            }
            let status = match lun.flush().await {
                Ok(()) => Usb0MscCompletionStatus::Success,
                Err(_) => Usb0MscCompletionStatus::HostError,
            };
            Usb0MscCompletion::Flush { ticket, status }
        }
    }
}

fn buffer_matches_ticket<'dev, 'd, A>(
    lun: &MscLun<'dev, 'd, A>,
    ticket: UsbMscRequestTicket,
    buffer_len: usize,
    read: bool,
) -> bool
where
    A: UsbHostAllocator<'d>,
{
    let expected_kind = match ticket.kind {
        UsbMscRequestKind::Read { block_count, .. } if read => Some(block_count),
        UsbMscRequestKind::Write { block_count, .. } if !read => Some(block_count),
        _ => None,
    };
    let Some(block_count) = expected_kind else {
        return false;
    };
    if block_count == 0 {
        return false;
    }
    let Some(capacity) = lun.cached_capacity() else {
        return false;
    };
    (capacity.block_size as usize)
        .checked_mul(block_count as usize)
        == Some(buffer_len)
}

fn complete_with_status(
    request: Usb0MscRequest,
    status: Usb0MscCompletionStatus,
) -> Usb0MscCompletion {
    match request {
        Usb0MscRequest::Read { ticket, buffer } => Usb0MscCompletion::Read {
            ticket,
            buffer,
            status,
        },
        Usb0MscRequest::Write { ticket, buffer } => Usb0MscCompletion::Write {
            ticket,
            buffer,
            status,
        },
        Usb0MscRequest::Flush { ticket } => Usb0MscCompletion::Flush { ticket, status },
    }
}
