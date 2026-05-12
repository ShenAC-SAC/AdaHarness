import unittest

from adaharness.evals.metrics import HarnessMetrics, compute_relative_metrics


class MetricsTests(unittest.TestCase):
    def test_relative_metrics_use_bare_baseline(self) -> None:
        metrics = compute_relative_metrics(
            [
                HarnessMetrics(
                    "bare",
                    success_rate=0.5,
                    estimated_cost=1.0,
                    estimated_latency=1.0,
                    retry_count=0,
                ),
                HarnessMetrics(
                    "adaptive",
                    success_rate=0.8,
                    estimated_cost=1.3,
                    estimated_latency=1.2,
                    retry_count=1,
                ),
            ]
        )

        adaptive = metrics[1]

        self.assertEqual(round(adaptive.harness_lift, 2), 0.3)
        self.assertEqual(adaptive.harness_tax, 1.3)
        self.assertLess(adaptive.minimal_effective_harness_score, adaptive.success_rate)
