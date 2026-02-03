"""Elastic electoral swing calculator for demographic-based scenarios."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Demographic:
    name: str
    baseline_voters: int
    base_support_a: float
    elasticity: float

    def validate(self) -> None:
        if self.baseline_voters < 0:
            raise ValueError(f"{self.name}: baseline_voters must be >= 0")
        if not self.base_support_a <= 100:
            raise ValueError(f"{self.name}: base_support_a must be 0-100")


@dataclass(frozen=True)
class Scenario:
    turnout_delta: dict[str, int]


@dataclass(frozen=True)
class Outcome:
    total_voters: int
    votes_a: int
    votes_b: int
    share_a: float
    share_b: float


@dataclass(frozen=True)
class Swing:
    baseline: Outcome
    scenario: Outcome
    vote_swing_a: int
    share_swing_a: float


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def parse_demographics(raw: Iterable[dict]) -> list[Demographic]:
    demographics: list[Demographic] = []
    for item in raw:
        demographic = Demographic(
            name=item["name"],
            baseline_voters=int(item["baseline_voters"]),
            base_support_a=float(item["base_support_a"]),
            elasticity=float(item.get("elasticity", 0.0)),
        )
        demographic.validate()
        demographics.append(demographic)
    return demographics


def compute_outcome(
    demographics: Iterable[Demographic],
    turnout_delta: dict[str, int] | None = None,
) -> Outcome:
    turnout_delta = turnout_delta or {}
    total_voters = 0
    total_votes_a = 0

    for demo in demographics:
        delta = int(turnout_delta.get(demo.name, 0))
        if delta == 0:
            adjusted_support = demo.base_support_a
        else:
            turnout_change_pct = (delta / demo.baseline_voters) * 100 if demo.baseline_voters else 0.0
            adjusted_support = demo.base_support_a + demo.elasticity * turnout_change_pct
        adjusted_support = clamp(adjusted_support, 0.0, 100.0)

        voters = demo.baseline_voters + delta
        if voters < 0:
            raise ValueError(f"{demo.name}: turnout delta produces negative voters")

        votes_a = round(voters * adjusted_support / 100)
        total_votes_a += votes_a
        total_voters += voters

    votes_b = total_voters - total_votes_a
    share_a = (total_votes_a / total_voters * 100) if total_voters else 0.0
    share_b = 100 - share_a if total_voters else 0.0

    return Outcome(
        total_voters=total_voters,
        votes_a=total_votes_a,
        votes_b=votes_b,
        share_a=share_a,
        share_b=share_b,
    )


def compute_swing(demographics: Iterable[Demographic], scenario: Scenario) -> Swing:
    baseline = compute_outcome(demographics)
    scenario_outcome = compute_outcome(demographics, scenario.turnout_delta)
    vote_swing_a = scenario_outcome.votes_a - baseline.votes_a
    share_swing_a = scenario_outcome.share_a - baseline.share_a
    return Swing(
        baseline=baseline,
        scenario=scenario_outcome,
        vote_swing_a=vote_swing_a,
        share_swing_a=share_swing_a,
    )


def format_outcome(label: str, outcome: Outcome) -> str:
    return (
        f"{label}: total voters={outcome.total_voters}, "
        f"A votes={outcome.votes_a}, B votes={outcome.votes_b}, "
        f"A share={outcome.share_a:.2f}%, B share={outcome.share_b:.2f}%"
    )


def load_config(path: Path) -> tuple[list[Demographic], Scenario]:
    data = json.loads(path.read_text())
    demographics = parse_demographics(data["demographics"])
    scenario = Scenario(turnout_delta=data.get("turnout_delta", {}))
    return demographics, scenario


def main() -> None:
    parser = argparse.ArgumentParser(description="Elastic electoral swing calculator")
    parser.add_argument("config", type=Path, help="Path to JSON config")
    args = parser.parse_args()

    demographics, scenario = load_config(args.config)
    swing = compute_swing(demographics, scenario)

    print(format_outcome("Baseline", swing.baseline))
    print(format_outcome("Scenario", swing.scenario))
    print(
        f"Swing for A: {swing.vote_swing_a:+d} votes "
        f"({swing.share_swing_a:+.2f} percentage points)"
    )


if __name__ == "__main__":
    main()
