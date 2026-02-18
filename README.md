# Electoral Monte Carlo Simulator

This project now includes a probabilistic Electoral College simulator. It models each state with:

- An expected Democratic vote share.
- A configurable state-specific standard deviation.
- A shared national error term plus state-specific error terms.
- A correlation control that tunes how much uncertainty is shared nationally.

The app runs seeded Monte Carlo simulations (default 10,000) for reproducible forecasts.

## Run the web app

```bash
python app.py
```

Then visit `http://localhost:8000`.

## Simulation outputs

The `/simulate` API returns:

- `winProbabilityDem` and `winProbabilityRep`
- EV percentile bands (5th/50th/95th) for both parties
- Distribution-ready EV histogram bins
- State win probabilities
- Tipping-point state frequencies
- Top battleground states sorted by closeness to 50/50

## UI features

- Histogram chart for Democratic EV outcomes
- Confidence interval cards
- Sortable battleground probability table
- Performance guardrail: simulation compute happens on the backend so the browser UI remains responsive

## Legacy endpoint

The CLI prints baseline totals, scenario totals, and the swing for Candidate A in votes and percentage points. The website displays the same results in a dashboard.

## Electoral College API

The Flask app now includes Electoral College modeling with deterministic state-by-state resolution and proper Maine/Nebraska district allocation.

### `POST /calculate`

In addition to demographic swing output, you can pass an optional `electoral_scenario` object and receive an `electoral` section containing state results and national totals:

- `evDem`, `evRep`
- `popularDem`, `popularRep`
- `winningPath` summary

### `POST /calculate-electoral`

Compute only Electoral College results. Request body supports:

- `electoral_scenario.national_dem_shift` / `national_rep_shift`
- `electoral_scenario.turnout_multiplier`
- `electoral_scenario.state_shifts[STATE_CODE]` overrides including district overrides for ME/NE
