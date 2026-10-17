import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bankers import Bankers, sample_manager


class TestBankers(unittest.TestCase):
    def test_1_initial_safety(self):
        safe, seq, _ = sample_manager().is_safe()
        self.assertTrue(safe)
        self.assertEqual(seq, [1, 3, 4, 0, 2])

    def test_2_need_matrix(self):
        self.assertEqual(sample_manager().need(0), [7, 4, 3])

    def test_3_valid_request(self):
        self.assertTrue(sample_manager().request(1, [1, 0, 2])["granted"])

    def test_4_not_enough_resources(self):
        m = sample_manager(); m.request(1, [1, 0, 2])   # Available becomes [2, 3, 0]
        r = m.request(4, [3, 3, 0])
        self.assertFalse(r["granted"]); self.assertEqual(r["code"], "NOT_AVAILABLE")

    def test_5_unsafe_request(self):
        m = sample_manager(); m.request(1, [1, 0, 2])
        r = m.request(0, [0, 2, 0])
        self.assertFalse(r["granted"]); self.assertEqual(r["code"], "UNSAFE")

    def test_6_exceeds_max(self):
        r = sample_manager().request(1, [5, 0, 0])
        self.assertFalse(r["granted"]); self.assertEqual(r["code"], "EXCEEDS_MAX")

    def test_7_rollback(self):
        m = sample_manager(); m.request(1, [1, 0, 2])
        before = (list(m.available), [r[:] for r in m.allocation])
        m.request(0, [0, 2, 0])
        self.assertEqual(before, (m.available, m.allocation))

    def test_8_deadlock_state(self):
        m = Bankers([0, 0], [[1, 1], [1, 1]], [[1, 0], [0, 1]])
        self.assertFalse(m.is_safe()[0])

    def test_9_invalid_input(self):
        with self.assertRaises(ValueError):
            Bankers([1], [[1]], [[2]])


if __name__ == "__main__":
    unittest.main()