"""Bayesian belief updating for match outcomes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class BeliefState:
    prior: float
    likelihood: float
    posterior: float
    evidence: list[str] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


class BayesianEngine:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        config = config or {}
        self.default_prior = config.get("default_prior", 0.50)
        self.min_confidence = config.get("min_confidence", 0.05)
        self.max_confidence = config.get("max_confidence", 0.95)
        self.states: dict[str, BeliefState] = {}

    def get_or_create(self, key: str) -> BeliefState:
        if key not in self.states:
            self.states[key] = BeliefState(
                prior=self.default_prior,
                likelihood=1.0,
                posterior=self.default_prior,
            )
        return self.states[key]

    def update(self, key: str, likelihood: float, evidence: str = "") -> float:
        state = self.get_or_create(key)
        state.prior = state.posterior
        state.likelihood = likelihood
        raw_posterior = state.prior * likelihood
        normalization = raw_posterior + (1 - state.prior) * (2 - likelihood)
        state.posterior = raw_posterior / (normalization + 1e-9)
        state.posterior = max(self.min_confidence, min(self.max_confidence, state.posterior))
        if evidence:
            state.evidence.append(evidence)
            state.history.append(
                {
                    "prior": state.prior,
                    "likelihood": likelihood,
                    "posterior": state.posterior,
                    "evidence": evidence,
                }
            )
        return state.posterior

    def get_posterior(self, key: str) -> float:
        return self.get_or_create(key).posterior
