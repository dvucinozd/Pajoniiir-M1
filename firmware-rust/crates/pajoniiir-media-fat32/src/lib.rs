#![no_std]
#![forbid(unsafe_code)]

use core::cell::RefCell;
use core::fmt;

use embedded_sdmmc::{Block, BlockCount, BlockDevice as SdmmcBlockDevice, BlockIdx};
use pajoniiir_media_block::{BlockGeometry, WritableBlockDevice};

pub const FAT_BLOCK_SIZE: u32 = 512;

#[derive(Debug, Eq, PartialEq)]
pub enum Fat32BlockError<E> {
    UnsupportedBlockSize(u32),
    TooManyBlocks(u64),
    BorrowConflict,
    AddressOverflow,
    Backend(E),
}

impl<E: fmt::Display> fmt::Display for Fat32BlockError<E> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedBlockSize(size) => {
                write!(formatter, "unsupported FAT block size: {size}")
            }
            Self::TooManyBlocks(count) => {
                write!(formatter, "FAT block count exceeds u32 range: {count}")
            }
            Self::BorrowConflict => formatter.write_str("FAT block adapter borrow conflict"),
            Self::AddressOverflow => formatter.write_str("FAT block address overflow"),
            Self::Backend(error) => write!(formatter, "FAT block backend error: {error}"),
        }
    }
}

impl<E> core::error::Error for Fat32BlockError<E> where E: core::error::Error + 'static {}

pub struct Fat32BlockAdapter<D> {
    inner: RefCell<D>,
}

impl<D> Fat32BlockAdapter<D> {
    pub const fn new(inner: D) -> Self {
        Self {
            inner: RefCell::new(inner),
        }
    }

    pub fn into_inner(self) -> D {
        self.inner.into_inner()
    }

    pub fn with_inner<R>(&self, f: impl FnOnce(&D) -> R) -> Result<R, Fat32BlockError<()>> {
        let inner = self
            .inner
            .try_borrow()
            .map_err(|_| Fat32BlockError::BorrowConflict)?;
        Ok(f(&inner))
    }
}

impl<D> Fat32BlockAdapter<D>
where
    D: WritableBlockDevice,
{
    pub fn validate_geometry(&self) -> Result<BlockGeometry, Fat32BlockError<D::Error>> {
        let inner = self
            .inner
            .try_borrow()
            .map_err(|_| Fat32BlockError::BorrowConflict)?;
        let geometry = inner.geometry();
        if geometry.block_size != FAT_BLOCK_SIZE {
            return Err(Fat32BlockError::UnsupportedBlockSize(geometry.block_size));
        }
        if geometry.block_count > u32::MAX as u64 {
            return Err(Fat32BlockError::TooManyBlocks(geometry.block_count));
        }
        Ok(geometry)
    }

    pub fn flush_inner(&self) -> Result<(), Fat32BlockError<D::Error>> {
        let mut inner = self
            .inner
            .try_borrow_mut()
            .map_err(|_| Fat32BlockError::BorrowConflict)?;
        inner.flush().map_err(Fat32BlockError::Backend)
    }
}

impl<D> SdmmcBlockDevice for Fat32BlockAdapter<D>
where
    D: WritableBlockDevice,
    D::Error: core::error::Error + 'static,
{
    type Error = Fat32BlockError<D::Error>;

    fn read(&self, blocks: &mut [Block], start_block_idx: BlockIdx) -> Result<(), Self::Error> {
        let geometry = self.validate_geometry()?;
        let start = start_block_idx.0 as u64;
        let count = u32::try_from(blocks.len()).map_err(|_| Fat32BlockError::AddressOverflow)?;

        geometry
            .validate_transfer(
                start,
                count,
                blocks
                    .len()
                    .checked_mul(FAT_BLOCK_SIZE as usize)
                    .ok_or(Fat32BlockError::AddressOverflow)?,
            )
            .map_err(|_| Fat32BlockError::AddressOverflow)?;

        let mut inner = self
            .inner
            .try_borrow_mut()
            .map_err(|_| Fat32BlockError::BorrowConflict)?;

        for (offset, block) in blocks.iter_mut().enumerate() {
            let block_index = start
                .checked_add(offset as u64)
                .ok_or(Fat32BlockError::AddressOverflow)?;
            inner
                .read_blocks(block_index, 1, &mut block.contents)
                .map_err(Fat32BlockError::Backend)?;
        }
        Ok(())
    }

    fn write(&self, blocks: &[Block], start_block_idx: BlockIdx) -> Result<(), Self::Error> {
        let geometry = self.validate_geometry()?;
        let start = start_block_idx.0 as u64;
        let count = u32::try_from(blocks.len()).map_err(|_| Fat32BlockError::AddressOverflow)?;

        geometry
            .validate_transfer(
                start,
                count,
                blocks
                    .len()
                    .checked_mul(FAT_BLOCK_SIZE as usize)
                    .ok_or(Fat32BlockError::AddressOverflow)?,
            )
            .map_err(|_| Fat32BlockError::AddressOverflow)?;

        let mut inner = self
            .inner
            .try_borrow_mut()
            .map_err(|_| Fat32BlockError::BorrowConflict)?;

        for (offset, block) in blocks.iter().enumerate() {
            let block_index = start
                .checked_add(offset as u64)
                .ok_or(Fat32BlockError::AddressOverflow)?;
            inner
                .write_blocks(block_index, 1, &block.contents)
                .map_err(Fat32BlockError::Backend)?;
        }
        Ok(())
    }

    fn num_blocks(&self) -> Result<BlockCount, Self::Error> {
        let geometry = self.validate_geometry()?;
        Ok(BlockCount(geometry.block_count as u32))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pajoniiir_media_block::BlockDevice;

    #[derive(Clone, Copy, Debug, Eq, PartialEq)]
    enum TestError {
        Invalid,
    }

    impl core::fmt::Display for TestError {
        fn fmt(&self, formatter: &mut core::fmt::Formatter<'_>) -> core::fmt::Result {
            formatter.write_str("invalid test block transfer")
        }
    }

    impl core::error::Error for TestError {}

    struct MemoryDevice {
        geometry: BlockGeometry,
        bytes: [u8; 2_048],
        flushes: u32,
    }

    impl MemoryDevice {
        fn new(block_size: u32, block_count: u64) -> Self {
            Self {
                geometry: BlockGeometry {
                    block_size,
                    block_count,
                },
                bytes: [0; 2_048],
                flushes: 0,
            }
        }
    }

    impl BlockDevice for MemoryDevice {
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
                .map_err(|_| TestError::Invalid)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Invalid)?;
            let end = start.checked_add(output.len()).ok_or(TestError::Invalid)?;
            let source = self.bytes.get(start..end).ok_or(TestError::Invalid)?;
            output.copy_from_slice(source);
            Ok(())
        }
    }

    impl WritableBlockDevice for MemoryDevice {
        fn write_blocks(
            &mut self,
            first_block: u64,
            block_count: u32,
            input: &[u8],
        ) -> Result<(), Self::Error> {
            self.geometry
                .validate_transfer(first_block, block_count, input.len())
                .map_err(|_| TestError::Invalid)?;
            let start = usize::try_from(first_block)
                .ok()
                .and_then(|value| value.checked_mul(self.geometry.block_size as usize))
                .ok_or(TestError::Invalid)?;
            let end = start.checked_add(input.len()).ok_or(TestError::Invalid)?;
            let destination = self.bytes.get_mut(start..end).ok_or(TestError::Invalid)?;
            destination.copy_from_slice(input);
            Ok(())
        }

        fn flush(&mut self) -> Result<(), Self::Error> {
            self.flushes += 1;
            Ok(())
        }
    }

    #[test]
    fn bridge_exposes_exact_512_byte_geometry() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(512, 4));
        assert_eq!(adapter.num_blocks(), Ok(BlockCount(4)));
    }

    #[test]
    fn bridge_rejects_non_512_sector_geometry() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(4_096, 1));
        assert_eq!(
            adapter.num_blocks(),
            Err(Fat32BlockError::UnsupportedBlockSize(4_096))
        );
    }

    #[test]
    fn bridge_rejects_capacity_beyond_embedded_sdmmc_limit() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(512, u32::MAX as u64 + 1));
        assert_eq!(
            adapter.num_blocks(),
            Err(Fat32BlockError::TooManyBlocks(u32::MAX as u64 + 1))
        );
    }

    #[test]
    fn bridge_reads_and_writes_through_pajoniiir_block_contract() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(512, 4));
        let mut write_block = Block::new();
        write_block.contents.fill(0x5a);

        adapter.write(&[write_block], BlockIdx(2)).unwrap();

        let mut read_block = Block::new();
        adapter
            .read(core::slice::from_mut(&mut read_block), BlockIdx(2))
            .unwrap();
        assert!(read_block.contents.iter().all(|byte| *byte == 0x5a));
    }

    #[test]
    fn explicit_flush_reaches_underlying_transport() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(512, 4));
        adapter.flush_inner().unwrap();

        assert_eq!(adapter.with_inner(|inner| inner.flushes).unwrap(), 1);
    }

    #[test]
    fn zero_block_transfer_is_rejected_by_contract() {
        let adapter = Fat32BlockAdapter::new(MemoryDevice::new(512, 4));
        let mut blocks: [Block; 0] = [];
        assert_eq!(
            adapter.read(&mut blocks, BlockIdx(0)),
            Err(Fat32BlockError::AddressOverflow)
        );
    }
}
