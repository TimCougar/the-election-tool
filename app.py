"""Flask web app for the elastic electoral swing calculator."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from election_swing_calculator import Scenario, compute_swing, parse_demographics

app = Flask(__name__, static_folder="static", static_url_path="/static")
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600


def _compute_asset_version() -> str:
    static_dir = Path(app.static_folder)
    asset_paths = [static_dir / "css" / "app.css", static_dir / "js" / "app.js"]
    timestamps = [path.stat().st_mtime_ns for path in asset_paths if path.exists()]
    return str(max(timestamps, default=0))


ASSET_VERSION = _compute_asset_version()


@app.context_processor
def inject_asset_version() -> dict[str, str]:
    return {"asset_version": ASSET_VERSION}


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
