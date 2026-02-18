"""Probabilistic Electoral College simulation engine."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StateModel:
    name: str
    electoral_votes: int
    dem_share: float
    stddev: float

    def validate(self) -> None:
        if not self.name:
            raise ValueError("State name is required")
        if self.electoral_votes <= 0:
            raise ValueError(f"{self.name}: electoral_votes must be > 0")
        if not 0 <= self.dem_share <= 100:
            raise ValueError(f"{self.name}: dem_share must be 0-100")
        if self.stddev < 0:
            raise ValueError(f"{self.name}: stddev must be >= 0")


@dataclass(frozen=True)
class SimulationConfig:
    n_simulations: int = 10000
    seed: int = 2024
    national_stddev: float = 2.0
    correlation: float = 0.6

    def validate(self) -> None:
        if self.n_simulations <= 0:
            raise ValueError("n_simulations must be > 0")
        if self.national_stddev < 0:
            raise ValueError("national_stddev must be >= 0")
        if not 0 <= self.correlation <= 1:
            raise ValueError("correlation must be between 0 and 1")


def parse_states(raw_states: Iterable[dict]) -> list[StateModel]:
    states: list[StateModel] = []
    for item in raw_states:
        state = StateModel(
            name=str(item["name"]).strip(),
            electoral_votes=int(item["electoral_votes"]),
            dem_share=float(item["dem_share"]),
            stddev=float(item.get("stddev", 3.0)),
        )
        state.validate()
        states.append(state)
    if not states:
        raise ValueError("At least one state is required")
    return states


def percentile(sorted_values: list[int], pct: float) -> int:
    if not sorted_values:
        return 0
    idx = int(round((len(sorted_values) - 1) * pct))
    idx = max(0, min(idx, len(sorted_values) - 1))
    return sorted_values[idx]


def make_histogram(values: list[int], total_ev: int, bins: int = 24) -> list[dict[str, int]]:
    if not values:
        return []
    bins = max(8, bins)
    width = max(1, math.ceil((total_ev + 1) / bins))
    counts = [0 for _ in range(bins)]
    for value in values:
        index = min(value // width, bins - 1)
        counts[index] += 1

    histogram = []
    for i, count in enumerate(counts):
        start = i * width
        end = min(total_ev, start + width - 1)
        histogram.append({"start": start, "end": end, "count": count})
    return histogram


def run_simulation(states: list[StateModel], config: SimulationConfig) -> dict:
    config.validate()
    total_ev = sum(state.electoral_votes for state in states)
    ev_to_win = total_ev // 2 + 1
    random_source = random.Random(config.seed)

    dem_ev_results: list[int] = []
    state_dem_wins = Counter()
    tipping_counter = Counter()

    state_noise_scale = math.sqrt(max(0.0, 1 - config.correlation**2))

    for _ in range(config.n_simulations):
        national_error = random_source.gauss(0.0, config.national_stddev)
        simulated_margins: dict[str, float] = {}
        dem_ev = 0

        for state in states:
            baseline_margin = state.dem_share - 50.0
            state_error = random_source.gauss(0.0, state.stddev)
            sampled_margin = baseline_margin + config.correlation * national_error + state_noise_scale * state_error
            simulated_margins[state.name] = sampled_margin
            if sampled_margin >= 0:
                dem_ev += state.electoral_votes
                state_dem_wins[state.name] += 1

        rep_ev = total_ev - dem_ev
        dem_ev_results.append(dem_ev)

        winner = "Dem" if dem_ev >= ev_to_win else "Rep"
        won_states = [
            state
            for state in states
            if (simulated_margins[state.name] >= 0 if winner == "Dem" else simulated_margins[state.name] < 0)
        ]
        won_states.sort(
            key=lambda s: (
                simulated_margins[s.name] if winner == "Dem" else -simulated_margins[s.name]
            ),
            reverse=True,
        )

        cumulative = 0
        for state in won_states:
            cumulative += state.electoral_votes
            if cumulative >= ev_to_win:
                tipping_counter[state.name] += 1
                break

    dem_ev_sorted = sorted(dem_ev_results)
    rep_ev_sorted = sorted(total_ev - dem_ev for dem_ev in dem_ev_results)

    battleground = []
    for state in states:
        dem_prob = state_dem_wins[state.name] / config.n_simulations
        battleground.append(
            {
                "state": state.name,
                "ev": state.electoral_votes,
                "demWinProbability": dem_prob,
                "repWinProbability": 1 - dem_prob,
                "tippingPointFrequency": tipping_counter[state.name] / config.n_simulations,
            }
        )

    battleground.sort(key=lambda row: abs(row["demWinProbability"] - 0.5))

    return {
        "nSimulations": config.n_simulations,
        "seed": config.seed,
        "evToWin": ev_to_win,
        "totalEv": total_ev,
        "winProbabilityDem": sum(1 for ev in dem_ev_results if ev >= ev_to_win) / config.n_simulations,
        "winProbabilityRep": sum(1 for ev in dem_ev_results if ev < ev_to_win) / config.n_simulations,
        "evPercentiles": {
            "dem": {
                "p5": percentile(dem_ev_sorted, 0.05),
                "p50": percentile(dem_ev_sorted, 0.5),
                "p95": percentile(dem_ev_sorted, 0.95),
            },
            "rep": {
                "p5": percentile(rep_ev_sorted, 0.05),
                "p50": percentile(rep_ev_sorted, 0.5),
                "p95": percentile(rep_ev_sorted, 0.95),
            },
        },
        "evHistogram": make_histogram(dem_ev_results, total_ev),
        "stateProbabilities": battleground,
        "topBattlegrounds": battleground[:10],
        "tippingPointStates": tipping_counter.most_common(10),
    }
