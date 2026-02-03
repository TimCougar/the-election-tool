# Elastic Electoral Swing Calculator

This tool estimates how turnout changes within specific demographic groups shift the overall vote share between two candidates. It treats turnout changes as whole numbers and lets you specify an elasticity for each demographic: the percentage-point change in support for Candidate A for each 1% turnout change in that demographic.

## Website

Open `index.html` directly in a browser, or serve it locally if your browser blocks local file
requests.

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000/index.html`.

## CLI usage

```bash
python election_swing_calculator.py data/example.json
```

## How it works

For each demographic group:

- Start with the baseline voters and Candidate A support share.
- Apply the turnout delta (whole-number change in voters).
- Compute the turnout change percentage.
- Adjust Candidate A support using the elasticity value.
- Clamp support to the 0–100% range and compute votes.

The calculator then compares the scenario to the baseline to report the swing for Candidate A.

## Configuration format

```json
{
  "demographics": [
    {
      "name": "young_voters",
      "baseline_voters": 12000,
      "base_support_a": 55,
      "elasticity": 0.2
    }
  ],
  "turnout_delta": {
    "young_voters": 600
  }
}
```

### Field definitions

- `baseline_voters`: whole-number voter count for the baseline scenario.
- `base_support_a`: baseline support for Candidate A (0–100).
- `elasticity`: change in Candidate A support (percentage points) per 1% turnout change.
- `turnout_delta`: whole-number turnout change per demographic (positive or negative).

## Output

The CLI prints baseline totals, scenario totals, and the swing for Candidate A in votes and percentage points. The website displays the same results in a dashboard.
