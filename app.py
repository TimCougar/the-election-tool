"""Flask web app for the elastic electoral swing calculator."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from flask import Flask, jsonify, render_template, request

from election_swing_calculator import Scenario, compute_swing, parse_demographics

app = Flask(__name__)


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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
