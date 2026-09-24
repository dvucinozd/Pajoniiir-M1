#![no_std]
#![forbid(unsafe_code)]

pub const MIXER_CONTROL_MAX: u16 = 16_383;
pub const MIXER_CONTROL_CENTER: u16 = 8_192;
pub const EQ_RAW_MIN: u16 = 0;
pub const EQ_RAW_CENTER: u16 = MIXER_CONTROL_CENTER;
pub const EQ_RAW_MAX: u16 = MIXER_CONTROL_MAX;

const EQ_LOW_CUTOFF_HZ: f32 = 800.0;
const EQ_HIGH_CUTOFF_HZ: f32 = 4_000.0;
const EQ_GAIN_BLOCK: u32 = 32;

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct PcmFrame {
    pub left: i16,
    pub right: i16,
}

#[derive(Clone, Copy, Debug, Default, PartialEq)]
pub struct DspFrame {
    pub left: f32,
    pub right: f32,
}

impl From<PcmFrame> for DspFrame {
    fn from(frame: PcmFrame) -> Self {
        Self {
            left: frame.left as f32,
            right: frame.right as f32,
        }
    }
}

impl From<DspFrame> for PcmFrame {
    fn from(frame: DspFrame) -> Self {
        Self {
            left: pcm_sample_from_float(frame.left),
            right: pcm_sample_from_float(frame.right),
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum EqBand {
    Low,
    Mid,
    High,
}

impl EqBand {
    const fn index(self) -> usize {
        match self {
            Self::Low => 0,
            Self::Mid => 1,
            Self::High => 2,
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct EqState {
    low_lp: [f32; 2],
    low_lp2: [f32; 2],
    high_lp: [f32; 2],
    high_lp2: [f32; 2],
    low_alpha: f32,
    high_alpha: f32,
    raw: [u16; 3],
    applied_raw: [u16; 3],
    gain: [f32; 3],
    gain_frames_left: u32,
}

impl EqState {
    pub fn new(sample_rate_hz: u32) -> Self {
        let mut state = Self {
            low_lp: [0.0; 2],
            low_lp2: [0.0; 2],
            high_lp: [0.0; 2],
            high_lp2: [0.0; 2],
            low_alpha: 0.0,
            high_alpha: 0.0,
            raw: [EQ_RAW_CENTER; 3],
            applied_raw: [EQ_RAW_CENTER; 3],
            gain: [1.0; 3],
            gain_frames_left: 0,
        };
        state.set_sample_rate(sample_rate_hz);
        state
    }

    pub fn set_sample_rate(&mut self, sample_rate_hz: u32) {
        self.low_alpha = one_pole_alpha(EQ_LOW_CUTOFF_HZ, sample_rate_hz);
        self.high_alpha = one_pole_alpha(EQ_HIGH_CUTOFF_HZ, sample_rate_hz);
    }

    pub fn reset_filters(&mut self) {
        self.low_lp = [0.0; 2];
        self.low_lp2 = [0.0; 2];
        self.high_lp = [0.0; 2];
        self.high_lp2 = [0.0; 2];
    }

    pub fn set_raw(&mut self, low: u16, mid: u16, high: u16) {
        self.set_band_raw(EqBand::Low, low);
        self.set_band_raw(EqBand::Mid, mid);
        self.set_band_raw(EqBand::High, high);
    }

    pub fn set_band_raw(&mut self, band: EqBand, raw: u16) {
        self.raw[band.index()] = raw.min(EQ_RAW_MAX);
    }

    pub fn band_raw(&self, band: EqBand) -> u16 {
        self.raw[band.index()]
    }

    pub fn process_frame(&mut self, input: DspFrame) -> DspFrame {
        if self.gain_frames_left == 0 {
            self.refresh_gains();
            self.gain_frames_left = EQ_GAIN_BLOCK;
        }
        self.gain_frames_left -= 1;

        DspFrame {
            left: self.process_sample(input.left, 0),
            right: self.process_sample(input.right, 1),
        }
    }

    pub fn process_pcm_frame(&mut self, input: PcmFrame) -> PcmFrame {
        self.process_frame(input.into()).into()
    }

    fn refresh_gains(&mut self) {
        for band in [EqBand::Low, EqBand::Mid, EqBand::High] {
            let index = band.index();
            let raw = self.raw[index];
            if raw != self.applied_raw[index] {
                self.applied_raw[index] = raw;
                self.gain[index] = eq_raw_to_gain(raw);
            }
        }
    }

    fn process_sample(&mut self, sample: f32, channel: usize) -> f32 {
        self.low_lp[channel] += self.low_alpha * (sample - self.low_lp[channel]);
        self.low_lp2[channel] += self.low_alpha * (self.low_lp[channel] - self.low_lp2[channel]);
        self.high_lp[channel] += self.high_alpha * (sample - self.high_lp[channel]);
        self.high_lp2[channel] +=
            self.high_alpha * (self.high_lp[channel] - self.high_lp2[channel]);

        let low = self.low_lp2[channel];
        let high = sample - self.high_lp2[channel];
        let mid = sample - low - high;

        (low * self.gain[EqBand::Low.index()])
            + (mid * self.gain[EqBand::Mid.index()])
            + (high * self.gain[EqBand::High.index()])
    }
}

pub const FILTER_RAW_MIN: u16 = 0;
pub const FILTER_RAW_CENTER: u16 = MIXER_CONTROL_CENTER;
pub const FILTER_RAW_MAX: u16 = MIXER_CONTROL_MAX;

const FILTER_LP_MAX_HZ: f32 = 18_000.0;
const FILTER_HP_MIN_HZ: f32 = 20.0;
const FILTER_RES_K: f32 = 0.8;
const FILTER_CENTER_DEAD_RAW: u16 = 96;
const FILTER_SMOOTH_BLOCK: u32 = 32;
const FILTER_SMOOTH_COEF: f32 = 0.2;
const FILTER_SMOOTH_SNAP_RAW: f32 = 0.5;
const FILTER_LP_LOG_RATIO: f32 = -5.703_782_6;
const FILTER_HP_LOG_RATIO: f32 = 5.991_464_6;

#[derive(Clone, Copy, Debug, PartialEq)]
pub struct FilterState {
    raw: u16,
    sample_rate_hz: u32,
    smoothed_raw: f32,
    block_frames_left: u32,
    coefficients_dirty: bool,
    bypassed: bool,
    hp_mode: bool,
    k: f32,
    a1: f32,
    a2: f32,
    a3: f32,
    ic1eq: [f32; 2],
    ic2eq: [f32; 2],
}

impl FilterState {
    pub fn new(sample_rate_hz: u32) -> Self {
        let mut state = Self {
            raw: FILTER_RAW_CENTER,
            sample_rate_hz: 44_100,
            smoothed_raw: FILTER_RAW_CENTER as f32,
            block_frames_left: 0,
            coefficients_dirty: true,
            bypassed: true,
            hp_mode: false,
            k: FILTER_RES_K,
            a1: 0.0,
            a2: 0.0,
            a3: 0.0,
            ic1eq: [0.0; 2],
            ic2eq: [0.0; 2],
        };
        state.set_sample_rate(sample_rate_hz);
        state.reset();
        state
    }

    pub fn reset(&mut self) {
        self.ic1eq = [0.0; 2];
        self.ic2eq = [0.0; 2];
        self.smoothed_raw = self.raw as f32;
        self.block_frames_left = 0;
        self.coefficients_dirty = true;
        self.bypassed = true;
    }

    pub fn set_sample_rate(&mut self, sample_rate_hz: u32) {
        let next = if sample_rate_hz == 0 {
            44_100
        } else {
            sample_rate_hz
        };
        if next != self.sample_rate_hz {
            self.sample_rate_hz = next;
            self.coefficients_dirty = true;
            self.block_frames_left = 0;
        }
    }

    pub fn set_raw(&mut self, raw: u16) {
        self.raw = raw.min(FILTER_RAW_MAX);
    }

    pub const fn raw(&self) -> u16 {
        self.raw
    }

    pub fn process_frame(&mut self, enabled: bool, input: DspFrame) -> DspFrame {
        if !enabled {
            return input;
        }

        if self.block_frames_left == 0 {
            self.block_frames_left = FILTER_SMOOTH_BLOCK;
            self.update_coefficients();
        }
        self.block_frames_left -= 1;

        if self.bypassed {
            return input;
        }

        DspFrame {
            left: self.svf_process(input.left, 0),
            right: self.svf_process(input.right, 1),
        }
    }

    pub fn process_pcm_frame(&mut self, enabled: bool, input: PcmFrame) -> PcmFrame {
        self.process_frame(enabled, input.into()).into()
    }

    fn update_coefficients(&mut self) {
        let target_raw = self.raw;
        let target = target_raw as f32;
        let movement = target - self.smoothed_raw;
        let mut position_changed = false;

        if movement.abs() <= FILTER_SMOOTH_SNAP_RAW {
            if self.smoothed_raw != target {
                self.smoothed_raw = target;
                position_changed = true;
            }
        } else {
            self.smoothed_raw += movement * FILTER_SMOOTH_COEF;
            position_changed = true;
        }

        let delta = self.smoothed_raw - FILTER_RAW_CENTER as f32;
        let mag = delta.abs();
        let raw_dist = target_raw.abs_diff(FILTER_RAW_CENTER);
        if raw_dist <= FILTER_CENTER_DEAD_RAW && mag <= FILTER_CENTER_DEAD_RAW as f32 {
            self.bypassed = true;
            return;
        }

        let was_bypassed = self.bypassed;
        let next_hp_mode = delta >= 0.0;
        self.bypassed = false;

        if !position_changed
            && !self.coefficients_dirty
            && !was_bypassed
            && self.hp_mode == next_hp_mode
        {
            return;
        }

        let intensity = (mag / FILTER_RAW_CENTER as f32).min(1.0);
        let cutoff = if delta < 0.0 {
            self.hp_mode = false;
            FILTER_LP_MAX_HZ * libm::expf(FILTER_LP_LOG_RATIO * intensity)
        } else {
            self.hp_mode = true;
            FILTER_HP_MIN_HZ * libm::expf(FILTER_HP_LOG_RATIO * intensity)
        };

        let fs = self.sample_rate_hz as f32;
        let cutoff = cutoff.min(0.45 * fs);
        let g = libm::tanf(core::f32::consts::PI * cutoff / fs);

        self.k = FILTER_RES_K;
        self.a1 = 1.0 / (1.0 + g * (g + self.k));
        self.a2 = g * self.a1;
        self.a3 = g * self.a2;
        self.coefficients_dirty = false;
    }

    fn svf_process(&mut self, sample: f32, channel: usize) -> f32 {
        let v3 = sample - self.ic2eq[channel];
        let v1 = self.a1 * self.ic1eq[channel] + self.a2 * v3;
        let v2 = self.ic2eq[channel] + self.a2 * self.ic1eq[channel] + self.a3 * v3;

        self.ic1eq[channel] = 2.0 * v1 - self.ic1eq[channel];
        self.ic2eq[channel] = 2.0 * v2 - self.ic2eq[channel];

        if self.hp_mode {
            sample - self.k * v1 - v2
        } else {
            v2
        }
    }
}


pub fn smart_cfx_curve_raw(raw: u16) -> u16 {
    let raw = raw.min(FILTER_RAW_MAX);
    if raw == FILTER_RAW_CENTER || raw == FILTER_RAW_MIN || raw == FILTER_RAW_MAX {
        return raw;
    }

    let delta = raw as i32 - FILTER_RAW_CENTER as i32;
    let sign = if delta < 0 { -1 } else { 1 };
    let mag = delta.unsigned_abs().min(FILTER_RAW_CENTER as u32);
    let max = FILTER_RAW_CENTER as u32;

    let numerator = mag as u64 * mag as u64 * (3 * max - 2 * mag) as u64;
    let denominator = max as u64 * max as u64;
    let mut curved = ((numerator + denominator / 2) / denominator) as u32;

    let min_audible = max / 24;
    if mag > min_audible && curved < min_audible {
        curved = min_audible;
    }

    let out = FILTER_RAW_CENTER as i32 + sign * curved as i32;
    out.clamp(FILTER_RAW_MIN as i32, FILTER_RAW_MAX as i32) as u16
}

pub fn eq_raw_to_gain(raw: u16) -> f32 {
    let raw = raw.min(EQ_RAW_MAX);
    if raw <= EQ_RAW_CENTER {
        raw as f32 / EQ_RAW_CENTER as f32
    } else {
        1.0 + (raw - EQ_RAW_CENTER) as f32 / (EQ_RAW_MAX - EQ_RAW_CENTER) as f32
    }
}

pub fn pcm_sample_from_float(sample: f32) -> i16 {
    if sample.is_nan() {
        0
    } else if sample > i16::MAX as f32 {
        i16::MAX
    } else if sample < i16::MIN as f32 {
        i16::MIN
    } else if sample >= 0.0 {
        (sample + 0.5) as i16
    } else {
        (sample - 0.5) as i16
    }
}

fn one_pole_alpha(cutoff_hz: f32, sample_rate_hz: u32) -> f32 {
    let sample_rate_hz = if sample_rate_hz == 0 {
        44_100
    } else {
        sample_rate_hz
    };
    let omega = 2.0 * core::f32::consts::PI * cutoff_hz;
    omega / (omega + sample_rate_hz as f32)
}

#[cfg(test)]
mod tests {
    use super::*;
    use core::f32::consts::PI;

    const SAMPLE_RATE: u32 = 44_100;
    const TEST_FRAMES: u32 = 44_100;

    fn rms_of_sine_after_eq(freq_hz: f32, low: u16, mid: u16, high: u16) -> f32 {
        let mut eq = EqState::new(SAMPLE_RATE);
        eq.set_raw(low, mid, high);

        let mut sum_sq = 0.0f64;
        for i in 0..TEST_FRAMES {
            let phase = 2.0 * PI * freq_hz * i as f32 / SAMPLE_RATE as f32;
            let sample = (phase.sin() * 12_000.0) as i16;
            let out = eq.process_pcm_frame(PcmFrame {
                left: sample,
                right: sample,
            });
            let normalized = out.left as f32 / 32_768.0;
            sum_sq += (normalized as f64) * (normalized as f64);
        }

        (sum_sq / TEST_FRAMES as f64).sqrt() as f32
    }

    fn peak_of_sine_after_wide_eq(freq_hz: f32, band: EqBand) -> f32 {
        let mut eq = EqState::new(SAMPLE_RATE);
        eq.set_band_raw(band, EQ_RAW_MAX);

        let mut peak = 0.0f32;
        for i in 0..TEST_FRAMES {
            let phase = 2.0 * PI * freq_hz * i as f32 / SAMPLE_RATE as f32;
            let sample = phase.sin() * 25_000.0;
            let out = eq.process_frame(DspFrame {
                left: sample,
                right: sample,
            });
            assert!(out.left.is_finite());
            peak = peak.max(out.left.abs());
        }
        peak
    }

    fn rms_after_filter(freq_hz: f32, raw: u16, enabled: bool) -> f32 {
        let mut filter = FilterState::new(SAMPLE_RATE);
        filter.set_raw(raw);

        let mut sum_sq = 0.0f64;
        for i in 0..TEST_FRAMES {
            let phase = 2.0 * PI * freq_hz * i as f32 / SAMPLE_RATE as f32;
            let sample = (libm::sinf(phase) * 12_000.0) as i16;
            let out = filter.process_pcm_frame(
                enabled,
                PcmFrame {
                    left: sample,
                    right: sample,
                },
            );
            let normalized = out.left as f32 / 32_768.0;
            sum_sq += (normalized as f64) * (normalized as f64);
        }

        libm::sqrt(sum_sq / TEST_FRAMES as f64) as f32
    }

    fn settle_filter(filter: &mut FilterState, raw: u16) {
        filter.set_raw(raw);
        for _ in 0..SAMPLE_RATE {
            filter.process_frame(true, DspFrame::default());
        }
    }

    fn programmed_cutoff_hz(filter: &FilterState) -> f32 {
        let g = filter.a2 / filter.a1;
        libm::atanf(g) * SAMPLE_RATE as f32 / PI
    }

    #[test]
    fn disabled_filter_is_bypass_even_at_extreme_raw() {
        let dry = rms_after_filter(8_000.0, FILTER_RAW_CENTER, false);
        let disabled = rms_after_filter(8_000.0, FILTER_RAW_MIN, false);
        assert!(disabled > dry * 0.98);
        assert!(disabled < dry * 1.02);
    }

    #[test]
    fn center_filter_is_bypass_when_enabled() {
        let dry = rms_after_filter(1_000.0, FILTER_RAW_CENTER, false);
        let center = rms_after_filter(1_000.0, FILTER_RAW_CENTER, true);
        assert!(center > dry * 0.98);
        assert!(center < dry * 1.02);
    }

    #[test]
    fn half_low_pass_keeps_bass_and_kills_treble() {
        let half_lp = FILTER_RAW_CENTER / 2;
        let bass = rms_after_filter(100.0, half_lp, true);
        let normal_bass = rms_after_filter(100.0, FILTER_RAW_CENTER, true);
        let treble = rms_after_filter(8_000.0, half_lp, true);
        let normal_treble = rms_after_filter(8_000.0, FILTER_RAW_CENTER, true);

        assert!(bass > normal_bass * 0.85);
        assert!(treble < normal_treble * 0.15);
    }

    #[test]
    fn full_low_pass_kills_mids_and_most_bass() {
        let mids = rms_after_filter(1_000.0, FILTER_RAW_MIN, true);
        let normal_mids = rms_after_filter(1_000.0, FILTER_RAW_CENTER, true);
        let bass = rms_after_filter(100.0, FILTER_RAW_MIN, true);
        let normal_bass = rms_after_filter(100.0, FILTER_RAW_CENTER, true);

        assert!(mids < normal_mids * 0.10);
        assert!(bass < normal_bass * 0.75);
    }

    #[test]
    fn low_pass_treble_cut_deepens_monotonically() {
        let normal = rms_after_filter(8_000.0, FILTER_RAW_CENTER, true);
        let quarter = rms_after_filter(8_000.0, FILTER_RAW_CENTER - FILTER_RAW_CENTER / 4, true);
        let half = rms_after_filter(8_000.0, FILTER_RAW_CENTER / 2, true);
        let full = rms_after_filter(8_000.0, FILTER_RAW_MIN, true);

        assert!(quarter < normal * 0.75);
        assert!(half < quarter * 0.5);
        assert!(full < half * 0.5);
    }

    #[test]
    fn half_high_pass_kills_bass_and_keeps_treble() {
        let half_hp = FILTER_RAW_CENTER + (FILTER_RAW_MAX - FILTER_RAW_CENTER) / 2;
        let bass = rms_after_filter(100.0, half_hp, true);
        let normal_bass = rms_after_filter(100.0, FILTER_RAW_CENTER, true);
        let treble = rms_after_filter(8_000.0, half_hp, true);
        let normal_treble = rms_after_filter(8_000.0, FILTER_RAW_CENTER, true);

        assert!(bass < normal_bass * 0.20);
        assert!(treble > normal_treble * 0.85);
    }

    #[test]
    fn full_high_pass_kills_mids_and_keeps_some_treble() {
        let mids = rms_after_filter(1_000.0, FILTER_RAW_MAX, true);
        let normal_mids = rms_after_filter(1_000.0, FILTER_RAW_CENTER, true);
        let treble = rms_after_filter(8_000.0, FILTER_RAW_MAX, true);
        let normal_treble = rms_after_filter(8_000.0, FILTER_RAW_CENTER, true);

        assert!(mids < normal_mids * 0.15);
        assert!(treble > normal_treble * 0.70);
    }

    #[test]
    fn resonant_bump_lifts_tone_at_cutoff() {
        let raw = FILTER_RAW_CENTER - (0.142 * FILTER_RAW_CENTER as f32) as u16;
        let at_cutoff = rms_after_filter(8_000.0, raw, true);
        let dry = rms_after_filter(8_000.0, FILTER_RAW_CENTER, true);

        assert!(at_cutoff > dry * 1.05);
        assert!(at_cutoff < dry * 1.60);
    }

    #[test]
    fn knob_sweep_follows_released_exponential_curve() {
        for intensity in [0.25f32, 0.5, 0.75, 1.0] {
            let travel = (intensity * FILTER_RAW_CENTER as f32) as u16;

            let mut lp = FilterState::new(SAMPLE_RATE);
            settle_filter(&mut lp, FILTER_RAW_CENTER - travel);
            assert!(!lp.hp_mode);
            let lp_expected = FILTER_LP_MAX_HZ * libm::powf(60.0 / FILTER_LP_MAX_HZ, intensity);
            let lp_actual = programmed_cutoff_hz(&lp);
            assert!(libm::fabsf(lp_actual - lp_expected) < lp_expected * 0.02);

            let mut hp = FilterState::new(SAMPLE_RATE);
            settle_filter(&mut hp, FILTER_RAW_CENTER + travel);
            assert!(hp.hp_mode);
            let hp_expected = FILTER_HP_MIN_HZ * libm::powf(8_000.0 / FILTER_HP_MIN_HZ, intensity);
            let hp_actual = programmed_cutoff_hz(&hp);
            assert!(libm::fabsf(hp_actual - hp_expected) < hp_expected * 0.02);
        }
    }

    #[test]
    fn stable_knob_skips_coefficient_recomputation() {
        let mut filter = FilterState::new(SAMPLE_RATE);
        settle_filter(&mut filter, FILTER_RAW_MIN);
        assert!(!filter.bypassed);

        let poison = -12_345.0;
        filter.a1 = poison;
        for _ in 0..4_096 {
            filter.process_frame(true, DspFrame::default());
        }
        assert_eq!(filter.a1, poison);

        filter.set_raw(FILTER_RAW_MAX);
        for _ in 0..4_096 {
            filter.process_frame(true, DspFrame::default());
        }
        assert_ne!(filter.a1, poison);
    }


    #[test]
    fn smart_cfx_center_and_extremes_are_identity() {
        assert_eq!(smart_cfx_curve_raw(FILTER_RAW_CENTER), FILTER_RAW_CENTER);
        assert_eq!(smart_cfx_curve_raw(FILTER_RAW_MIN), FILTER_RAW_MIN);
        assert_eq!(smart_cfx_curve_raw(FILTER_RAW_MAX), FILTER_RAW_MAX);
        assert_eq!(smart_cfx_curve_raw(u16::MAX), FILTER_RAW_MAX);
    }

    #[test]
    fn smart_cfx_softens_near_center() {
        let input = FILTER_RAW_CENTER - 512;
        let curved = smart_cfx_curve_raw(input);
        assert!(curved < FILTER_RAW_CENTER);
        assert!(curved > input);
    }

    #[test]
    fn smart_cfx_half_turn_is_near_linear() {
        let half_low = FILTER_RAW_CENTER / 2;
        let curved_low = smart_cfx_curve_raw(half_low);
        assert!(curved_low >= half_low - 8);
        assert!(curved_low <= half_low + 8);

        let half_high =
            FILTER_RAW_CENTER + (FILTER_RAW_MAX - FILTER_RAW_CENTER) / 2;
        let curved_high = smart_cfx_curve_raw(half_high);
        assert!(curved_high >= half_high - 8);
        assert!(curved_high <= half_high + 8);
    }

    #[test]
    fn smart_cfx_past_half_turn_runs_ahead_of_linear() {
        let three_quarters_low = FILTER_RAW_CENTER / 4;
        assert!(smart_cfx_curve_raw(three_quarters_low) < three_quarters_low);
    }

    #[test]
    fn raw_gain_mapping_matches_released_contract() {
        assert_eq!(eq_raw_to_gain(EQ_RAW_MIN), 0.0);
        assert_eq!(eq_raw_to_gain(EQ_RAW_CENTER), 1.0);
        assert_eq!(eq_raw_to_gain(EQ_RAW_MAX), 2.0);
        assert_eq!(eq_raw_to_gain(u16::MAX), 2.0);
    }

    #[test]
    fn raw_values_are_clamped_and_reported_without_forcing_immediate_refresh() {
        let mut eq = EqState::new(SAMPLE_RATE);
        eq.set_band_raw(EqBand::Low, u16::MAX);
        assert_eq!(eq.band_raw(EqBand::Low), EQ_RAW_MAX);

        eq.process_frame(DspFrame::default());
        eq.set_band_raw(EqBand::Low, EQ_RAW_MIN);
        for _ in 0..31 {
            eq.process_frame(DspFrame::default());
        }
        assert_eq!(eq.gain[EqBand::Low.index()], 2.0);

        eq.process_frame(DspFrame::default());
        assert_eq!(eq.gain[EqBand::Low.index()], 0.0);
    }

    #[test]
    fn sample_rate_retune_preserves_filter_history_and_gains() {
        let mut eq = EqState::new(SAMPLE_RATE);
        eq.set_band_raw(EqBand::Mid, EQ_RAW_MAX);
        eq.process_frame(DspFrame {
            left: 10_000.0,
            right: -10_000.0,
        });

        let low_before = eq.low_lp;
        let gain_before = eq.gain;
        eq.set_sample_rate(48_000);

        assert_eq!(eq.low_lp, low_before);
        assert_eq!(eq.gain, gain_before);
        assert_ne!(eq.low_alpha, one_pole_alpha(EQ_LOW_CUTOFF_HZ, SAMPLE_RATE));
    }

    #[test]
    fn center_eq_keeps_signal_level_near_unity() {
        let dry = rms_of_sine_after_eq(1_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let centered = rms_of_sine_after_eq(1_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);
        assert!(centered > dry * 0.98);
        assert!(centered < dry * 1.02);
    }

    #[test]
    fn low_kill_reduces_bass_more_than_treble() {
        let killed_bass = rms_of_sine_after_eq(100.0, EQ_RAW_MIN, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let normal_bass = rms_of_sine_after_eq(100.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let killed_treble = rms_of_sine_after_eq(8_000.0, EQ_RAW_MIN, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let normal_treble =
            rms_of_sine_after_eq(8_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);

        assert!(killed_bass < normal_bass * 0.35);
        assert!(killed_treble > normal_treble * 0.80);
    }

    #[test]
    fn high_kill_reduces_treble_more_than_bass() {
        let killed_treble = rms_of_sine_after_eq(8_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_MIN);
        let normal_treble =
            rms_of_sine_after_eq(8_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let killed_bass = rms_of_sine_after_eq(100.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_MIN);
        let normal_bass = rms_of_sine_after_eq(100.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);

        assert!(killed_treble < normal_treble * 0.35);
        assert!(killed_bass > normal_bass * 0.80);
    }

    #[test]
    fn mid_boost_increases_level_and_pcm_conversion_clamps() {
        let normal_mid = rms_of_sine_after_eq(1_000.0, EQ_RAW_CENTER, EQ_RAW_CENTER, EQ_RAW_CENTER);
        let boosted_mid = rms_of_sine_after_eq(1_000.0, EQ_RAW_CENTER, EQ_RAW_MAX, EQ_RAW_CENTER);
        assert!(boosted_mid > normal_mid * 1.35);

        let mut eq = EqState::new(SAMPLE_RATE);
        eq.set_raw(EQ_RAW_MAX, EQ_RAW_MAX, EQ_RAW_MAX);
        let out = eq.process_pcm_frame(PcmFrame {
            left: 30_000,
            right: -30_000,
        });
        assert_eq!(out.left, i16::MAX);
        assert_eq!(out.right, i16::MIN);
    }

    #[test]
    fn each_band_boost_preserves_wide_headroom() {
        for (freq_hz, band) in [
            (100.0, EqBand::Low),
            (1_000.0, EqBand::Mid),
            (8_000.0, EqBand::High),
        ] {
            let peak = peak_of_sine_after_wide_eq(freq_hz, band);
            assert!(peak > 32_768.0);
            assert!(peak < 60_000.0);
        }
    }

    #[test]
    fn pcm_conversion_matches_released_nan_round_and_clamp_policy() {
        assert_eq!(pcm_sample_from_float(f32::NAN), 0);
        assert_eq!(pcm_sample_from_float(32_768.0), i16::MAX);
        assert_eq!(pcm_sample_from_float(-32_769.0), i16::MIN);
        assert_eq!(pcm_sample_from_float(10.49), 10);
        assert_eq!(pcm_sample_from_float(10.50), 11);
        assert_eq!(pcm_sample_from_float(-10.49), -10);
        assert_eq!(pcm_sample_from_float(-10.50), -11);
    }
}
