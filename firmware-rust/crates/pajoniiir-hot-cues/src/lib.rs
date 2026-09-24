#![no_std]
#![forbid(unsafe_code)]

use pajoniiir_core::MediaTrackId;

pub const HOT_CUE_SLOT_COUNT: usize = 8;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum HotCueKind {
    Single,
    Loop,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HotCueSlot {
    pub pos_ms: u32,
    pub end_ms: u32,
    pub kind: HotCueKind,
}

impl HotCueSlot {
    pub const fn single(pos_ms: u32) -> Self {
        Self {
            pos_ms,
            end_ms: 0,
            kind: HotCueKind::Single,
        }
    }

    pub const fn loop_region(pos_ms: u32, end_ms: u32) -> Option<Self> {
        if end_ms > pos_ms {
            Some(Self {
                pos_ms,
                end_ms,
                kind: HotCueKind::Loop,
            })
        } else {
            None
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct HotCueBank {
    track_id: MediaTrackId,
    slots: [Option<HotCueSlot>; HOT_CUE_SLOT_COUNT],
}

impl HotCueBank {
    pub const fn empty(track_id: MediaTrackId) -> Self {
        Self {
            track_id,
            slots: [None; HOT_CUE_SLOT_COUNT],
        }
    }

    pub const fn track_id(&self) -> MediaTrackId {
        self.track_id
    }

    pub fn slot(&self, index: u8) -> Option<HotCueSlot> {
        self.slots.get(index as usize).copied().flatten()
    }

    pub fn set_single(&mut self, index: u8, pos_ms: u32) -> bool {
        let Some(slot) = self.slots.get_mut(index as usize) else {
            return false;
        };
        *slot = Some(HotCueSlot::single(pos_ms));
        true
    }

    pub fn set_loop(&mut self, index: u8, pos_ms: u32, end_ms: u32) -> bool {
        let Some(cue) = HotCueSlot::loop_region(pos_ms, end_ms) else {
            return false;
        };
        let Some(slot) = self.slots.get_mut(index as usize) else {
            return false;
        };
        *slot = Some(cue);
        true
    }

    pub fn clear(&mut self, index: u8) -> bool {
        let Some(slot) = self.slots.get_mut(index as usize) else {
            return false;
        };
        if slot.is_none() {
            return false;
        }
        *slot = None;
        true
    }

    pub fn exists_mask(&self) -> u8 {
        let mut mask = 0u8;
        for (index, slot) in self.slots.iter().enumerate() {
            if slot.is_some() {
                mask |= 1u8 << index;
            }
        }
        mask
    }
}

/// Storage boundary for the platform adapter.
///
/// The product model owns cue semantics. ESP32-P4 firmware can implement this
/// trait with NVS or another bounded persistent store without coupling flash I/O
/// to the controller reducer.
pub trait HotCueStore {
    type Error;

    fn load(&mut self, track_id: MediaTrackId) -> Result<Option<HotCueBank>, Self::Error>;
    fn save(&mut self, bank: &HotCueBank) -> Result<(), Self::Error>;
    fn clear(&mut self, track_id: MediaTrackId) -> Result<(), Self::Error>;
}

#[cfg(test)]
mod tests {
    use super::*;

    fn id(seed: u8) -> MediaTrackId {
        MediaTrackId([seed; 16])
    }

    #[test]
    fn empty_bank_has_no_slots() {
        let bank = HotCueBank::empty(id(1));
        assert_eq!(bank.track_id(), id(1));
        assert_eq!(bank.exists_mask(), 0);
        for slot in 0..HOT_CUE_SLOT_COUNT as u8 {
            assert_eq!(bank.slot(slot), None);
        }
    }

    #[test]
    fn single_and_loop_slots_are_bounded() {
        let mut bank = HotCueBank::empty(id(2));
        assert!(bank.set_single(0, 1_000));
        assert!(bank.set_loop(7, 2_000, 4_000));
        assert!(!bank.set_single(8, 5_000));
        assert!(!bank.set_loop(1, 5_000, 5_000));

        assert_eq!(bank.slot(0), Some(HotCueSlot::single(1_000)));
        assert_eq!(
            bank.slot(7),
            Some(HotCueSlot {
                pos_ms: 2_000,
                end_ms: 4_000,
                kind: HotCueKind::Loop,
            })
        );
        assert_eq!(bank.exists_mask(), 0x81);
    }

    #[test]
    fn clear_is_idempotent_and_reports_change() {
        let mut bank = HotCueBank::empty(id(3));
        assert!(!bank.clear(3));
        assert!(bank.set_single(3, 9_000));
        assert!(bank.clear(3));
        assert!(!bank.clear(3));
        assert_eq!(bank.exists_mask(), 0);
    }
}
