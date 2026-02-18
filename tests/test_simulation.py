import unittest

from simulation import SimulationConfig, StateModel, run_simulation


class SimulationTests(unittest.TestCase):
    def test_seeded_runs_are_reproducible(self):
        states = [
            StateModel("A", 10, 52.0, 3.0),
            StateModel("B", 10, 48.0, 3.0),
            StateModel("C", 10, 50.0, 3.0),
        ]
        config = SimulationConfig(n_simulations=500, seed=99, national_stddev=2.0, correlation=0.6)

        first = run_simulation(states, config)
        second = run_simulation(states, config)

        self.assertEqual(first["winProbabilityDem"], second["winProbabilityDem"])
        self.assertEqual(first["evPercentiles"], second["evPercentiles"])
        self.assertEqual(first["evHistogram"], second["evHistogram"])

    def test_probabilities_sum_to_one(self):
        states = [
            StateModel("A", 55, 55.0, 1.0),
            StateModel("B", 45, 45.0, 1.0),
        ]
        config = SimulationConfig(n_simulations=400, seed=7, national_stddev=1.5, correlation=0.5)

        result = run_simulation(states, config)

        total = result["winProbabilityDem"] + result["winProbabilityRep"]
        self.assertAlmostEqual(total, 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
