import unittest

from electoral_college import (
    STATE_BASELINES,
    allocateElectoralVotes,
    applyScenarioToState,
    computeNationalOutcome,
)


class ElectoralCollegeTests(unittest.TestCase):
    def test_dataset_includes_all_states_and_dc(self):
        self.assertEqual(51, len(STATE_BASELINES))
        codes = {state["code"] for state in STATE_BASELINES}
        self.assertIn("DC", codes)
        self.assertIn("ME", codes)
        self.assertIn("NE", codes)

    def test_apply_scenario_to_state_adjusts_shares(self):
        az = next(state for state in STATE_BASELINES if state["code"] == "AZ")
        result = applyScenarioToState(
            az,
            {
                "national_dem_shift": 1.0,
                "state_shifts": {"AZ": {"dem_shift": 1.0, "rep_shift": -1.0}},
            },
        )
        self.assertGreater(result["dem_share"], result["rep_share"])
        self.assertEqual("dem", result["winner"])

    def test_allocate_electoral_votes_winner_take_all(self):
        result = {
            "allocation": "winner_take_all",
            "electoral_votes": 11,
            "winner": "rep",
        }
        allocation = allocateElectoralVotes(result)
        self.assertEqual({"evDem": 0, "evRep": 11}, allocation)

    def test_allocate_electoral_votes_district(self):
        result = {
            "allocation": "district",
            "winner": "dem",
            "at_large_evs": 2,
            "districts": [
                {"id": "X-1", "electoral_votes": 1, "winner": "dem"},
                {"id": "X-2", "electoral_votes": 1, "winner": "rep"},
            ],
        }
        allocation = allocateElectoralVotes(result)
        self.assertEqual({"evDem": 3, "evRep": 1}, allocation)

    def test_compute_national_outcome(self):
        states = [
            {
                "code": "A",
                "winner": "dem",
                "allocation": "winner_take_all",
                "electoral_votes": 270,
                "popular_dem": 100,
                "popular_rep": 90,
            },
            {
                "code": "B",
                "winner": "rep",
                "allocation": "winner_take_all",
                "electoral_votes": 10,
                "popular_dem": 20,
                "popular_rep": 50,
            },
        ]
        national = computeNationalOutcome(states)
        self.assertEqual(270, national["evDem"])
        self.assertEqual(10, national["evRep"])
        self.assertEqual(120, national["popularDem"])
        self.assertEqual(140, national["popularRep"])
        self.assertEqual("dem", national["winner"])


if __name__ == "__main__":
    unittest.main()
