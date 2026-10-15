"""Tests for the hand-written sorts and the recursive clue tracer.

Run from the project root:
    uv run python -m unittest discover -s tests -t . -v

The built-in sorted() is used HERE ONLY, as an independent answer to compare
against. The game itself never calls sort() or sorted().
"""
import unittest

from algorithms import (
    bubble_sort, insert_sorted, insertion_sort, selection_sort, trace_chain,
)

SORTS = {
    "bubble": bubble_sort,
    "insertion": insertion_sort,
    "selection": selection_sort,
}

# A short list of game data: (suspect, suspicion score)
SUSPECT_SCORES = [("crane", 105), ("pike", 55), ("vera", 50), ("hale", 25), ("finch", 5)]
UNSORTED_SCORES = [("vera", 50), ("crane", 105), ("finch", 5), ("hale", 25), ("pike", 55)]


class SortTests(unittest.TestCase):
    def test_empty_list(self):
        for name, sort in SORTS.items():
            with self.subTest(sort=name):
                self.assertEqual(sort([]), [])

    def test_one_item(self):
        for name, sort in SORTS.items():
            with self.subTest(sort=name):
                self.assertEqual(sort([42]), [42])

    def test_short_game_data_descending(self):
        for name, sort in SORTS.items():
            with self.subTest(sort=name):
                result = sort(UNSORTED_SCORES, key=lambda s: s[1], reverse=True)
                self.assertEqual(result, SUSPECT_SCORES)

    def test_short_game_data_ascending(self):
        for name, sort in SORTS.items():
            with self.subTest(sort=name):
                result = sort(UNSORTED_SCORES, key=lambda s: s[1])
                self.assertEqual(result, list(reversed(SUSPECT_SCORES)))

    def test_matches_builtin_on_many_lists(self):
        samples = [
            [3, 1, 2], [1, 2, 3], [3, 2, 1], [5, 5, 5], [2, 1, 2, 1],
            [9, -4, 0, 7, 7, -4, 12, 1],
            [(21, 15), (19, 40), (21, 5), (16, 0)],   # (hour, minute) tuples
        ]
        for data in samples:
            for name, sort in SORTS.items():
                with self.subTest(sort=name, data=data):
                    self.assertEqual(sort(data), sorted(data))
                    self.assertEqual(sort(data, reverse=True),
                                     sorted(data, reverse=True))

    def test_input_list_is_not_changed(self):
        for name, sort in SORTS.items():
            with self.subTest(sort=name):
                data = [3, 1, 2]
                sort(data)
                self.assertEqual(data, [3, 1, 2])

    def test_insertion_and_bubble_are_stable(self):
        pairs = [("a", 1), ("b", 1), ("c", 0), ("d", 1)]
        expected = [("c", 0), ("a", 1), ("b", 1), ("d", 1)]
        self.assertEqual(bubble_sort(pairs, key=lambda p: p[1]), expected)
        self.assertEqual(insertion_sort(pairs, key=lambda p: p[1]), expected)


class InsertSortedTests(unittest.TestCase):
    def test_insert_into_empty(self):
        self.assertEqual(insert_sorted([], 5), [5])

    def test_insert_at_each_position(self):
        self.assertEqual(insert_sorted([2, 4, 6], 1), [1, 2, 4, 6])
        self.assertEqual(insert_sorted([2, 4, 6], 5), [2, 4, 5, 6])
        self.assertEqual(insert_sorted([2, 4, 6], 9), [2, 4, 6, 9])

    def test_journal_style_time_tuples(self):
        journal = [(16, 0), (19, 40), (21, 15)]
        insert_sorted(journal, (21, 5))
        self.assertEqual(journal, [(16, 0), (19, 40), (21, 5), (21, 15)])


class TraceChainTests(unittest.TestCase):
    GRAPH = {"A": ["B", "C"], "B": ["A", "D"], "C": ["A"], "D": ["B", "E"], "E": ["D"]}

    def test_nothing_found_returns_empty(self):
        self.assertEqual(trace_chain("A", self.GRAPH, set()), [])

    def test_single_found_clue(self):
        self.assertEqual(trace_chain("A", self.GRAPH, {"A"}), ["A"])

    def test_follows_links_through_found_clues_only(self):
        found = {"A", "B", "D"}          # C and E not found: chain skips them
        self.assertEqual(sorted(trace_chain("A", self.GRAPH, found)), ["A", "B", "D"])

    def test_chain_breaks_at_missing_clue(self):
        found = {"A", "D", "E"}          # B missing, so D and E are unreachable from A
        self.assertEqual(trace_chain("A", self.GRAPH, found), ["A"])

    def test_cycles_terminate(self):
        loop = {"A": ["B"], "B": ["C"], "C": ["A"]}
        self.assertEqual(trace_chain("A", loop, {"A", "B", "C"}), ["A", "B", "C"])

    def test_calls_do_not_share_hidden_state(self):
        self.assertEqual(trace_chain("A", self.GRAPH, {"A"}), ["A"])
        self.assertEqual(trace_chain("D", self.GRAPH, {"D"}), ["D"])


if __name__ == "__main__":
    unittest.main()
