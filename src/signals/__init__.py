"""Signal registry and batch computation."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from src.signals import (
    bench_impact,
    confidence_spread,
    days_rest,
    fatigue,
    game_state,
    goalkeeper_form,
    momentum,
    narrative,
    penalty_shootout,
    pressure,
    referee_matrix,
    set_piece,
    sharp_money,
    star_dependency,
    tactical_matchup,
    telemetry,
)

SIGNAL_COMPUTERS: dict[str, Callable[[pd.Series], float]] = {
    "fatigue_accumulation_index": fatigue.compute,
    "tactical_matchup_score": tactical_matchup.compute,
    "set_piece_differential": set_piece.compute,
    "pressure_resilience_index": pressure.compute,
    "momentum_velocity": momentum.compute,
    "narrative_pressure": narrative.compute,
    "penalty_shootout_prob": penalty_shootout.compute,
    "referee_team_compatibility": referee_matrix.compute,
    "game_state_elasticity": game_state.compute,
    "sharp_money_divergence": sharp_money.compute,
    "prediction_confidence_spread": confidence_spread.compute,
    "goalkeeper_form_index": goalkeeper_form.compute,
    "star_dependency_ratio": star_dependency.compute,
    "bench_impact_index": bench_impact.compute,
    "days_rest_effect": days_rest.compute,
}


def apply_all_signals(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for name, computer in SIGNAL_COMPUTERS.items():
        result[name] = result.apply(computer, axis=1)
    return telemetry.apply_hidden_telemetry_corrections(result)
