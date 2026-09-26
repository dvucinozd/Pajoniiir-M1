use embassy_usb_driver::host::UsbHostAllocator;
use embassy_usb_host::class::msc::{BlockCapacity, MscError, MscLun};
use pajoniiir_media_usb_msc::UsbMscCapacity;

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
