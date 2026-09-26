#![no_std]
#![forbid(unsafe_code)]

pub use pajoniiir_core::DeckId;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PadMode {
    HotCue,
    BeatLoop,
    BeatJump,
    KeyShift,
    Keyboard,
    PadFx1,
    PadFx2,
    Sampler,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct PadAction {
    pub pad: u8,
    pub mode: PadMode,
    pub shifted: bool,
    pub pressed: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DeckExtAction {
    Censor,
    SyncMaster,
    ReloopStop,
    LoopAdjustIn,
    LoopAdjustOut,
    Quantize,
    SyncOff,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DeckExtActionValue {
    pub action: DeckExtAction,
    pub pressed: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BeatFxTarget {
    ChannelOne,
    ChannelTwo,
    Both,
}

/// Controller-independent product action.
///
/// Raw USB MIDI bytes and controller-specific note/CC values must be translated
/// into this semantic layer before they can affect product state.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SemanticControl {
    Play,
    Cue,
    JogScratch,
    JogBend,
    JogTouch,
    Tempo,
    Shift,
    ToStart,
    Sync,
    TempoRange,
    LoopIn,
    LoopOut,
    ReloopExit,
    LoopHalve,
    LoopDouble,
    BeatJumpBack,
    BeatJumpForward,
    PadModeHotCue,
    PadModeBeatLoop,
    PadModeBeatJump,
    PadModeKeyShift,
    PadAction,
    PadModeKeyboard,
    PadModePadFx1,
    PadModePadFx2,
    PadModeSampler,
    JogSearch,
    JogSearchTouch,
    DeckExtAction,
    LoopSize,
    ChannelVolume,
    Crossfader,
    Trim,
    EqHigh,
    EqMid,
    EqLow,
    Filter,
    Pfl,
    HeadphoneMix,
    BrowseDelta,
    Load,
    BrowsePress,
    ShiftBrowseDelta,
    ShiftBrowsePress,
    ShiftLoad,
    SmartCfx,
    SmartFader,
    BeatFxSelectNext,
    BeatFxSelectPrev,
    BeatFxBeatDec,
    BeatFxBeatInc,
    BeatFxTarget,
    BeatFxDepth,
    BeatFxOn,
    BeatFxClear,
    MasterVolume,
    MasterCue,
    HeadphoneLevel,
    SmartCfxShift,
    SmartFaderShift,
    BeatFxBeatDecShift,
    BeatFxBeatIncShift,
}

/// Exact controller-independent payload.
///
/// Absolute controls keep their integer range instead of being prematurely
/// converted to floating point, which preserves deterministic replay and host
/// parity with the released controller-profile runtime.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ControlValue {
    Pressed(bool),
    Relative(i16),
    Absolute { value: u16, max: u16 },
    PadAction(PadAction),
    DeckExtAction(DeckExtActionValue),
    BeatFxTarget(BeatFxTarget),
}

/// A controller-independent event entering the product scheduler.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct ControlEvent {
    pub deck: Option<DeckId>,
    pub control: SemanticControl,
    pub value: ControlValue,
}

/// Semantic LED state before controller-specific output mapping.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LedState {
    Off,
    On,
    Blink,
    Value(u8),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn play_event_does_not_encode_midi_transport() {
        let event = ControlEvent {
            deck: Some(DeckId::One),
            control: SemanticControl::Play,
            value: ControlValue::Pressed(true),
        };

        assert_eq!(event.control, SemanticControl::Play);
        assert_eq!(event.deck, Some(DeckId::One));
    }

    #[test]
    fn pad_action_is_semantic_not_wire_packed() {
        let value = ControlValue::PadAction(PadAction {
            pad: 3,
            mode: PadMode::BeatJump,
            shifted: true,
            pressed: true,
        });

        assert_eq!(
            value,
            ControlValue::PadAction(PadAction {
                pad: 3,
                mode: PadMode::BeatJump,
                shifted: true,
                pressed: true,
            })
        );
    }
}
