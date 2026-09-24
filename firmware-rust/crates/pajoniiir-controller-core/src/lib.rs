#![no_std]
#![forbid(unsafe_code)]

use pajoniiir_core::DeckId;

/// Controller-independent product action.
///
/// Raw USB MIDI bytes and controller-specific note/CC values must be translated
/// into this semantic layer before they can affect product state.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SemanticControl {
    Play,
    Cue,
    Sync,
    Shift,
    Tempo,
    Jog,
    LoopIn,
    LoopOut,
    Reloop,
    BeatJump,
    HotCue(u8),
    ChannelFader,
    Crossfader,
    Trim,
    EqHigh,
    EqMid,
    EqLow,
    Filter,
    Pfl,
    MasterVolume,
    HeadphoneMix,
    HeadphoneLevel,
    Browse,
    Load,
    BeatFxSelect,
    BeatFxDepth,
    SmartCfx,
    SmartFader,
}

/// Normalized semantic control payload.
#[derive(Clone, Copy, Debug, PartialEq)]
pub enum ControlValue {
    Pressed(bool),
    Relative(i16),
    AbsoluteU14(u16),
    Normalized(f32),
}

/// A controller-independent event entering the product scheduler.
#[derive(Clone, Copy, Debug, PartialEq)]
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
    Dim,
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
}
