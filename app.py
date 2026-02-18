"""Flask web app for the elastic electoral swing calculator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from flask import Flask, jsonify, render_template, request

from election_swing_calculator import Scenario, compute_swing, parse_demographics

app = Flask(__name__)

VALID_STATE_CODES = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}


@app.get("/")
def index() -> str:
    return render_template("index.html")


def serialize_outcome(outcome: Any) -> dict[str, Any]:
    return asdict(outcome)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _normalize(a_share: float, b_share: float) -> tuple[float, float]:
    a_share = _clamp(a_share, 0.0, 100.0)
    b_share = _clamp(b_share, 0.0, 100.0)
    total = a_share + b_share
    if total <= 0:
        return 50.0, 50.0
    return (a_share / total) * 100.0, (b_share / total) * 100.0


def _scenario_error(message: str) -> tuple[Any, int]:
    return jsonify({"error": message}), 400


def _validate_state_code(code: str, context: str) -> str:
    normalized = code.upper().strip()
    if normalized not in VALID_STATE_CODES:
        raise ValueError(
            f"{context}: '{code}' is not a valid US state code. Use two-letter codes like 'PA' or 'AZ'."
        )
    return normalized


def _compute_layered_scenario(payload: dict[str, Any]) -> dict[str, Any]:
    baseline_states = payload.get("baselineStateShares", [])
    scenario = payload.get("scenario", {})

    if not baseline_states:
        raise ValueError(
            "baselineStateShares is required. Add at least one state with voters and party shares."
        )

    national_swing = scenario.get("nationalSwing", {})
    state_adjustments = scenario.get("stateAdjustments", {})
    turnout_shocks = scenario.get("turnoutShocks", [])
    demographic_effects = scenario.get("demographicEffects", {})

    state_inputs: dict[str, dict[str, float]] = {}

    for row in baseline_states:
        state_raw = str(row.get("state", ""))
        state = _validate_state_code(state_raw, "baselineStateShares")

        voters = float(row.get("voters", 0) or 0)
        if voters < 0:
            raise ValueError(f"baselineStateShares[{state}]: voters must be >= 0.")

        share_a = float(row.get("shareA", 0) or 0)
        share_b = float(row.get("shareB", 0) or 0)
        if share_a < 0 or share_b < 0:
            raise ValueError(
                f"baselineStateShares[{state}]: shareA/shareB must both be >= 0."
            )
        if share_a + share_b > 100:
            raise ValueError(
                f"baselineStateShares[{state}]: total share > 100. Lower shareA/shareB so the sum is <= 100."
            )
        state_inputs[state] = {"voters": voters, "shareA": share_a, "shareB": share_b}

    shift_a = float(national_swing.get("shiftA", 0) or 0)
    shift_b = float(national_swing.get("shiftB", -shift_a) or 0)

    for state_code in state_adjustments:
        _validate_state_code(str(state_code), "stateAdjustments")

    for group_key, impacts in demographic_effects.items():
        if not isinstance(impacts, dict):
            raise ValueError(
                f"demographicEffects[{group_key}] must be an object like {{'PA': 1.2}}."
            )
        for state_code in impacts:
            _validate_state_code(str(state_code), f"demographicEffects[{group_key}]")

    layered_states: list[dict[str, Any]] = []
    assumption_lines = [
        f"National swing applied first: A {shift_a:+.2f} pts, B {shift_b:+.2f} pts.",
        "Then per-state overrides were applied.",
        "Then turnout shocks were translated with demographicEffects and applied.",
        "Final shares were clamped to 0-100 and normalized to sum to 100.",
    ]

    for state, values in state_inputs.items():
        a_share = values["shareA"]
        b_share = values["shareB"]
        applied_effects: list[str] = []

        a_share += shift_a
        b_share += shift_b

        state_override_raw = state_adjustments.get(state, 0)
        if isinstance(state_override_raw, dict):
            state_shift_a = float(state_override_raw.get("shiftA", 0) or 0)
            state_shift_b = float(state_override_raw.get("shiftB", -state_shift_a) or 0)
        else:
            state_shift_a = float(state_override_raw or 0)
            state_shift_b = -state_shift_a

        a_share += state_shift_a
        b_share += state_shift_b
        if state_shift_a or state_shift_b:
            applied_effects.append(
                f"state override A {state_shift_a:+.2f}, B {state_shift_b:+.2f}"
            )

        for i, shock in enumerate(turnout_shocks):
            group_key = str(shock.get("groupKey", "")).strip()
            if not group_key:
                raise ValueError(
                    f"turnoutShocks[{i}] is missing groupKey. Add a groupKey that exists in demographicEffects."
                )
            if group_key not in demographic_effects:
                raise ValueError(
                    f"turnoutShocks[{i}] unknown group key '{group_key}'. Add demographicEffects['{group_key}'] or update the shock key."
                )

            target_state = str(shock.get("state", "ALL")).strip().upper() or "ALL"
            multiplier = float(shock.get("multiplier", 1) or 0)
            group_map: dict[str, Any] = demographic_effects[group_key]

            if target_state != "ALL":
                _validate_state_code(target_state, f"turnoutShocks[{i}]")
                if target_state != state:
                    continue
                effect = float(group_map.get(state, 0) or 0)
                if effect:
                    a_share += effect * multiplier
                    b_share -= effect * multiplier
                    applied_effects.append(
                        f"{group_key} turnout x{multiplier:.2f} -> A {effect * multiplier:+.2f}"
                    )
                continue

            effect = float(group_map.get(state, 0) or 0)
            if effect:
                a_share += effect * multiplier
                b_share -= effect * multiplier
                applied_effects.append(
                    f"{group_key} turnout x{multiplier:.2f} -> A {effect * multiplier:+.2f}"
                )

        normalized_a, normalized_b = _normalize(a_share, b_share)
        layered_states.append(
            {
                "state": state,
                "voters": int(round(values["voters"])),
                "baseline": {"shareA": values["shareA"], "shareB": values["shareB"]},
                "scenario": {"shareA": normalized_a, "shareB": normalized_b},
                "effects": applied_effects,
            }
        )

    total_voters = sum(item["voters"] for item in layered_states)
    if total_voters:
        baseline_share_a = (
            sum(item["baseline"]["shareA"] * item["voters"] for item in layered_states)
            / total_voters
        )
        scenario_share_a = (
            sum(item["scenario"]["shareA"] * item["voters"] for item in layered_states)
            / total_voters
        )
    else:
        baseline_share_a = 0.0
        scenario_share_a = 0.0

    return {
        "states": sorted(layered_states, key=lambda row: row["state"]),
        "national": {
            "totalVoters": total_voters,
            "baselineShareA": baseline_share_a,
            "scenarioShareA": scenario_share_a,
            "swingA": scenario_share_a - baseline_share_a,
        },
        "assumptionsSummary": assumption_lines,
    }


@app.post("/calculate")
def calculate() -> Any:
    payload = request.get_json(force=True)

    if payload.get("baselineStateShares") is not None:
        try:
            return jsonify(_compute_layered_scenario(payload))
        except ValueError as error:
            return _scenario_error(str(error))

    demographics = parse_demographics(payload.get("demographics", []))
    scenario = Scenario(turnout_delta=payload.get("turnout_delta", {}))
    swing = compute_swing(demographics, scenario)

    return jsonify(
        {
            "baseline": serialize_outcome(swing.baseline),
            "scenario": serialize_outcome(swing.scenario),
            "vote_swing_a": swing.vote_swing_a,
            "share_swing_a": swing.share_swing_a,
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
