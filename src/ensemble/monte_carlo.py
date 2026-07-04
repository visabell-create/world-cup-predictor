"""Monte Carlo tournament bracket simulation."""

from __future__ import annotations

from typing import Any

import numpy as np

from src.config import load_config


class TournamentMonteCarlo:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg = config or load_config()
        self.n_simulations = cfg.get("monte_carlo", {}).get("simulations", 10000)

    def simulate_match(
        self,
        p_home_win_90: float,
        p_draw_90: float,
        p_home_win_et: float = 0.5,
        p_home_win_pens: float = 0.5,
    ) -> str:
        roll = np.random.random()
        if roll < p_home_win_90:
            return "home"
        if roll < p_home_win_90 + p_draw_90:
            et_roll = np.random.random()
            if et_roll < p_home_win_et:
                return "home"
            pen_roll = np.random.random()
            return "home" if pen_roll < p_home_win_pens else "away"
        return "away"

    def run_bracket(
        self,
        match_probs: list[dict[str, float]],
    ) -> dict[str, Any]:
        home_wins = 0
        for _ in range(self.n_simulations):
            winners = []
            for prob in match_probs:
                winner = self.simulate_match(
                    prob.get("p_win_90", 0.4),
                    prob.get("p_draw_90", 0.25),
                    prob.get("p_win_et", 0.5),
                    prob.get("p_win_pens", 0.5),
                )
                winners.append(winner)
            if winners and winners[0] == "home":
                home_wins += 1
        return {
            "simulations": self.n_simulations,
            "home_advance_rate": home_wins / self.n_simulations,
            "matches_simulated": len(match_probs),
        }
