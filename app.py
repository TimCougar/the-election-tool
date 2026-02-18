"""Flask web app for the elastic electoral swing calculator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from flask import Flask, jsonify, render_template, request

from election_swing_calculator import Scenario, compute_swing, parse_demographics
from simulation import SimulationConfig, parse_states, run_simulation

app = Flask(__name__)


@app.errorhandler(ValueError)
def handle_value_error(error: ValueError) -> tuple[Any, int]:
    return jsonify({"error": str(error)}), 400


@app.get("/")
def index() -> str:
    return render_template("index.html")


def serialize_outcome(outcome: Any) -> dict[str, Any]:
    return asdict(outcome)


@app.post("/calculate")
def calculate() -> Any:
    payload = request.get_json(force=True)
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


@app.post("/simulate")
def simulate() -> Any:
    payload = request.get_json(force=True)
    states = parse_states(payload.get("states", []))
    config = SimulationConfig(
        n_simulations=int(payload.get("n_simulations", 10000)),
        seed=int(payload.get("seed", 2024)),
        national_stddev=float(payload.get("national_stddev", 2.0)),
        correlation=float(payload.get("correlation", 0.6)),
    )
    return jsonify(run_simulation(states, config))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
