#![no_std]
#![forbid(unsafe_code)]

use core::cell::RefCell;
use core::fmt;
use core::ops::ControlFlow;

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


const FAT32_ID_OFFSET: u32 = 0x4d31_0000;

#[derive(Debug)]
pub enum Fat32FsError<E>
where
    E: core::error::Error + 'static,
{
    Block(Fat32BlockError<E>),
    Backend(embedded_sdmmc::Error<Fat32BlockError<E>>),
    StaleLease,
    InvalidPath,
    PositionTooLarge(u64),
    UnsupportedLongDirectory,
    NameTooLong,
}

impl<E> fmt::Display for Fat32FsError<E>
where
    E: core::error::Error + 'static,
{
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Block(error) => write!(formatter, "FAT32 block adapter error: {error}"),
            Self::Backend(error) => write!(formatter, "FAT32 filesystem error: {error:?}"),
            Self::StaleLease => formatter.write_str("stale FAT32 media lease"),
            Self::InvalidPath => formatter.write_str("invalid FAT32 path"),
            Self::PositionTooLarge(position) => {
                write!(formatter, "FAT32 seek position exceeds u32 range: {position}")
            }
            Self::UnsupportedLongDirectory => {
                formatter.write_str("embedded-sdmmc cannot open long-name directories")
            }
            Self::NameTooLong => formatter.write_str("FAT32 filename exceeds neutral name storage"),
        }
    }
}

impl<E> core::error::Error for Fat32FsError<E> where E: core::error::Error + 'static {}

impl<E> From<embedded_sdmmc::Error<Fat32BlockError<E>>> for Fat32FsError<E>
where
    E: core::error::Error + 'static,
{
    fn from(error: embedded_sdmmc::Error<Fat32BlockError<E>>) -> Self {
        Self::Backend(error)
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Fat32FileHandle {
    lease: pajoniiir_media_session::MediaLease,
    raw: embedded_sdmmc::RawFile,
    len: u64,
    position: u64,
}

impl pajoniiir_media_fs::LeaseBound for Fat32FileHandle {
    fn lease(&self) -> pajoniiir_media_session::MediaLease {
        self.lease
    }
}

impl pajoniiir_media_fs::FileHandle for Fat32FileHandle {
    fn len(&self) -> u64 {
        self.len
    }

    fn position(&self) -> u64 {
        self.position
    }

    fn set_position(&mut self, position: u64) {
        self.position = position;
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Fat32DirectoryHandle {
    lease: pajoniiir_media_session::MediaLease,
    raw: embedded_sdmmc::RawDirectory,
    next_index: usize,
}

impl pajoniiir_media_fs::LeaseBound for Fat32DirectoryHandle {
    fn lease(&self) -> pajoniiir_media_session::MediaLease {
        self.lease
    }
}

impl pajoniiir_media_fs::DirectoryHandle for Fat32DirectoryHandle {}

pub struct Fat32FileSystem<D, T, const MAX_DIRS: usize = 8, const MAX_FILES: usize = 8>
where
    D: WritableBlockDevice,
    D::Error: core::error::Error + 'static,
    T: embedded_sdmmc::TimeSource,
{
    lease: pajoniiir_media_session::MediaLease,
    manager: embedded_sdmmc::VolumeManager<
        Fat32BlockAdapter<D>,
        T,
        MAX_DIRS,
        MAX_FILES,
        1,
    >,
    volume: embedded_sdmmc::RawVolume,
}

impl<D, T, const MAX_DIRS: usize, const MAX_FILES: usize>
    Fat32FileSystem<D, T, MAX_DIRS, MAX_FILES>
where
    D: WritableBlockDevice,
    D::Error: core::error::Error + 'static,
    T: embedded_sdmmc::TimeSource,
{
    pub fn mount(
        device: D,
        time_source: T,
        volume_index: usize,
        lease: pajoniiir_media_session::MediaLease,
    ) -> Result<Self, Fat32FsError<D::Error>> {
        let adapter = Fat32BlockAdapter::new(device);
        adapter.validate_geometry().map_err(Fat32FsError::Block)?;

        let manager = embedded_sdmmc::VolumeManager::<
            Fat32BlockAdapter<D>,
            T,
            MAX_DIRS,
            MAX_FILES,
            1,
        >::new_with_limits(adapter, time_source, FAT32_ID_OFFSET);
        let volume = manager
            .open_raw_volume(embedded_sdmmc::VolumeIdx(volume_index))
            .map_err(Fat32FsError::Backend)?;

        Ok(Self {
            lease,
            manager,
            volume,
        })
    }

    fn ensure_lease(
        &self,
        lease: pajoniiir_media_session::MediaLease,
    ) -> Result<(), Fat32FsError<D::Error>> {
        if lease == self.lease {
            Ok(())
        } else {
            Err(Fat32FsError::StaleLease)
        }
    }

    fn open_directory_raw(
        &self,
        path: &str,
    ) -> Result<embedded_sdmmc::RawDirectory, Fat32FsError<D::Error>> {
        let mut current = self
            .manager
            .open_root_dir(self.volume)
            .map_err(Fat32FsError::Backend)?;
        let trimmed = path.trim_matches('/');
        if trimmed.is_empty() {
            return Ok(current);
        }

        for component in trimmed.split('/') {
            if component.is_empty() {
                continue;
            }

            let next = match self.manager.open_dir(current, component) {
                Ok(directory) => directory,
                Err(error) => {
                    let _ = self.manager.close_dir(current);
                    return Err(match error {
                        embedded_sdmmc::Error::FilenameError(_) => {
                            Fat32FsError::UnsupportedLongDirectory
                        }
                        other => Fat32FsError::Backend(other),
                    });
                }
            };

            if let Err(error) = self.manager.close_dir(current) {
                let _ = self.manager.close_dir(next);
                return Err(Fat32FsError::Backend(error));
            }
            current = next;
        }

        Ok(current)
    }

    fn split_parent_name<'a>(
        &self,
        path: &'a str,
    ) -> Result<(&'a str, &'a str), Fat32FsError<D::Error>> {
        let trimmed = path.trim_matches('/');
        if trimmed.is_empty() {
            return Err(Fat32FsError::InvalidPath);
        }
        Ok(match trimmed.rsplit_once('/') {
            Some((parent, name)) if !name.is_empty() => (parent, name),
            None => ("", trimmed),
            _ => return Err(Fat32FsError::InvalidPath),
        })
    }

    fn open_existing_file_raw(
        &self,
        path: &str,
    ) -> Result<embedded_sdmmc::RawFile, Fat32FsError<D::Error>> {
        let (parent_path, name) = self.split_parent_name(path)?;
        let parent = self.open_directory_raw(parent_path)?;

        let opened = match self.manager.open_long_name_file_in_dir(
            parent,
            name,
            embedded_sdmmc::Mode::ReadOnly,
        ) {
            Ok(file) => Ok(file),
            Err(embedded_sdmmc::Error::NotFound) => self
                .manager
                .open_file_in_dir(parent, name, embedded_sdmmc::Mode::ReadOnly),
            Err(error) => Err(error),
        };

        let close_parent = self.manager.close_dir(parent);
        match (opened, close_parent) {
            (Ok(file), Ok(())) => Ok(file),
            (Ok(file), Err(error)) => {
                let _ = self.manager.close_file(file);
                Err(Fat32FsError::Backend(error))
            }
            (Err(error), _) => Err(Fat32FsError::Backend(error)),
        }
    }

    fn neutral_entry(
        entry: &embedded_sdmmc::DirEntry,
        name_len: usize,
    ) -> pajoniiir_media_fs::DirEntry {
        pajoniiir_media_fs::DirEntry {
            kind: if entry.attributes.is_directory() {
                pajoniiir_media_fs::EntryKind::Directory
            } else {
                pajoniiir_media_fs::EntryKind::File
            },
            len: entry.size as u64,
            modified_unix_seconds: None,
            name_len: name_len as u16,
        }
    }

    fn is_visible_entry(entry: &embedded_sdmmc::DirEntry) -> bool {
        !entry.attributes.is_volume()
            && entry.name != embedded_sdmmc::ShortFileName::this_dir()
            && entry.name != embedded_sdmmc::ShortFileName::parent_dir()
    }
}

impl<D, T, const MAX_DIRS: usize, const MAX_FILES: usize> pajoniiir_media_fs::LeaseBound
    for Fat32FileSystem<D, T, MAX_DIRS, MAX_FILES>
where
    D: WritableBlockDevice,
    D::Error: core::error::Error + 'static,
    T: embedded_sdmmc::TimeSource,
{
    fn lease(&self) -> pajoniiir_media_session::MediaLease {
        self.lease
    }
}

impl<D, T, const MAX_DIRS: usize, const MAX_FILES: usize> pajoniiir_media_fs::FileSystem
    for Fat32FileSystem<D, T, MAX_DIRS, MAX_FILES>
where
    D: WritableBlockDevice,
    D::Error: core::error::Error + 'static,
    T: embedded_sdmmc::TimeSource,
{
    type Error = Fat32FsError<D::Error>;
    type File = Fat32FileHandle;
    type Directory = Fat32DirectoryHandle;

    fn kind(&self) -> pajoniiir_media_fs::FileSystemKind {
        pajoniiir_media_fs::FileSystemKind::Fat32
    }

    fn capabilities(&self) -> pajoniiir_media_fs::FileSystemCapabilities {
        pajoniiir_media_fs::FileSystemCapabilities {
            read: true,
            write: false,
            directories: true,
            // LFN files can be read/listed, but embedded-sdmmc 0.10 opens
            // directories through the 8.3 ToShortFileName path.
            long_names: false,
            flush: false,
            random_seek: true,
            streaming_directory_visit: true,
        }
    }

    fn stat(&mut self, path: &str) -> Result<pajoniiir_media_fs::FileStat, Self::Error> {
        if path.trim_matches('/').is_empty() {
            return Ok(pajoniiir_media_fs::FileStat {
                kind: pajoniiir_media_fs::EntryKind::Directory,
                len: 0,
                modified_unix_seconds: None,
            });
        }

        match self.open_existing_file_raw(path) {
            Ok(file) => {
                let len = self
                    .manager
                    .file_length(file)
                    .map_err(Fat32FsError::Backend)? as u64;
                self.manager
                    .close_file(file)
                    .map_err(Fat32FsError::Backend)?;
                Ok(pajoniiir_media_fs::FileStat {
                    kind: pajoniiir_media_fs::EntryKind::File,
                    len,
                    modified_unix_seconds: None,
                })
            }
            Err(Fat32FsError::Backend(embedded_sdmmc::Error::OpenedDirAsFile))
            | Err(Fat32FsError::Backend(embedded_sdmmc::Error::NotFound))
            | Err(Fat32FsError::Backend(embedded_sdmmc::Error::FilenameError(_))) => {
                let directory = self.open_directory_raw(path)?;
                self.manager
                    .close_dir(directory)
                    .map_err(Fat32FsError::Backend)?;
                Ok(pajoniiir_media_fs::FileStat {
                    kind: pajoniiir_media_fs::EntryKind::Directory,
                    len: 0,
                    modified_unix_seconds: None,
                })
            }
            Err(error) => Err(error),
        }
    }

    fn open_read(&mut self, path: &str) -> Result<Self::File, Self::Error> {
        let raw = self.open_existing_file_raw(path)?;
        let len = match self.manager.file_length(raw) {
            Ok(len) => len as u64,
            Err(error) => {
                let _ = self.manager.close_file(raw);
                return Err(Fat32FsError::Backend(error));
            }
        };
        let position = match self.manager.file_offset(raw) {
            Ok(position) => position as u64,
            Err(error) => {
                let _ = self.manager.close_file(raw);
                return Err(Fat32FsError::Backend(error));
            }
        };

        Ok(Fat32FileHandle {
            lease: self.lease,
            raw,
            len,
            position,
        })
    }

    fn close_file(&mut self, file: Self::File) -> Result<(), Self::Error> {
        self.ensure_lease(file.lease)?;
        self.manager
            .close_file(file.raw)
            .map_err(Fat32FsError::Backend)
    }

    fn read(&mut self, file: &mut Self::File, output: &mut [u8]) -> Result<usize, Self::Error> {
        self.ensure_lease(file.lease)?;
        let read = self
            .manager
            .read(file.raw, output)
            .map_err(Fat32FsError::Backend)?;
        file.position = file.position.saturating_add(read as u64);
        Ok(read)
    }

    fn seek_absolute(&mut self, file: &mut Self::File, position: u64) -> Result<(), Self::Error> {
        self.ensure_lease(file.lease)?;
        let position_u32 =
            u32::try_from(position).map_err(|_| Fat32FsError::PositionTooLarge(position))?;
        self.manager
            .file_seek_from_start(file.raw, position_u32)
            .map_err(Fat32FsError::Backend)?;
        file.position = position;
        Ok(())
    }

    fn open_directory(&mut self, path: &str) -> Result<Self::Directory, Self::Error> {
        let raw = self.open_directory_raw(path)?;
        Ok(Fat32DirectoryHandle {
            lease: self.lease,
            raw,
            next_index: 0,
        })
    }

    fn next_entry(
        &mut self,
        directory: &mut Self::Directory,
        name_storage: &mut [u8; pajoniiir_media_fs::FS_NAME_MAX],
    ) -> Result<Option<pajoniiir_media_fs::DirEntry>, Self::Error> {
        self.ensure_lease(directory.lease)?;

        let target = directory.next_index;
        let mut visible_index = 0usize;
        let mut found = None;
        let mut name_error = false;
        let mut lfn_storage = [0u8; pajoniiir_media_fs::FS_NAME_MAX];
        let mut lfn_buffer = embedded_sdmmc::LfnBuffer::new(&mut lfn_storage);

        self.manager
            .iterate_dir_lfn(directory.raw, &mut lfn_buffer, |entry, long_name| {
                if !Self::is_visible_entry(entry) {
                    return ControlFlow::Continue(());
                }
                if visible_index != target {
                    visible_index = visible_index.saturating_add(1);
                    return ControlFlow::Continue(());
                }

                let name_len = match long_name {
                    Some(name) => copy_utf8(name.as_bytes(), name_storage),
                    None => encode_short_name(entry.name, name_storage),
                };
                let Some(name_len) = name_len else {
                    name_error = true;
                    return ControlFlow::Break(());
                };
                found = Some(Self::neutral_entry(entry, name_len));
                ControlFlow::Break(())
            })
            .map_err(Fat32FsError::Backend)?;

        if name_error {
            return Err(Fat32FsError::NameTooLong);
        }
        if found.is_some() {
            directory.next_index = directory.next_index.saturating_add(1);
        }
        Ok(found)
    }

    fn close_directory(&mut self, directory: Self::Directory) -> Result<(), Self::Error> {
        self.ensure_lease(directory.lease)?;
        self.manager
            .close_dir(directory.raw)
            .map_err(Fat32FsError::Backend)
    }

    fn visit_directory<V: pajoniiir_media_fs::DirectoryVisitor>(
        &mut self,
        path: &str,
        name_storage: &mut [u8; pajoniiir_media_fs::FS_NAME_MAX],
        visitor: &mut V,
    ) -> Result<(), Self::Error> {
        let directory = self.open_directory_raw(path)?;
        let mut lfn_storage = [0u8; pajoniiir_media_fs::FS_NAME_MAX];
        let mut lfn_buffer = embedded_sdmmc::LfnBuffer::new(&mut lfn_storage);
        let mut name_error = false;

        let iterate_result =
            self.manager
                .iterate_dir_lfn(directory, &mut lfn_buffer, |entry, long_name| {
                    if !Self::is_visible_entry(entry) {
                        return ControlFlow::Continue(());
                    }

                    match long_name {
                        Some(name) => {
                            let bytes = name.as_bytes();
                            let Some(name_len) = copy_utf8(bytes, name_storage) else {
                                name_error = true;
                                return ControlFlow::Break(());
                            };
                            let item = Self::neutral_entry(entry, name_len);
                            if visitor.visit(item, &name_storage[..name_len]) {
                                ControlFlow::Continue(())
                            } else {
                                ControlFlow::Break(())
                            }
                        }
                        None => {
                            let Some(name_len) = encode_short_name(entry.name, name_storage) else {
                                name_error = true;
                                return ControlFlow::Break(());
                            };
                            let item = Self::neutral_entry(entry, name_len);
                            if visitor.visit(item, &name_storage[..name_len]) {
                                ControlFlow::Continue(())
                            } else {
                                ControlFlow::Break(())
                            }
                        }
                    }
                });

        let close_result = self.manager.close_dir(directory);
        iterate_result.map_err(Fat32FsError::Backend)?;
        close_result.map_err(Fat32FsError::Backend)?;
        if name_error {
            Err(Fat32FsError::NameTooLong)
        } else {
            Ok(())
        }
    }
}

fn copy_utf8(input: &[u8], output: &mut [u8]) -> Option<usize> {
    if input.len() > output.len() {
        return None;
    }
    output[..input.len()].copy_from_slice(input);
    Some(input.len())
}

fn encode_short_name(name: embedded_sdmmc::ShortFileName, output: &mut [u8]) -> Option<usize> {
    let mut written = 0usize;
    written = encode_latin1(name.base_name(), output, written)?;
    let extension = name.extension();
    if !extension.is_empty() {
        if written >= output.len() {
            return None;
        }
        output[written] = b'.';
        written += 1;
        written = encode_latin1(extension, output, written)?;
    }
    Some(written)
}

fn encode_latin1(input: &[u8], output: &mut [u8], mut written: usize) -> Option<usize> {
    for &byte in input {
        if byte < 0x80 {
            if written >= output.len() {
                return None;
            }
            output[written] = byte;
            written += 1;
        } else {
            if written + 1 >= output.len() {
                return None;
            }
            output[written] = 0xc0 | (byte >> 6);
            output[written + 1] = 0x80 | (byte & 0x3f);
            written += 2;
        }
    }
    Some(written)
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
