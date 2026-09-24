#![no_std]
#![forbid(unsafe_code)]

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct Beat {
    pub time_ms: u32,
    pub phase: u16,
    pub bpm_x100: u32,
}


#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AnalysisProvider {
    RekordboxImport,
    AptaCache,
    AptaNative,
}

#[derive(Clone, Copy, Debug)]
pub struct TrackAnalysis<'a> {
    provider: AnalysisProvider,
    generation: u32,
    bpm_x100: u32,
    beat_grid: Option<BeatGrid<'a>>,
}

impl<'a> TrackAnalysis<'a> {
    pub const fn new(
        provider: AnalysisProvider,
        generation: u32,
        bpm_x100: u32,
        beat_grid: Option<BeatGrid<'a>>,
    ) -> Self {
        Self {
            provider,
            generation,
            bpm_x100,
            beat_grid,
        }
    }

    pub const fn provider(&self) -> AnalysisProvider {
        self.provider
    }

    pub const fn generation(&self) -> u32 {
        self.generation
    }

    pub const fn bpm_x100(&self) -> u32 {
        self.bpm_x100
    }

    pub const fn beat_grid(&self) -> Option<BeatGrid<'a>> {
        self.beat_grid
    }
}

#[derive(Clone, Copy, Debug)]
pub struct BeatGrid<'a> {
    beats: &'a [Beat],
}

impl<'a> BeatGrid<'a> {
    pub const fn new(beats: &'a [Beat]) -> Self {
        Self { beats }
    }

    pub const fn beats(&self) -> &'a [Beat] {
        self.beats
    }

    pub const fn is_empty(&self) -> bool {
        self.beats.is_empty()
    }

    pub fn nearest_index(&self, position_ms: u32) -> Option<usize> {
        let mut closest = None;
        let mut min_diff = u32::MAX;

        for (index, beat) in self.beats.iter().enumerate() {
            let diff = position_ms.abs_diff(beat.time_ms);
            if diff < min_diff {
                min_diff = diff;
                closest = Some(index);
            }
        }

        closest
    }
}

/// Align a target playhead to the reference deck's beat phase while preserving
/// the reference deck's signed intra-beat offset.
///
/// This is the provider-neutral equivalent of the released M2.2 phase-align
/// behavior. Rekordbox and future APTA providers only supply immutable BeatGrid
/// values.
pub fn phase_align_target_ms(
    target_position_ms: u32,
    target: BeatGrid<'_>,
    reference_position_ms: u32,
    reference: BeatGrid<'_>,
) -> Option<u32> {
    let reference_index = reference.nearest_index(reference_position_ms)?;
    let reference_beat = reference.beats()[reference_index];
    let target_phase = reference_beat.phase;
    let reference_offset_ms =
        reference_position_ms as i64 - reference_beat.time_ms as i64;

    let mut best = None;
    let mut min_diff = u32::MAX;

    for beat in target.beats() {
        if beat.phase != target_phase {
            continue;
        }

        let candidate = (beat.time_ms as i64 + reference_offset_ms).max(0);
        let candidate_ms = candidate.min(u32::MAX as i64) as u32;
        let diff = target_position_ms.abs_diff(candidate_ms);

        if best.is_none() || diff < min_diff {
            best = Some(candidate_ms);
            min_diff = diff;
        }
    }

    best
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn neutral_track_analysis_keeps_provider_and_generation_explicit() {
        let beats = [Beat {
            time_ms: 1000,
            phase: 0,
            bpm_x100: 12_000,
        }];
        let analysis = TrackAnalysis::new(
            AnalysisProvider::RekordboxImport,
            7,
            12_000,
            Some(BeatGrid::new(&beats)),
        );

        assert_eq!(analysis.provider(), AnalysisProvider::RekordboxImport);
        assert_eq!(analysis.generation(), 7);
        assert_eq!(analysis.bpm_x100(), 12_000);
        assert_eq!(analysis.beat_grid().unwrap().beats(), &beats);
    }

    #[test]
    fn nearest_beat_prefers_first_entry_on_equal_distance() {
        let beats = [
            Beat {
                time_ms: 1000,
                phase: 0,
                bpm_x100: 12_000,
            },
            Beat {
                time_ms: 2000,
                phase: 1,
                bpm_x100: 12_000,
            },
        ];

        let grid = BeatGrid::new(&beats);
        assert_eq!(grid.nearest_index(1500), Some(0));
    }

    #[test]
    fn released_phase_align_fixture_returns_1962_ms() {
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

        assert_eq!(
            phase_align_target_ms(
                2600,
                BeatGrid::new(&target_beats),
                8900,
                BeatGrid::new(&reference_beats),
            ),
            Some(1962)
        );
    }

    #[test]
    fn phase_align_requires_both_nonempty_grids() {
        let target_beats = [Beat {
            time_ms: 1000,
            phase: 0,
            bpm_x100: 12_000,
        }];
        let empty: [Beat; 0] = [];

        assert_eq!(
            phase_align_target_ms(
                1000,
                BeatGrid::new(&target_beats),
                1000,
                BeatGrid::new(&empty),
            ),
            None
        );
        assert_eq!(
            phase_align_target_ms(
                1000,
                BeatGrid::new(&empty),
                1000,
                BeatGrid::new(&target_beats),
            ),
            None
        );
    }

    #[test]
    fn negative_reference_offset_clamps_candidate_to_zero() {
        let target_beats = [Beat {
            time_ms: 100,
            phase: 0,
            bpm_x100: 12_000,
        }];
        let reference_beats = [Beat {
            time_ms: 1000,
            phase: 0,
            bpm_x100: 12_000,
        }];

        assert_eq!(
            phase_align_target_ms(
                0,
                BeatGrid::new(&target_beats),
                0,
                BeatGrid::new(&reference_beats),
            ),
            Some(0)
        );
    }

    #[test]
    fn missing_matching_phase_returns_none() {
        let target_beats = [Beat {
            time_ms: 1000,
            phase: 0,
            bpm_x100: 12_000,
        }];
        let reference_beats = [Beat {
            time_ms: 1000,
            phase: 2,
            bpm_x100: 12_000,
        }];

        assert_eq!(
            phase_align_target_ms(
                1000,
                BeatGrid::new(&target_beats),
                1000,
                BeatGrid::new(&reference_beats),
            ),
            None
        );
    }
}
