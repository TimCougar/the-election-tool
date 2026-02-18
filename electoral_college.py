"""Electoral College outcome model for state and district-level allocations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Canonical baseline dataset (states + DC) using 2020-era two-party share assumptions.
# Shares are approximate and meant to be scenario baselines.
STATE_BASELINES: list[dict[str, Any]] = [
    {"code": "AL", "name": "Alabama", "electoral_votes": 9, "dem_share": 36.6, "rep_share": 62.0, "baseline_turnout": 2320000, "uncertainty": 2.0},
    {"code": "AK", "name": "Alaska", "electoral_votes": 3, "dem_share": 42.8, "rep_share": 52.8, "baseline_turnout": 360000, "uncertainty": 3.0},
    {"code": "AZ", "name": "Arizona", "electoral_votes": 11, "dem_share": 49.4, "rep_share": 49.1, "baseline_turnout": 3387000, "uncertainty": 2.5},
    {"code": "AR", "name": "Arkansas", "electoral_votes": 6, "dem_share": 34.8, "rep_share": 62.4, "baseline_turnout": 1219000, "uncertainty": 2.0},
    {"code": "CA", "name": "California", "electoral_votes": 54, "dem_share": 63.5, "rep_share": 34.3, "baseline_turnout": 17500000, "uncertainty": 1.5},
    {"code": "CO", "name": "Colorado", "electoral_votes": 10, "dem_share": 55.4, "rep_share": 41.9, "baseline_turnout": 3296000, "uncertainty": 1.8},
    {"code": "CT", "name": "Connecticut", "electoral_votes": 7, "dem_share": 59.3, "rep_share": 39.2, "baseline_turnout": 1820000, "uncertainty": 1.5},
    {"code": "DE", "name": "Delaware", "electoral_votes": 3, "dem_share": 58.8, "rep_share": 39.8, "baseline_turnout": 510000, "uncertainty": 1.8},
    {"code": "DC", "name": "District of Columbia", "electoral_votes": 3, "dem_share": 92.1, "rep_share": 5.4, "baseline_turnout": 345000, "uncertainty": 1.0},
    {"code": "FL", "name": "Florida", "electoral_votes": 30, "dem_share": 47.9, "rep_share": 51.2, "baseline_turnout": 11140000, "uncertainty": 2.8},
    {"code": "GA", "name": "Georgia", "electoral_votes": 16, "dem_share": 49.5, "rep_share": 49.3, "baseline_turnout": 5000000, "uncertainty": 2.6},
    {"code": "HI", "name": "Hawaii", "electoral_votes": 4, "dem_share": 63.7, "rep_share": 34.3, "baseline_turnout": 580000, "uncertainty": 2.0},
    {"code": "ID", "name": "Idaho", "electoral_votes": 4, "dem_share": 33.1, "rep_share": 63.8, "baseline_turnout": 880000, "uncertainty": 1.8},
    {"code": "IL", "name": "Illinois", "electoral_votes": 19, "dem_share": 57.5, "rep_share": 40.6, "baseline_turnout": 6034000, "uncertainty": 1.6},
    {"code": "IN", "name": "Indiana", "electoral_votes": 11, "dem_share": 41.0, "rep_share": 57.0, "baseline_turnout": 3030000, "uncertainty": 2.0},
    {"code": "IA", "name": "Iowa", "electoral_votes": 6, "dem_share": 44.9, "rep_share": 53.1, "baseline_turnout": 1700000, "uncertainty": 2.2},
    {"code": "KS", "name": "Kansas", "electoral_votes": 6, "dem_share": 41.5, "rep_share": 56.2, "baseline_turnout": 1370000, "uncertainty": 2.0},
    {"code": "KY", "name": "Kentucky", "electoral_votes": 8, "dem_share": 36.2, "rep_share": 62.1, "baseline_turnout": 2130000, "uncertainty": 1.8},
    {"code": "LA", "name": "Louisiana", "electoral_votes": 8, "dem_share": 39.9, "rep_share": 58.5, "baseline_turnout": 2150000, "uncertainty": 2.2},
    {"code": "ME", "name": "Maine", "electoral_votes": 4, "allocation": "district", "at_large_evs": 2, "dem_share": 53.1, "rep_share": 44.0, "baseline_turnout": 820000, "uncertainty": 2.4,
     "districts": [
         {"id": "ME-1", "electoral_votes": 1, "dem_share": 60.0, "rep_share": 38.0},
         {"id": "ME-2", "electoral_votes": 1, "dem_share": 45.0, "rep_share": 53.0},
     ]},
    {"code": "MD", "name": "Maryland", "electoral_votes": 10, "dem_share": 65.4, "rep_share": 32.1, "baseline_turnout": 3030000, "uncertainty": 1.6},
    {"code": "MA", "name": "Massachusetts", "electoral_votes": 11, "dem_share": 65.6, "rep_share": 32.1, "baseline_turnout": 3630000, "uncertainty": 1.5},
    {"code": "MI", "name": "Michigan", "electoral_votes": 15, "dem_share": 50.6, "rep_share": 47.8, "baseline_turnout": 5540000, "uncertainty": 2.4},
    {"code": "MN", "name": "Minnesota", "electoral_votes": 10, "dem_share": 52.4, "rep_share": 45.3, "baseline_turnout": 3280000, "uncertainty": 2.0},
    {"code": "MS", "name": "Mississippi", "electoral_votes": 6, "dem_share": 41.1, "rep_share": 57.6, "baseline_turnout": 1310000, "uncertainty": 2.1},
    {"code": "MO", "name": "Missouri", "electoral_votes": 10, "dem_share": 41.4, "rep_share": 56.8, "baseline_turnout": 3020000, "uncertainty": 2.0},
    {"code": "MT", "name": "Montana", "electoral_votes": 4, "dem_share": 40.5, "rep_share": 56.9, "baseline_turnout": 610000, "uncertainty": 2.0},
    {"code": "NE", "name": "Nebraska", "electoral_votes": 5, "allocation": "district", "at_large_evs": 2, "dem_share": 39.2, "rep_share": 58.2, "baseline_turnout": 970000, "uncertainty": 2.4,
     "districts": [
         {"id": "NE-1", "electoral_votes": 1, "dem_share": 45.0, "rep_share": 53.0},
         {"id": "NE-2", "electoral_votes": 1, "dem_share": 52.0, "rep_share": 46.0},
         {"id": "NE-3", "electoral_votes": 1, "dem_share": 25.0, "rep_share": 73.0},
     ]},
    {"code": "NV", "name": "Nevada", "electoral_votes": 6, "dem_share": 50.1, "rep_share": 47.7, "baseline_turnout": 1405000, "uncertainty": 2.7},
    {"code": "NH", "name": "New Hampshire", "electoral_votes": 4, "dem_share": 52.7, "rep_share": 45.4, "baseline_turnout": 815000, "uncertainty": 2.4},
    {"code": "NJ", "name": "New Jersey", "electoral_votes": 14, "dem_share": 57.3, "rep_share": 41.4, "baseline_turnout": 4600000, "uncertainty": 1.7},
    {"code": "NM", "name": "New Mexico", "electoral_votes": 5, "dem_share": 54.3, "rep_share": 43.5, "baseline_turnout": 930000, "uncertainty": 2.0},
    {"code": "NY", "name": "New York", "electoral_votes": 28, "dem_share": 60.9, "rep_share": 37.7, "baseline_turnout": 8600000, "uncertainty": 1.8},
    {"code": "NC", "name": "North Carolina", "electoral_votes": 16, "dem_share": 48.6, "rep_share": 50.1, "baseline_turnout": 5520000, "uncertainty": 2.5},
    {"code": "ND", "name": "North Dakota", "electoral_votes": 3, "dem_share": 31.8, "rep_share": 65.1, "baseline_turnout": 370000, "uncertainty": 1.8},
    {"code": "OH", "name": "Ohio", "electoral_votes": 17, "dem_share": 45.2, "rep_share": 53.3, "baseline_turnout": 5900000, "uncertainty": 2.1},
    {"code": "OK", "name": "Oklahoma", "electoral_votes": 7, "dem_share": 32.3, "rep_share": 65.4, "baseline_turnout": 1570000, "uncertainty": 1.7},
    {"code": "OR", "name": "Oregon", "electoral_votes": 8, "dem_share": 56.5, "rep_share": 40.4, "baseline_turnout": 2400000, "uncertainty": 1.9},
    {"code": "PA", "name": "Pennsylvania", "electoral_votes": 19, "dem_share": 50.0, "rep_share": 48.8, "baseline_turnout": 6915000, "uncertainty": 2.6},
    {"code": "RI", "name": "Rhode Island", "electoral_votes": 4, "dem_share": 59.5, "rep_share": 38.7, "baseline_turnout": 520000, "uncertainty": 1.8},
    {"code": "SC", "name": "South Carolina", "electoral_votes": 9, "dem_share": 43.4, "rep_share": 55.1, "baseline_turnout": 2520000, "uncertainty": 2.1},
    {"code": "SD", "name": "South Dakota", "electoral_votes": 3, "dem_share": 35.6, "rep_share": 61.8, "baseline_turnout": 430000, "uncertainty": 1.9},
    {"code": "TN", "name": "Tennessee", "electoral_votes": 11, "dem_share": 37.4, "rep_share": 60.7, "baseline_turnout": 3050000, "uncertainty": 2.0},
    {"code": "TX", "name": "Texas", "electoral_votes": 40, "dem_share": 46.5, "rep_share": 52.1, "baseline_turnout": 11320000, "uncertainty": 2.4},
    {"code": "UT", "name": "Utah", "electoral_votes": 6, "dem_share": 37.7, "rep_share": 58.1, "baseline_turnout": 1460000, "uncertainty": 2.0},
    {"code": "VT", "name": "Vermont", "electoral_votes": 3, "dem_share": 66.1, "rep_share": 30.7, "baseline_turnout": 370000, "uncertainty": 1.4},
    {"code": "VA", "name": "Virginia", "electoral_votes": 13, "dem_share": 54.1, "rep_share": 44.0, "baseline_turnout": 4500000, "uncertainty": 2.0},
    {"code": "WA", "name": "Washington", "electoral_votes": 12, "dem_share": 58.2, "rep_share": 38.8, "baseline_turnout": 4100000, "uncertainty": 1.8},
    {"code": "WV", "name": "West Virginia", "electoral_votes": 4, "dem_share": 29.7, "rep_share": 68.6, "baseline_turnout": 790000, "uncertainty": 1.6},
    {"code": "WI", "name": "Wisconsin", "electoral_votes": 10, "dem_share": 49.6, "rep_share": 48.9, "baseline_turnout": 3300000, "uncertainty": 2.4},
    {"code": "WY", "name": "Wyoming", "electoral_votes": 3, "dem_share": 26.6, "rep_share": 70.4, "baseline_turnout": 280000, "uncertainty": 1.5},
]


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(value, high))


def _normalize_two_party(dem_share: float, rep_share: float) -> tuple[float, float]:
    dem = _clamp(dem_share)
    rep = _clamp(rep_share)
    total = dem + rep
    if total <= 0:
        return 50.0, 50.0
    return (dem / total) * 100.0, (rep / total) * 100.0


def _winner(dem_share: float, rep_share: float) -> str:
    return "dem" if dem_share > rep_share else "rep"


def applyScenarioToState(state: dict[str, Any], scenario: dict[str, Any] | None) -> dict[str, Any]:
    """Apply scenario shifts to a single state and resolve deterministic winners."""
    scenario = scenario or {}
    national_dem_shift = float(scenario.get("national_dem_shift", 0.0))
    national_rep_shift = float(scenario.get("national_rep_shift", 0.0))
    global_turnout_multiplier = float(scenario.get("turnout_multiplier", 1.0))
    per_state = scenario.get("state_shifts", {})
    state_shift = per_state.get(state["code"], {})

    dem = float(state["dem_share"]) + national_dem_shift + float(state_shift.get("dem_shift", 0.0))
    rep = float(state["rep_share"]) + national_rep_shift + float(state_shift.get("rep_shift", 0.0))
    dem, rep = _normalize_two_party(dem, rep)

    turnout_multiplier = global_turnout_multiplier * float(state_shift.get("turnout_multiplier", 1.0))
    turnout = max(0, round(float(state.get("baseline_turnout", 0)) * turnout_multiplier))
    popular_dem = round(turnout * dem / 100)
    popular_rep = turnout - popular_dem

    result: dict[str, Any] = {
        "code": state["code"],
        "name": state["name"],
        "allocation": state.get("allocation", "winner_take_all"),
        "electoral_votes": int(state["electoral_votes"]),
        "dem_share": dem,
        "rep_share": rep,
        "winner": _winner(dem, rep),
        "popular_dem": popular_dem,
        "popular_rep": popular_rep,
        "uncertainty": state.get("uncertainty"),
    }

    if state.get("allocation") == "district":
        district_shifts = state_shift.get("district_shifts", {})
        districts: list[dict[str, Any]] = []
        for district in state.get("districts", []):
            d_shift = district_shifts.get(district["id"], {})
            d_dem = float(district["dem_share"]) + national_dem_shift + float(state_shift.get("dem_shift", 0.0)) + float(d_shift.get("dem_shift", 0.0))
            d_rep = float(district["rep_share"]) + national_rep_shift + float(state_shift.get("rep_shift", 0.0)) + float(d_shift.get("rep_shift", 0.0))
            d_dem, d_rep = _normalize_two_party(d_dem, d_rep)
            districts.append(
                {
                    "id": district["id"],
                    "electoral_votes": int(district.get("electoral_votes", 1)),
                    "dem_share": d_dem,
                    "rep_share": d_rep,
                    "winner": _winner(d_dem, d_rep),
                }
            )

        result["at_large_evs"] = int(state.get("at_large_evs", 2))
        result["districts"] = districts

    return result


def allocateElectoralVotes(stateResult: dict[str, Any]) -> dict[str, int]:
    """Allocate electoral votes according to winner-take-all or district rules."""
    ev_dem = 0
    ev_rep = 0

    if stateResult.get("allocation") == "district":
        at_large = int(stateResult.get("at_large_evs", 2))
        if stateResult["winner"] == "dem":
            ev_dem += at_large
        else:
            ev_rep += at_large

        for district in stateResult.get("districts", []):
            ev = int(district.get("electoral_votes", 1))
            if district["winner"] == "dem":
                ev_dem += ev
            else:
                ev_rep += ev
    else:
        if stateResult["winner"] == "dem":
            ev_dem += int(stateResult["electoral_votes"])
        else:
            ev_rep += int(stateResult["electoral_votes"])

    return {"evDem": ev_dem, "evRep": ev_rep}


def computeNationalOutcome(stateResults: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute national EV and popular vote totals from resolved state results."""
    ev_dem = 0
    ev_rep = 0
    popular_dem = 0
    popular_rep = 0
    dem_states: list[str] = []
    rep_states: list[str] = []

    for state in stateResults:
        allocation = allocateElectoralVotes(state)
        ev_dem += allocation["evDem"]
        ev_rep += allocation["evRep"]
        popular_dem += int(state.get("popular_dem", 0))
        popular_rep += int(state.get("popular_rep", 0))

        if state["winner"] == "dem":
            dem_states.append(state["code"])
        else:
            rep_states.append(state["code"])

    winner = "dem" if ev_dem >= 270 and ev_dem >= ev_rep else "rep"
    ev_margin = ev_dem - ev_rep

    winning_states = dem_states if winner == "dem" else rep_states
    path_summary = {
        "winner": winner,
        "evMargin": ev_margin,
        "statesWon": winning_states,
        "statesNeededFor270": max(0, 270 - (ev_dem if winner == "dem" else ev_rep)),
    }

    return {
        "evDem": ev_dem,
        "evRep": ev_rep,
        "popularDem": popular_dem,
        "popularRep": popular_rep,
        "winner": winner,
        "winningPath": path_summary,
    }


def compute_electoral_outcome(scenario: dict[str, Any] | None = None) -> dict[str, Any]:
    """Convenience helper: apply scenario to all states and return full national outcome."""
    states = [applyScenarioToState(deepcopy(state), scenario) for state in STATE_BASELINES]
    national = computeNationalOutcome(states)
    return {"states": states, "national": national}
