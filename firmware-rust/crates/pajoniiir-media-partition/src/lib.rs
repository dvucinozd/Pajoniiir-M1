#![no_std]
#![forbid(unsafe_code)]

use core::num::NonZeroU64;

pub const MAX_PARTITION_CANDIDATES: usize = 8;
pub const MIN_SECTOR_SIZE: usize = 512;

const MICROSOFT_BASIC_DATA_GUID: [u8; 16] = [
    0xa2, 0xa0, 0xd0, 0xeb, 0xe5, 0xb9, 0x33, 0x44, 0x87, 0xc0, 0x68, 0xb6, 0xb7, 0x26, 0x99,
    0xc7,
];

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum VolumeKind {
    Unknown,
    Fat,
    ExFat,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PartitionCandidate {
    pub first_lba: u64,
    pub sector_count: Option<NonZeroU64>,
    pub kind: VolumeKind,
}

impl PartitionCandidate {
    const EMPTY: Self = Self {
        first_lba: 0,
        sector_count: None,
        kind: VolumeKind::Unknown,
    };
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PartitionLayout {
    candidates: [PartitionCandidate; MAX_PARTITION_CANDIDATES],
    count: usize,
    protective_mbr: bool,
}

impl PartitionLayout {
    pub const fn new() -> Self {
        Self {
            candidates: [PartitionCandidate::EMPTY; MAX_PARTITION_CANDIDATES],
            count: 0,
            protective_mbr: false,
        }
    }

    pub fn clear(&mut self) {
        *self = Self::new();
    }

    pub fn candidates(&self) -> &[PartitionCandidate] {
        &self.candidates[..self.count]
    }

    pub const fn count(&self) -> usize {
        self.count
    }

    pub const fn has_protective_mbr(&self) -> bool {
        self.protective_mbr
    }

    pub fn append_candidate(
        &mut self,
        first_lba: u64,
        sector_count: Option<NonZeroU64>,
        kind: VolumeKind,
    ) -> bool {
        if let Some(existing) = self.candidates[..self.count]
            .iter_mut()
            .find(|candidate| candidate.first_lba == first_lba)
        {
            if existing.kind == VolumeKind::Unknown && kind != VolumeKind::Unknown {
                existing.kind = kind;
            }
            if existing.sector_count.is_none() {
                existing.sector_count = sector_count;
            }
            return true;
        }

        if self.count >= MAX_PARTITION_CANDIDATES {
            return false;
        }

        self.candidates[self.count] = PartitionCandidate {
            first_lba,
            sector_count,
            kind,
        };
        self.count += 1;
        true
    }
}

impl Default for PartitionLayout {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PartitionScanResult {
    Ok,
    Invalid,
    NeedsGpt,
    NoCandidate,
}

pub fn classify_boot_sector(sector: &[u8]) -> VolumeKind {
    if !has_boot_signature(sector) || !has_valid_boot_jump(sector) {
        return VolumeKind::Unknown;
    }

    if sector.get(3..11) == Some(b"EXFAT   ".as_slice()) {
        return VolumeKind::ExFat;
    }

    if sector.get(54..57) == Some(b"FAT".as_slice())
        || sector.get(82..87) == Some(b"FAT32".as_slice())
    {
        return VolumeKind::Fat;
    }

    VolumeKind::Unknown
}

pub fn scan_mbr_or_superfloppy(
    sector: &[u8],
    layout: &mut PartitionLayout,
) -> PartitionScanResult {
    layout.clear();
    if !has_boot_signature(sector) {
        return PartitionScanResult::Invalid;
    }

    let superfloppy_kind = classify_boot_sector(sector);
    if superfloppy_kind != VolumeKind::Unknown {
        return if layout.append_candidate(0, None, superfloppy_kind) {
            PartitionScanResult::Ok
        } else {
            PartitionScanResult::Invalid
        };
    }

    for index in 0..4usize {
        let offset = 446 + index * 16;
        let entry = &sector[offset..offset + 16];
        let partition_type = entry[4];
        let first_lba = read_u32_le(&entry[8..12]);
        let sector_count = read_u32_le(&entry[12..16]);

        if partition_type == 0 {
            continue;
        }
        if partition_type == 0xee {
            layout.protective_mbr = true;
            continue;
        }
        if first_lba == 0 || sector_count == 0 || !mbr_range_fits(first_lba, sector_count) {
            continue;
        }

        let kind = if is_mbr_fat_type(partition_type) {
            Some(VolumeKind::Fat)
        } else if partition_type == 0x07 {
            Some(VolumeKind::Unknown)
        } else {
            None
        };

        if let Some(kind) = kind {
            let sectors = NonZeroU64::new(sector_count as u64);
            let _ = layout.append_candidate(first_lba as u64, sectors, kind);
        }
    }

    if layout.protective_mbr {
        PartitionScanResult::NeedsGpt
    } else if layout.count != 0 {
        PartitionScanResult::Ok
    } else {
        PartitionScanResult::NoCandidate
    }
}

pub fn scan_gpt(
    header_sector: &[u8],
    entries: &[u8],
    layout: &mut PartitionLayout,
) -> PartitionScanResult {
    layout.clear();
    if header_sector.len() < MIN_SECTOR_SIZE || header_sector.get(..8) != Some(b"EFI PART".as_slice())
    {
        return PartitionScanResult::Invalid;
    }

    let header_size = read_u32_le(&header_sector[12..16]) as usize;
    let entry_count = read_u32_le(&header_sector[80..84]) as usize;
    let entry_size = read_u32_le(&header_sector[84..88]) as usize;
    if !(92..=MIN_SECTOR_SIZE).contains(&header_size)
        || entry_count == 0
        || !(128..=512).contains(&entry_size)
    {
        return PartitionScanResult::Invalid;
    }

    let available_entries = entries.len() / entry_size;
    let entries_to_scan = available_entries.min(entry_count);

    for index in 0..entries_to_scan {
        let entry = &entries[index * entry_size..(index + 1) * entry_size];
        if entry.get(..16) != Some(MICROSOFT_BASIC_DATA_GUID.as_slice()) {
            continue;
        }

        let first_lba = read_u64_le(&entry[32..40]);
        let last_lba = read_u64_le(&entry[40..48]);
        if first_lba == 0 || last_lba < first_lba {
            continue;
        }
        let Some(sector_count) = last_lba
            .checked_sub(first_lba)
            .and_then(|distance| distance.checked_add(1))
            .and_then(NonZeroU64::new)
        else {
            continue;
        };

        let _ = layout.append_candidate(first_lba, Some(sector_count), VolumeKind::Unknown);
    }

    if layout.count != 0 {
        PartitionScanResult::Ok
    } else {
        PartitionScanResult::NoCandidate
    }
}

fn has_boot_signature(sector: &[u8]) -> bool {
    sector.len() >= MIN_SECTOR_SIZE && read_u16_le(&sector[510..512]) == 0xaa55
}

fn has_valid_boot_jump(sector: &[u8]) -> bool {
    matches!(sector.first().copied(), Some(0xeb | 0xe9))
}

fn is_mbr_fat_type(partition_type: u8) -> bool {
    matches!(partition_type, 0x01 | 0x04 | 0x06 | 0x0b | 0x0c | 0x0e)
}

fn mbr_range_fits(first_lba: u32, sector_count: u32) -> bool {
    (first_lba as u64)
        .checked_add(sector_count as u64)
        .and_then(|end| end.checked_sub(1))
        .is_some_and(|end| end <= u32::MAX as u64)
}

fn read_u16_le(input: &[u8]) -> u16 {
    u16::from_le_bytes([input[0], input[1]])
}

fn read_u32_le(input: &[u8]) -> u32 {
    u32::from_le_bytes([input[0], input[1], input[2], input[3]])
}

fn read_u64_le(input: &[u8]) -> u64 {
    u64::from_le_bytes([
        input[0], input[1], input[2], input[3], input[4], input[5], input[6], input[7],
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    fn put_u16_le(output: &mut [u8], value: u16) {
        output.copy_from_slice(&value.to_le_bytes());
    }

    fn put_u32_le(output: &mut [u8], value: u32) {
        output.copy_from_slice(&value.to_le_bytes());
    }

    fn put_u64_le(output: &mut [u8], value: u64) {
        output.copy_from_slice(&value.to_le_bytes());
    }

    fn exfat_boot() -> [u8; 512] {
        let mut sector = [0u8; 512];
        sector[0] = 0xeb;
        sector[1] = 0x76;
        sector[2] = 0x90;
        sector[3..11].copy_from_slice(b"EXFAT   ");
        put_u16_le(&mut sector[510..512], 0xaa55);
        sector
    }

    fn fat32_boot() -> [u8; 512] {
        let mut sector = [0u8; 512];
        sector[0] = 0xeb;
        sector[1] = 0x58;
        sector[2] = 0x90;
        sector[82..90].copy_from_slice(b"FAT32   ");
        put_u16_le(&mut sector[510..512], 0xaa55);
        sector
    }

    fn mbr(partition_type: u8, first_lba: u32, sectors: u32) -> [u8; 512] {
        let mut sector = [0u8; 512];
        let entry = &mut sector[446..462];
        entry[4] = partition_type;
        put_u32_le(&mut entry[8..12], first_lba);
        put_u32_le(&mut entry[12..16], sectors);
        put_u16_le(&mut sector[510..512], 0xaa55);
        sector
    }

    fn gpt_header(entry_count: u32, entry_size: u32) -> [u8; 512] {
        let mut sector = [0u8; 512];
        sector[..8].copy_from_slice(b"EFI PART");
        put_u32_le(&mut sector[12..16], 92);
        put_u64_le(&mut sector[72..80], 2);
        put_u32_le(&mut sector[80..84], entry_count);
        put_u32_le(&mut sector[84..88], entry_size);
        sector
    }

    fn write_basic_data_entry(entry: &mut [u8], first_lba: u64, last_lba: u64) {
        entry[..16].copy_from_slice(&MICROSOFT_BASIC_DATA_GUID);
        put_u64_le(&mut entry[32..40], first_lba);
        put_u64_le(&mut entry[40..48], last_lba);
    }

    #[test]
    fn classifies_released_fat_and_exfat_boot_sectors() {
        assert_eq!(classify_boot_sector(&exfat_boot()), VolumeKind::ExFat);
        assert_eq!(classify_boot_sector(&fat32_boot()), VolumeKind::Fat);
        assert_eq!(classify_boot_sector(&[0u8; 512]), VolumeKind::Unknown);
        assert_eq!(classify_boot_sector(&[0u8; 511]), VolumeKind::Unknown);
    }

    #[test]
    fn exfat_superfloppy_is_candidate_at_lba_zero_with_unknown_extent() {
        let mut layout = PartitionLayout::new();
        assert_eq!(
            scan_mbr_or_superfloppy(&exfat_boot(), &mut layout),
            PartitionScanResult::Ok
        );
        assert_eq!(
            layout.candidates(),
            &[PartitionCandidate {
                first_lba: 0,
                sector_count: None,
                kind: VolumeKind::ExFat,
            }]
        );
    }

    #[test]
    fn fat32_and_type_07_mbr_candidates_match_released_behavior() {
        let mut layout = PartitionLayout::new();
        assert_eq!(
            scan_mbr_or_superfloppy(&mbr(0x0c, 2_048, 65_536), &mut layout),
            PartitionScanResult::Ok
        );
        assert_eq!(layout.candidates()[0].first_lba, 2_048);
        assert_eq!(
            layout.candidates()[0].sector_count,
            NonZeroU64::new(65_536)
        );
        assert_eq!(layout.candidates()[0].kind, VolumeKind::Fat);

        assert_eq!(
            scan_mbr_or_superfloppy(&mbr(0x07, 4_096, 131_072), &mut layout),
            PartitionScanResult::Ok
        );
        assert_eq!(layout.candidates()[0].kind, VolumeKind::Unknown);
    }

    #[test]
    fn invalid_mbr_extent_past_u32_address_space_is_rejected() {
        let mut layout = PartitionLayout::new();
        assert_eq!(
            scan_mbr_or_superfloppy(&mbr(0x0c, u32::MAX - 8, 16), &mut layout),
            PartitionScanResult::NoCandidate
        );
        assert_eq!(layout.count(), 0);
    }

    #[test]
    fn protective_mbr_requires_gpt_scan() {
        let mut layout = PartitionLayout::new();
        assert_eq!(
            scan_mbr_or_superfloppy(&mbr(0xee, 1, u32::MAX), &mut layout),
            PartitionScanResult::NeedsGpt
        );
        assert!(layout.has_protective_mbr());
    }

    #[test]
    fn gpt_basic_data_candidate_matches_released_fixture() {
        let header = gpt_header(4, 128);
        let mut entries = [0u8; 512];
        write_basic_data_entry(&mut entries[..128], 32_768, 98_303);
        let mut layout = PartitionLayout::new();

        assert_eq!(
            scan_gpt(&header, &entries, &mut layout),
            PartitionScanResult::Ok
        );
        assert_eq!(
            layout.candidates()[0],
            PartitionCandidate {
                first_lba: 32_768,
                sector_count: NonZeroU64::new(65_536),
                kind: VolumeKind::Unknown,
            }
        );
    }

    #[test]
    fn gpt_supports_valid_extents_beyond_u32_lba() {
        let header = gpt_header(1, 128);
        let mut entries = [0u8; 128];
        let first = u32::MAX as u64 + 4_096;
        write_basic_data_entry(&mut entries, first, first + 65_535);
        let mut layout = PartitionLayout::new();

        assert_eq!(
            scan_gpt(&header, &entries, &mut layout),
            PartitionScanResult::Ok
        );
        assert_eq!(layout.candidates()[0].first_lba, first);
        assert_eq!(
            layout.candidates()[0].sector_count,
            NonZeroU64::new(65_536)
        );
    }

    #[test]
    fn malformed_gpt_and_short_mbr_fail_closed_without_panicking() {
        let mut layout = PartitionLayout::new();
        assert_eq!(
            scan_gpt(&[0u8; 512], &[0u8; 512], &mut layout),
            PartitionScanResult::Invalid
        );
        assert_eq!(
            scan_mbr_or_superfloppy(&[0u8; 511], &mut layout),
            PartitionScanResult::Invalid
        );
    }

    #[test]
    fn duplicate_candidate_upgrades_kind_without_consuming_slot() {
        let mut layout = PartitionLayout::new();
        assert!(layout.append_candidate(
            8_192,
            NonZeroU64::new(262_144),
            VolumeKind::Unknown
        ));
        assert!(layout.append_candidate(
            8_192,
            NonZeroU64::new(262_144),
            VolumeKind::ExFat
        ));
        assert_eq!(layout.count(), 1);
        assert_eq!(layout.candidates()[0].kind, VolumeKind::ExFat);
    }
}
