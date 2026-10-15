"""Headless tests for the game rules (no pygame window needed)."""
import unittest

from case_data import ACTION_POINTS, CLUE_LINKS, EVIDENCE, MAX_ATTEMPTS, ROOMS, SUSPECTS
from game_state import Game


def walk(game, *directions):
    for d in directions:
        assert game.move(d), f"could not move {d} from {game.pos}"


def search_all_here(game):
    for eid in [e for e, ev in EVIDENCE.items() if ev["room"] == game.pos]:
        game.examine(eid)


class DataTests(unittest.TestCase):
    def test_every_evidence_room_exists(self):
        for eid, ev in EVIDENCE.items():
            self.assertIn(ev["room"], ROOMS, eid)

    def test_every_suspect_room_exists(self):
        for sid, s in SUSPECTS.items():
            self.assertIn(s["room"], ROOMS, sid)
            self.assertIn(s["contradicted_by"], EVIDENCE, sid)

    def test_clue_graph_is_two_way(self):
        for a, links in CLUE_LINKS.items():
            for b in links:
                self.assertIn(a, CLUE_LINKS[b])


class MovementTests(unittest.TestCase):
    def test_walls_block_movement_and_cost_nothing(self):
        g = Game()
        self.assertFalse(g.move("left") and g.move("left"))  # Foyer -> Cellar -> wall
        before = g.ap
        self.assertFalse(g.move("left"))
        self.assertEqual(g.ap, before)

    def test_move_costs_one_action(self):
        g = Game()
        g.move("up")
        self.assertEqual(g.pos, (1, 1))
        self.assertEqual(g.ap, ACTION_POINTS - 1)


class EvidenceTests(unittest.TestCase):
    def test_collecting_adds_to_set_and_ordered_journal(self):
        g = Game()
        walk(g, "up")
        search_all_here(g)                       # Study: E01 19:40, E02 21:15, E03 21:20
        self.assertEqual(g.collected, {"E01", "E02", "E03"})
        self.assertEqual(g.journal, ["E01", "E02", "E03"])

    def test_journal_stays_chronological_across_rooms(self):
        g = Game()
        search_all_here(g)                       # Foyer: E10 21:00, E06 21:35
        walk(g, "up", "left")                    # Library: E08 16:00, E07 17:30
        search_all_here(g)
        times = [EVIDENCE[e]["time"] for e in g.journal]
        self.assertEqual(times, sorted(times))
        self.assertEqual(g.journal[0], "E08")

    def test_no_duplicate_collection(self):
        g = Game()
        walk(g, "up")
        g.examine("E01")
        ap = g.ap
        self.assertFalse(g.examine("E01"))
        self.assertEqual(g.ap, ap)
        self.assertEqual(len(g.collected), 1)

    def test_cannot_examine_clue_in_other_room(self):
        g = Game()
        self.assertFalse(g.examine("E04"))       # E04 is in the Garden

    def test_suspicion_changes_and_never_goes_negative(self):
        g = Game()
        search_all_here(g)                       # Hale alibi -20 from base 15
        self.assertEqual(g.suspicion["hale"], 0)


class RankingTests(unittest.TestCase):
    def test_ranked_suspects_is_descending(self):
        g = Game()
        order = g.ranked_suspects()
        scores = [g.suspicion[s] for s in order]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertEqual(order[0], "vera")       # highest base suspicion at the start

    def test_interview_queue_shrinks_and_is_descending(self):
        g = Game()
        queue = g.interview_queue()
        self.assertEqual(len(queue), len(SUSPECTS))
        scores = [g.suspicion[s] for s in queue]
        self.assertEqual(scores, sorted(scores, reverse=True))
        search_all_here(g)
        g.interview("hale")                      # Hale is in the Foyer
        self.assertNotIn("hale", g.interview_queue())


class InterviewTests(unittest.TestCase):
    def test_interview_then_confront(self):
        g = Game()
        search_all_here(g)                       # Foyer: finds E06 and E10
        g.interview("hale")                      # E09 not found yet
        self.assertFalse(g.can_confront("hale"))
        before = g.ap
        g.interview("hale")                      # nothing new: free
        self.assertEqual(g.ap, before)

    def test_confront_after_finding_contradiction(self):
        g = Game()
        walk(g, "right", "up")                   # Kitchen -> Dining Room
        g.interview("pike")
        walk(g, "down")                          # Kitchen
        g.examine("E05")
        walk(g, "up")                            # Dining Room
        self.assertTrue(g.can_confront("pike"))
        score = g.suspicion["pike"]
        g.interview("pike")
        self.assertIn("pike", g.confronted)
        self.assertEqual(g.suspicion["pike"], score + SUSPECTS["pike"]["slip_suspicion"])


class TraceTests(unittest.TestCase):
    def test_trace_with_no_evidence(self):
        g = Game()
        self.assertEqual(g.trace(), [])

    def test_disconnected_thread_does_not_reach_murder_weapon(self):
        g = Game()
        walk(g, "up", "left")                    # Library
        search_all_here(g)                       # E07 + E08, a separate thread
        chain = g.trace("E07")
        self.assertEqual(sorted(chain), ["E07", "E08"])


def build_winning_game():
    g = Game()
    search_all_here(g)                           # Foyer: E10, E06
    walk(g, "up")
    search_all_here(g)                           # Study: E01, E02, E03
    walk(g, "up")
    search_all_here(g)                           # Garden: E04, E12
    return g


class AccusationTests(unittest.TestCase):
    def test_correct_accusation_with_proof_wins(self):
        g = build_winning_game()
        self.assertEqual(g.proof_for("crane")[1], set())
        self.assertEqual(g.accuse("crane"), "win")
        self.assertEqual(g.status, "won")
        self.assertGreater(g.score, 0)

    def test_correct_suspect_without_proof_costs_an_attempt(self):
        g = Game()
        walk(g, "up")
        g.examine("E02")                         # only the weapon, nothing proving Crane
        self.assertEqual(g.accuse("crane"), "no_proof")
        self.assertEqual(g.status, "playing")
        self.assertEqual(g.attempts, MAX_ATTEMPTS - 1)
        self.assertEqual(g.proof_for("crane")[1], {"motive", "means", "opportunity"})

    def test_missing_murder_weapon_means_no_proof(self):
        g = Game()
        walk(g, "up", "up")
        search_all_here(g)                       # Garden clues but no brandy glass
        self.assertEqual(g.accuse("crane"), "no_proof")

    def test_wrong_accusations_end_the_game(self):
        g = build_winning_game()
        for _ in range(MAX_ATTEMPTS):
            self.assertEqual(g.accuse("vera"), "wrong")
        self.assertEqual(g.status, "lost")
        self.assertIn("Crane", g.result_text)

    def test_actions_run_out_forces_final_accusation(self):
        g = Game()
        for i in range(ACTION_POINTS):
            g.move("up" if i % 2 == 0 else "down")
        self.assertEqual(g.ap, 0)
        self.assertTrue(g.final_call)
        self.assertFalse(g.move("up"))           # no more moves
        self.assertEqual(g.accuse("crane"), "no_proof")
        self.assertEqual(g.status, "lost")       # final call: no second chances

    def test_restart_resets_everything(self):
        g = build_winning_game()
        g.accuse("crane")
        g.reset()
        self.assertEqual(g.status, "playing")
        self.assertEqual(g.collected, set())
        self.assertEqual(g.journal, [])
        self.assertEqual(g.ap, ACTION_POINTS)


if __name__ == "__main__":
    unittest.main()
