#![no_std]
#![forbid(unsafe_code)]

use pajoniiir_controller_core::{
    ControlEvent, ControlValue, DeckExtAction, DeckId, PadMode, SemanticControl,
};
use pajoniiir_track_analysis::{TrackAnalysis, phase_align_target_ms};

pub const PITCH_CENTER: u16 = 8192;
pub const PITCH_MAX: u16 = 16383;
pub const DEFAULT_TEMPO_RANGE_PERCENT: u16 = 10;
pub const BEAT_SYNC_MAX_PERCENT: i16 = 20;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PerformanceMode {
    HotCue,
    LoopRoll,
    BeatJump,
    KeyShift,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum LoopAdjustMode {
    None,
    In,
    Out,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct PendingPlayback {
    request_id: u32,
    playing: bool,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DeckState {
    pub playing: bool,
    pub position_ms: u32,
    pub cue_point_ms: u32,
    pub pitch_raw: u16,
    pub pitch_centipercent: i16,
    pub tempo_range_percent: u16,
    pub perf_mode: PerformanceMode,
    pub pad_mode: PadMode,
    pub sync_enabled: bool,
    pub sync_master: bool,
    pub quantize_enabled: bool,
    pub loop_adjust_mode: LoopAdjustMode,
    pub censor_active: bool,
    pub master_tempo: bool,
    pub controller_connected: bool,
    pub shift_held: bool,
    pub jog_touched: bool,
    pub base_bpm_x100: u32,
    playback_generation: u32,
    pending_playback: Option<PendingPlayback>,
}

impl DeckState {
    pub const fn new() -> Self {
        Self {
            playing: false,
            position_ms: 0,
            cue_point_ms: 0,
            pitch_raw: PITCH_CENTER,
            pitch_centipercent: 0,
            tempo_range_percent: DEFAULT_TEMPO_RANGE_PERCENT,
            perf_mode: PerformanceMode::HotCue,
            pad_mode: PadMode::HotCue,
            sync_enabled: false,
            sync_master: false,
            quantize_enabled: false,
            loop_adjust_mode: LoopAdjustMode::None,
            censor_active: false,
            master_tempo: false,
            controller_connected: false,
            shift_held: false,
            jog_touched: false,
            base_bpm_x100: 12_000,
            playback_generation: 0,
            pending_playback: None,
        }
    }
}

impl Default for DeckState {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum DeckEffect {
    PlaybackRequest {
        deck: DeckId,
        playing: bool,
        request_id: u32,
    },
    Pause {
        deck: DeckId,
    },
    Seek {
        deck: DeckId,
        position_ms: u32,
    },
    SetPitchCentipercent {
        deck: DeckId,
        value: i16,
    },
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct DeckEffects {
    pub items: [Option<DeckEffect>; 2],
}

impl DeckEffects {
    pub const NONE: Self = Self {
        items: [None, None],
    };

    pub const fn one(effect: DeckEffect) -> Self {
        Self {
            items: [Some(effect), None],
        }
    }

    pub const fn two(first: DeckEffect, second: DeckEffect) -> Self {
        Self {
            items: [Some(first), Some(second)],
        }
    }
}

pub struct DeckProductState {
    decks: [DeckState; 2],
    sync_master: Option<DeckId>,
}

impl Default for DeckProductState {
    fn default() -> Self {
        Self::new()
    }
}

impl DeckProductState {
    pub const fn new() -> Self {
        Self {
            decks: [DeckState::new(), DeckState::new()],
            sync_master: None,
        }
    }

    pub fn deck(&self, deck: DeckId) -> &DeckState {
        &self.decks[deck_index(deck)]
    }

    pub fn set_base_bpm_x100(&mut self, deck: DeckId, bpm_x100: u32) {
        self.decks[deck_index(deck)].base_bpm_x100 = if bpm_x100 == 0 { 12_000 } else { bpm_x100 };
    }

    pub fn set_position_ms(&mut self, deck: DeckId, position_ms: u32) {
        self.decks[deck_index(deck)].position_ms = position_ms;
    }

    pub fn set_controller_connected(&mut self, connected: bool) {
        for state in &mut self.decks {
            state.controller_connected = connected;
            if !connected {
                state.jog_touched = false;
                state.loop_adjust_mode = LoopAdjustMode::None;
            }
        }
    }

    pub fn handle_control(&mut self, event: ControlEvent) -> DeckEffects {
        self.handle_control_with_analysis(event, [None, None])
    }

    pub fn handle_control_with_analysis(
        &mut self,
        event: ControlEvent,
        analysis: [Option<TrackAnalysis<'_>>; 2],
    ) -> DeckEffects {
        let Some(deck) = event.deck else {
            return DeckEffects::NONE;
        };

        match event.control {
            SemanticControl::Play => self.handle_play(deck, event.value),
            SemanticControl::Cue => self.handle_cue(deck, event.value),
            SemanticControl::ToStart => self.handle_to_start(deck, event.value),
            SemanticControl::Tempo => self.handle_tempo(deck, event.value),
            SemanticControl::TempoRange => self.handle_tempo_range(deck, event.value),
            SemanticControl::Sync => self.handle_sync(deck, event.value, analysis),
            SemanticControl::Shift => {
                if let ControlValue::Pressed(pressed) = event.value {
                    self.decks[deck_index(deck)].shift_held = pressed;
                }
                DeckEffects::NONE
            }
            SemanticControl::JogTouch => {
                if let ControlValue::Pressed(pressed) = event.value {
                    self.decks[deck_index(deck)].jog_touched = pressed;
                }
                DeckEffects::NONE
            }
            SemanticControl::PadModeHotCue => {
                self.set_pad_mode_if_pressed(
                    deck,
                    event.value,
                    PadMode::HotCue,
                    Some(PerformanceMode::HotCue),
                );
                DeckEffects::NONE
            }
            SemanticControl::PadModeBeatLoop => {
                self.set_pad_mode_if_pressed(
                    deck,
                    event.value,
                    PadMode::BeatLoop,
                    Some(PerformanceMode::LoopRoll),
                );
                DeckEffects::NONE
            }
            SemanticControl::PadModeBeatJump => {
                self.set_pad_mode_if_pressed(
                    deck,
                    event.value,
                    PadMode::BeatJump,
                    Some(PerformanceMode::BeatJump),
                );
                DeckEffects::NONE
            }
            SemanticControl::PadModePadFx1 => {
                self.set_pad_mode_if_pressed(deck, event.value, PadMode::PadFx1, None);
                DeckEffects::NONE
            }
            SemanticControl::PadModePadFx2 => {
                self.set_pad_mode_if_pressed(deck, event.value, PadMode::PadFx2, None);
                DeckEffects::NONE
            }
            SemanticControl::PadModeKeyboard
            | SemanticControl::PadModeKeyShift
            | SemanticControl::PadModeSampler => DeckEffects::NONE,
            SemanticControl::DeckExtAction => {
                self.handle_deck_ext_action(deck, event.value);
                DeckEffects::NONE
            }
            _ => DeckEffects::NONE,
        }
    }

    pub fn resolve_playback_request(
        &mut self,
        deck: DeckId,
        request_id: u32,
        succeeded: bool,
    ) -> bool {
        let state = &mut self.decks[deck_index(deck)];
        let Some(pending) = state.pending_playback else {
            return false;
        };
        if pending.request_id != request_id {
            return false;
        }

        state.pending_playback = None;
        if succeeded {
            state.playing = pending.playing;
        }
        true
    }

    fn handle_play(&mut self, deck: DeckId, value: ControlValue) -> DeckEffects {
        if value != ControlValue::Pressed(true) {
            return DeckEffects::NONE;
        }

        let state = &mut self.decks[deck_index(deck)];
        state.playback_generation = state.playback_generation.wrapping_add(1);
        let request_id = state.playback_generation;
        let desired_now = state
            .pending_playback
            .map(|pending| pending.playing)
            .unwrap_or(state.playing);
        let playing = !desired_now;
        state.pending_playback = Some(PendingPlayback {
            request_id,
            playing,
        });

        DeckEffects::one(DeckEffect::PlaybackRequest {
            deck,
            playing,
            request_id,
        })
    }

    fn handle_cue(&mut self, deck: DeckId, value: ControlValue) -> DeckEffects {
        if value != ControlValue::Pressed(true) {
            return DeckEffects::NONE;
        }

        let state = &mut self.decks[deck_index(deck)];
        state.pending_playback = None;
        state.playing = false;
        state.position_ms = state.cue_point_ms;

        DeckEffects::two(
            DeckEffect::Pause { deck },
            DeckEffect::Seek {
                deck,
                position_ms: state.cue_point_ms,
            },
        )
    }

    fn handle_to_start(&mut self, deck: DeckId, value: ControlValue) -> DeckEffects {
        if value != ControlValue::Pressed(true) {
            return DeckEffects::NONE;
        }

        let state = &mut self.decks[deck_index(deck)];
        state.pending_playback = None;
        state.playing = false;
        state.position_ms = 0;
        state.cue_point_ms = 0;

        DeckEffects::two(
            DeckEffect::Pause { deck },
            DeckEffect::Seek {
                deck,
                position_ms: 0,
            },
        )
    }

    fn handle_tempo(&mut self, deck: DeckId, value: ControlValue) -> DeckEffects {
        let ControlValue::Absolute { value, max } = value else {
            return DeckEffects::NONE;
        };
        if max == 0 {
            return DeckEffects::NONE;
        }

        let raw = scale_absolute(value, max, PITCH_MAX);
        let state = &mut self.decks[deck_index(deck)];
        state.sync_enabled = false;
        state.pitch_raw = raw;
        state.pitch_centipercent = tempo_centipercent_from_raw(raw, state.tempo_range_percent);

        DeckEffects::one(DeckEffect::SetPitchCentipercent {
            deck,
            value: state.pitch_centipercent,
        })
    }

    fn handle_tempo_range(&mut self, deck: DeckId, value: ControlValue) -> DeckEffects {
        if value != ControlValue::Pressed(true) {
            return DeckEffects::NONE;
        }

        let state = &mut self.decks[deck_index(deck)];
        state.sync_enabled = false;
        state.tempo_range_percent = next_tempo_range_percent(state.tempo_range_percent);
        state.pitch_centipercent =
            tempo_centipercent_from_raw(state.pitch_raw, state.tempo_range_percent);

        DeckEffects::one(DeckEffect::SetPitchCentipercent {
            deck,
            value: state.pitch_centipercent,
        })
    }

    fn handle_sync(
        &mut self,
        deck: DeckId,
        value: ControlValue,
        analysis: [Option<TrackAnalysis<'_>>; 2],
    ) -> DeckEffects {
        if value != ControlValue::Pressed(true) {
            return DeckEffects::NONE;
        }

        let deck_idx = deck_index(deck);
        if self.decks[deck_idx].sync_enabled {
            self.decks[deck_idx].sync_enabled = false;
            return DeckEffects::NONE;
        }

        let reference = match self.sync_master {
            Some(master) if master != deck => master,
            _ => other_deck(deck),
        };
        let reference_idx = deck_index(reference);
        let target_bpm_x100 = analysis[deck_idx]
            .map(|item| item.bpm_x100())
            .filter(|bpm| *bpm > 0)
            .unwrap_or(self.decks[deck_idx].base_bpm_x100);
        let mut reference_state = self.decks[reference_idx];
        reference_state.base_bpm_x100 = analysis[reference_idx]
            .map(|item| item.bpm_x100())
            .filter(|bpm| *bpm > 0)
            .unwrap_or(reference_state.base_bpm_x100);
        let target_centipercent = centipercent_for_bpm_match(target_bpm_x100, reference_state);

        let pitch_effect = DeckEffect::SetPitchCentipercent {
            deck,
            value: target_centipercent,
        };

        let target_position_ms = self.decks[deck_idx].position_ms;
        let reference_position_ms = self.decks[reference_idx].position_ms;
        let aligned_ms = match (analysis[deck_idx], analysis[reference_idx]) {
            (Some(target_analysis), Some(reference_analysis)) => {
                if let (Some(target_grid), Some(reference_grid)) =
                    (target_analysis.beat_grid(), reference_analysis.beat_grid())
                {
                    phase_align_target_ms(
                        target_position_ms,
                        target_grid,
                        reference_position_ms,
                        reference_grid,
                    )
                } else {
                    None
                }
            }
            _ => None,
        };

        let state = &mut self.decks[deck_idx];
        state.sync_enabled = true;
        state.pitch_centipercent = target_centipercent;

        if let Some(position_ms) = aligned_ms {
            state.position_ms = position_ms;
            DeckEffects::two(pitch_effect, DeckEffect::Seek { deck, position_ms })
        } else {
            DeckEffects::one(pitch_effect)
        }
    }

    fn set_pad_mode_if_pressed(
        &mut self,
        deck: DeckId,
        value: ControlValue,
        pad_mode: PadMode,
        perf_mode: Option<PerformanceMode>,
    ) {
        if value != ControlValue::Pressed(true) {
            return;
        }
        let state = &mut self.decks[deck_index(deck)];
        state.pad_mode = pad_mode;
        if let Some(perf_mode) = perf_mode {
            state.perf_mode = perf_mode;
        }
    }

    fn handle_deck_ext_action(&mut self, deck: DeckId, value: ControlValue) {
        let ControlValue::DeckExtAction(action) = value else {
            return;
        };

        match action.action {
            DeckExtAction::SyncMaster if action.pressed => {
                self.sync_master = Some(deck);
                for candidate in [DeckId::One, DeckId::Two] {
                    self.decks[deck_index(candidate)].sync_master = candidate == deck;
                }
                self.decks[deck_index(deck)].sync_enabled = false;
            }
            DeckExtAction::Quantize if action.pressed => {
                let state = &mut self.decks[deck_index(deck)];
                state.quantize_enabled = !state.quantize_enabled;
            }
            DeckExtAction::SyncOff if action.pressed => {
                self.decks[deck_index(deck)].sync_enabled = false;
            }
            DeckExtAction::Censor
            | DeckExtAction::ReloopStop
            | DeckExtAction::LoopAdjustIn
            | DeckExtAction::LoopAdjustOut => {
                // These actions depend on qualified audio/loop state and are
                // intentionally left for the next reducer slice rather than
                // approximated here.
            }
            _ => {}
        }
    }
}

pub const fn tempo_centipercent_from_raw(raw: u16, range_percent: u16) -> i16 {
    let raw = if raw > PITCH_MAX { PITCH_MAX } else { raw } as i32;
    let centi_range = range_percent as i32 * 100;
    ((PITCH_CENTER as i32 - raw) * centi_range / PITCH_CENTER as i32) as i16
}

pub const fn next_tempo_range_percent(current: u16) -> u16 {
    match current {
        6 => 10,
        10 => 16,
        _ => 6,
    }
}

fn scale_absolute(value: u16, max: u16, target_max: u16) -> u16 {
    if max == target_max {
        return value.min(target_max);
    }
    let scaled = (value as u32 * target_max as u32 + max as u32 / 2) / max as u32;
    scaled.min(target_max as u32) as u16
}

fn centipercent_for_bpm_match(target_base_x100: u32, reference: DeckState) -> i16 {
    let target_base_x100 = if target_base_x100 == 0 {
        12_000
    } else {
        target_base_x100
    };
    let reference_base_x100 = if reference.base_bpm_x100 == 0 {
        12_000
    } else {
        reference.base_bpm_x100
    };
    let reference_factor = 10_000i64 + reference.pitch_centipercent as i64;
    let numerator = reference_base_x100 as i64 * reference_factor;
    let ratio_x10_000 = div_round_nearest_positive(numerator, target_base_x100 as i64);
    let centipercent = ratio_x10_000 - 10_000;
    centipercent.clamp(
        -(BEAT_SYNC_MAX_PERCENT as i64) * 100,
        BEAT_SYNC_MAX_PERCENT as i64 * 100,
    ) as i16
}

fn div_round_nearest_positive(numerator: i64, denominator: i64) -> i64 {
    (numerator + denominator / 2) / denominator
}

const fn deck_index(deck: DeckId) -> usize {
    match deck {
        DeckId::One => 0,
        DeckId::Two => 1,
    }
}

const fn other_deck(deck: DeckId) -> DeckId {
    match deck {
        DeckId::One => DeckId::Two,
        DeckId::Two => DeckId::One,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use pajoniiir_controller_core::{DeckExtActionValue, SemanticControl};

    fn pressed(deck: DeckId, control: SemanticControl, value: bool) -> ControlEvent {
        ControlEvent {
            deck: Some(deck),
            control,
            value: ControlValue::Pressed(value),
        }
    }

    fn absolute(deck: DeckId, control: SemanticControl, value: u16) -> ControlEvent {
        ControlEvent {
            deck: Some(deck),
            control,
            value: ControlValue::Absolute {
                value,
                max: PITCH_MAX,
            },
        }
    }

    fn ext(deck: DeckId, action: DeckExtAction, pressed: bool) -> ControlEvent {
        ControlEvent {
            deck: Some(deck),
            control: SemanticControl::DeckExtAction,
            value: ControlValue::DeckExtAction(DeckExtActionValue { action, pressed }),
        }
    }

    fn playback_request(effects: DeckEffects) -> (DeckId, bool, u32) {
        match effects.items[0].unwrap() {
            DeckEffect::PlaybackRequest {
                deck,
                playing,
                request_id,
            } => (deck, playing, request_id),
            other => panic!("expected playback request, got {other:?}"),
        }
    }

    #[test]
    fn released_defaults_are_preserved() {
        let state = DeckProductState::new();
        for deck in [DeckId::One, DeckId::Two] {
            assert_eq!(state.deck(deck).tempo_range_percent, 10);
            assert_eq!(state.deck(deck).pitch_raw, PITCH_CENTER);
            assert_eq!(state.deck(deck).pitch_centipercent, 0);
            assert_eq!(state.deck(deck).pad_mode, PadMode::HotCue);
        }
    }

    #[test]
    fn decks_track_transport_independently() {
        let mut state = DeckProductState::new();

        let (_, target, request) = playback_request(state.handle_control(pressed(
            DeckId::One,
            SemanticControl::Play,
            true,
        )));
        assert!(target);
        assert!(state.resolve_playback_request(DeckId::One, request, true));
        assert!(state.deck(DeckId::One).playing);
        assert!(!state.deck(DeckId::Two).playing);

        let (_, target, request) = playback_request(state.handle_control(pressed(
            DeckId::Two,
            SemanticControl::Play,
            true,
        )));
        assert!(target);
        assert!(state.resolve_playback_request(DeckId::Two, request, true));
        assert!(state.deck(DeckId::One).playing);
        assert!(state.deck(DeckId::Two).playing);

        state.handle_control(pressed(DeckId::Two, SemanticControl::Cue, true));
        assert!(state.deck(DeckId::One).playing);
        assert!(!state.deck(DeckId::Two).playing);
    }

    #[test]
    fn failed_playback_request_does_not_mark_deck_playing() {
        let mut state = DeckProductState::new();
        let (_, _, request) = playback_request(state.handle_control(pressed(
            DeckId::Two,
            SemanticControl::Play,
            true,
        )));

        assert!(state.resolve_playback_request(DeckId::Two, request, false));
        assert!(!state.deck(DeckId::Two).playing);
    }

    #[test]
    fn stale_playback_completion_cannot_overwrite_newer_request() {
        let mut state = DeckProductState::new();
        let (_, _, first) = playback_request(state.handle_control(pressed(
            DeckId::One,
            SemanticControl::Play,
            true,
        )));
        let (_, second_target, second) = playback_request(state.handle_control(pressed(
            DeckId::One,
            SemanticControl::Play,
            true,
        )));

        assert!(!second_target);
        assert!(!state.resolve_playback_request(DeckId::One, first, true));
        assert!(!state.deck(DeckId::One).playing);
        assert!(state.resolve_playback_request(DeckId::One, second, true));
        assert!(!state.deck(DeckId::One).playing);
    }

    #[test]
    fn decks_track_pitch_independently() {
        let mut state = DeckProductState::new();

        state.handle_control(absolute(DeckId::One, SemanticControl::Tempo, 7000));
        state.handle_control(absolute(DeckId::Two, SemanticControl::Tempo, 9600));

        assert_eq!(state.deck(DeckId::One).pitch_raw, 7000);
        assert_eq!(state.deck(DeckId::Two).pitch_raw, 9600);
    }

    #[test]
    fn tempo_range_cycles_requested_deck_only() {
        let mut state = DeckProductState::new();
        let d1 = pressed(DeckId::One, SemanticControl::TempoRange, true);
        let d2 = pressed(DeckId::Two, SemanticControl::TempoRange, true);

        state.handle_control(d1);
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 16);
        assert_eq!(state.deck(DeckId::Two).tempo_range_percent, 10);

        state.handle_control(d1);
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 6);
        state.handle_control(d1);
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 10);

        state.handle_control(d2);
        assert_eq!(state.deck(DeckId::Two).tempo_range_percent, 16);
    }

    #[test]
    fn tempo_range_release_does_not_cycle() {
        let mut state = DeckProductState::new();
        state.handle_control(pressed(DeckId::One, SemanticControl::TempoRange, false));
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 10);
    }

    #[test]
    fn pitch_mapping_matches_released_integer_contract() {
        let mut state = DeckProductState::new();

        state.handle_control(absolute(DeckId::One, SemanticControl::Tempo, 0));
        state.handle_control(absolute(DeckId::Two, SemanticControl::Tempo, PITCH_MAX));

        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 1000);
        assert_eq!(state.deck(DeckId::Two).pitch_centipercent, -999);

        state.handle_control(pressed(DeckId::One, SemanticControl::TempoRange, true));
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 16);
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 1600);
    }

    #[test]
    fn tempo_range_change_reapplies_current_pitch() {
        let mut state = DeckProductState::new();

        state.handle_control(absolute(DeckId::One, SemanticControl::Tempo, 4096));
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 500);

        let effects = state.handle_control(pressed(DeckId::One, SemanticControl::TempoRange, true));
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 800);
        assert_eq!(
            effects.items[0],
            Some(DeckEffect::SetPitchCentipercent {
                deck: DeckId::One,
                value: 800,
            })
        );
    }

    #[test]
    fn sync_toggles_requested_deck_only() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 12_000);
        state.set_base_bpm_x100(DeckId::Two, 12_000);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert!(state.deck(DeckId::One).sync_enabled);
        assert!(!state.deck(DeckId::Two).sync_enabled);

        state.handle_control(pressed(DeckId::Two, SemanticControl::Sync, true));
        assert!(state.deck(DeckId::One).sync_enabled);
        assert!(state.deck(DeckId::Two).sync_enabled);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert!(!state.deck(DeckId::One).sync_enabled);
        assert!(state.deck(DeckId::Two).sync_enabled);
    }

    #[test]
    fn sync_master_marks_requested_deck_as_reference() {
        let mut state = DeckProductState::new();
        state.handle_control(ext(DeckId::One, DeckExtAction::SyncMaster, true));

        assert!(state.deck(DeckId::One).sync_master);
        assert!(!state.deck(DeckId::Two).sync_master);
        assert!(!state.deck(DeckId::One).sync_enabled);
    }

    #[test]
    fn sync_matches_other_deck_bpm_and_can_exceed_selected_range() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 12_000);
        state.set_base_bpm_x100(DeckId::Two, 12_800);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 667);

        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 10_000);
        state.set_base_bpm_x100(DeckId::Two, 11_700);
        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert_eq!(state.deck(DeckId::One).tempo_range_percent, 10);
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 1700);
    }

    #[test]
    fn sync_clamps_to_twenty_percent_safe_limit() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 10_000);
        state.set_base_bpm_x100(DeckId::Two, 13_000);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 2000);
    }

    #[test]
    fn sync_phase_aligns_with_provider_neutral_beatgrids() {
        use pajoniiir_track_analysis::{AnalysisProvider, Beat, BeatGrid};

        let target_beats = [
            Beat {
                time_ms: 1000,
                phase: 0,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 1500,
                phase: 1,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 2000,
                phase: 2,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 2500,
                phase: 3,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 3000,
                phase: 0,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 3500,
                phase: 1,
                bpm_x100: 12_000,
            },
        ];
        let reference_beats = [
            Beat {
                time_ms: 8000,
                phase: 0,
                bpm_x100: 12_800,
            },
            Beat {
                time_ms: 8469,
                phase: 1,
                bpm_x100: 12_800,
            },
            Beat {
                time_ms: 8938,
                phase: 2,
                bpm_x100: 12_800,
            },
            Beat {
                time_ms: 9407,
                phase: 3,
                bpm_x100: 12_800,
            },
        ];

        let target = TrackAnalysis::new(
            AnalysisProvider::RekordboxImport,
            1,
            12_000,
            Some(BeatGrid::new(&target_beats)),
        );
        let reference = TrackAnalysis::new(
            AnalysisProvider::AptaNative,
            4,
            12_800,
            Some(BeatGrid::new(&reference_beats)),
        );

        let mut state = DeckProductState::new();
        state.set_position_ms(DeckId::One, 2600);
        state.set_position_ms(DeckId::Two, 8900);

        let effects = state.handle_control_with_analysis(
            pressed(DeckId::One, SemanticControl::Sync, true),
            [Some(target), Some(reference)],
        );

        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 667);
        assert_eq!(state.deck(DeckId::One).position_ms, 1962);
        assert_eq!(
            effects,
            DeckEffects::two(
                DeckEffect::SetPitchCentipercent {
                    deck: DeckId::One,
                    value: 667,
                },
                DeckEffect::Seek {
                    deck: DeckId::One,
                    position_ms: 1962,
                },
            )
        );
    }

    #[test]
    fn sync_without_both_beatgrids_keeps_phase_position_unchanged() {
        use pajoniiir_track_analysis::{AnalysisProvider, Beat, BeatGrid};

        let target_beats = [Beat {
            time_ms: 1000,
            phase: 0,
            bpm_x100: 12_000,
        }];
        let target = TrackAnalysis::new(
            AnalysisProvider::RekordboxImport,
            1,
            12_000,
            Some(BeatGrid::new(&target_beats)),
        );
        let reference = TrackAnalysis::new(AnalysisProvider::AptaCache, 2, 12_800, None);

        let mut state = DeckProductState::new();
        state.set_position_ms(DeckId::One, 2600);
        state.set_position_ms(DeckId::Two, 8900);

        let effects = state.handle_control_with_analysis(
            pressed(DeckId::One, SemanticControl::Sync, true),
            [Some(target), Some(reference)],
        );

        assert_eq!(state.deck(DeckId::One).position_ms, 2600);
        assert_eq!(
            effects.items[0],
            Some(DeckEffect::SetPitchCentipercent {
                deck: DeckId::One,
                value: 667,
            })
        );
        assert_eq!(effects.items[1], None);
    }

    #[test]
    fn sync_uses_other_decks_effective_bpm() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 12_000);
        state.set_base_bpm_x100(DeckId::Two, 10_000);
        state.handle_control(absolute(DeckId::Two, SemanticControl::Tempo, 0));
        assert_eq!(state.deck(DeckId::Two).pitch_centipercent, 1000);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, -833);
    }

    #[test]
    fn selected_sync_master_is_used_as_reference() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 10_000);
        state.set_base_bpm_x100(DeckId::Two, 12_500);
        state.handle_control(ext(DeckId::One, DeckExtAction::SyncMaster, true));

        state.handle_control(pressed(DeckId::Two, SemanticControl::Sync, true));
        assert!(state.deck(DeckId::Two).sync_enabled);
        assert_eq!(state.deck(DeckId::Two).pitch_centipercent, -2000);
    }

    #[test]
    fn sync_toggle_off_does_not_reapply_pitch() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 12_000);
        state.set_base_bpm_x100(DeckId::Two, 12_800);

        let first = state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert!(first.items[0].is_some());
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 667);

        let second = state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert_eq!(second, DeckEffects::NONE);
        assert!(!state.deck(DeckId::One).sync_enabled);
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 667);
    }

    #[test]
    fn manual_pitch_disables_sync_state() {
        let mut state = DeckProductState::new();
        state.set_base_bpm_x100(DeckId::One, 12_000);
        state.set_base_bpm_x100(DeckId::Two, 12_800);

        state.handle_control(pressed(DeckId::One, SemanticControl::Sync, true));
        assert!(state.deck(DeckId::One).sync_enabled);

        state.handle_control(absolute(DeckId::One, SemanticControl::Tempo, PITCH_CENTER));
        assert!(!state.deck(DeckId::One).sync_enabled);
        assert_eq!(state.deck(DeckId::One).pitch_centipercent, 0);
    }

    #[test]
    fn pad_mode_behavior_matches_released_scope() {
        let mut state = DeckProductState::new();

        state.handle_control(pressed(DeckId::One, SemanticControl::PadModeBeatLoop, true));
        state.handle_control(pressed(DeckId::Two, SemanticControl::PadModeBeatJump, true));
        assert_eq!(state.deck(DeckId::One).perf_mode, PerformanceMode::LoopRoll);
        assert_eq!(state.deck(DeckId::Two).perf_mode, PerformanceMode::BeatJump);
        assert_eq!(state.deck(DeckId::One).pad_mode, PadMode::BeatLoop);
        assert_eq!(state.deck(DeckId::Two).pad_mode, PadMode::BeatJump);

        state.handle_control(pressed(DeckId::One, SemanticControl::PadModePadFx1, true));
        state.handle_control(pressed(DeckId::Two, SemanticControl::PadModeSampler, true));
        state.handle_control(pressed(DeckId::One, SemanticControl::PadModeKeyboard, true));
        state.handle_control(pressed(DeckId::Two, SemanticControl::PadModeKeyShift, true));

        assert_eq!(state.deck(DeckId::One).pad_mode, PadMode::PadFx1);
        assert_eq!(state.deck(DeckId::One).perf_mode, PerformanceMode::LoopRoll);
        assert_eq!(state.deck(DeckId::Two).pad_mode, PadMode::BeatJump);
        assert_eq!(state.deck(DeckId::Two).perf_mode, PerformanceMode::BeatJump);
    }

    #[test]
    fn disconnect_clears_physical_hold_state_without_stopping_playback() {
        let mut state = DeckProductState::new();
        state.decks[0].playing = true;
        state.decks[0].jog_touched = true;
        state.decks[0].loop_adjust_mode = LoopAdjustMode::In;

        state.set_controller_connected(false);

        assert!(state.deck(DeckId::One).playing);
        assert!(!state.deck(DeckId::One).jog_touched);
        assert_eq!(
            state.deck(DeckId::One).loop_adjust_mode,
            LoopAdjustMode::None
        );
        assert!(!state.deck(DeckId::One).controller_connected);
        assert!(!state.deck(DeckId::Two).controller_connected);
    }
}
