"""Game rules and state for Detective Case Zero (no pygame in this file).

Keeping the rules separate from the drawing code means the whole game can be
tested without opening a window, and every teammate can read the logic alone.

Required course concepts used here:
    Bubble Sort    -> ranked_suspects()
    Insertion Sort -> examine()  (insert_sorted keeps the journal in time order)
    Selection Sort -> interview_queue()
    Tuple          -> self.pos, room coordinates, evidence times
    Set            -> self.collected, self.interviewed, self.confronted
    Dictionary     -> self.suspicion, ROOMS / SUSPECTS / EVIDENCE profiles
    Recursion      -> trace(), proof_for()  (via algorithms.trace_chain)
"""

from algorithms import bubble_sort, insert_sorted, selection_sort, trace_chain
from case_data import (
    ACTION_POINTS, CASE_INTRO, CLUE_LINKS, CULPRIT, DIRECTIONS, EVIDENCE,
    KEY_CLUE, MAX_ATTEMPTS, REQUIRED_CATEGORIES, ROOMS, SOLUTION_TEXT,
    START_POS, SUSPECTS,
)


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.pos = START_POS                    # tuple (x, y)
        self.ap = ACTION_POINTS                 # actions left before dawn
        self.attempts = MAX_ATTEMPTS            # accusations left
        self.collected = set()                  # unique evidence ids found
        self.journal = []                       # evidence ids, oldest event first
        self.suspicion = {sid: s["base_suspicion"] for sid, s in SUSPECTS.items()}
        self.interviewed = set()
        self.confronted = set()
        self.visited_rooms = {START_POS}
        self.selected_clue = None
        self.last_chain = []
        self.messages = []
        self.status = "playing"                 # playing / won / lost
        self.final_call = False                 # True once the actions run out
        self.result_title = ""
        self.result_text = ""
        self.score = 0
        self.proof_chain = []
        self.say(CASE_INTRO)

    # ------------------------------------------------------------------ helpers
    def say(self, text):
        self.messages.append(text)
        del self.messages[:-40]

    def _spend(self, cost=1):
        self.ap = max(0, self.ap - cost)
        if self.ap == 0 and self.status == "playing" and not self.final_call:
            self.final_call = True
            self.say("Dawn breaks and the police are at the door. "
                     "You have one chance left: make your final accusation.")

    @property
    def room(self):
        return ROOMS[self.pos]

    def name_of(self, clue_id):
        return EVIDENCE[clue_id]["name"]

    # ----------------------------------------------------------------- movement
    def neighbours(self):
        """Return {direction: room position} for every room you can walk into."""
        result = {}
        for direction, (dx, dy) in DIRECTIONS.items():
            target = (self.pos[0] + dx, self.pos[1] + dy)
            if target in ROOMS:
                result[direction] = target
        return result

    def move(self, direction):
        target = self.neighbours().get(direction)
        if target is None:
            return False
        return self.move_to(target)

    def move_to(self, target):
        if self.status != "playing" or self.final_call:
            return False
        if target not in self.neighbours().values():
            return False
        self.pos = target
        first_visit = target not in self.visited_rooms
        self.visited_rooms.add(target)
        text = f"You enter the {self.room['name']}. {self.room['blurb']}"
        if self._unfound_here():
            text += " Something here deserves a closer look."
        elif first_visit:
            text += " You find nothing else of interest."
        self.say(text)
        self._spend(1)
        return True

    def _unfound_here(self):
        return [e for e, ev in EVIDENCE.items()
                if ev["room"] == self.pos and e not in self.collected]

    # ------------------------------------------------------------------ actions
    def actions(self):
        """Everything you can do in the current room, in display order."""
        acts = []
        for eid, ev in EVIDENCE.items():
            if ev["room"] != self.pos:
                continue
            if eid in self.collected:
                acts.append({"kind": "select", "id": eid, "done": True,
                             "label": f"{ev['name']}  (collected)"})
            else:
                acts.append({"kind": "examine", "id": eid, "done": False,
                             "label": f"Search {ev['spot']}"})
        for sid, s in SUSPECTS.items():
            if s["room"] != self.pos:
                continue
            if sid not in self.interviewed:
                label, done = f"Interview {s['name']}", False
            elif self.can_confront(sid):
                label, done = f"Confront {s['name']}  (new evidence!)", False
            else:
                label, done = f"Talk to {s['name']}  (nothing new)", True
            acts.append({"kind": "interview", "id": sid, "done": done, "label": label})
        return acts

    def examine(self, clue_id):
        ev = EVIDENCE.get(clue_id)
        if self.status != "playing" or self.final_call:
            return False
        if ev is None or ev["room"] != self.pos or clue_id in self.collected:
            return False
        self.collected.add(clue_id)
        # Insertion Sort step: slot the new clue into the time-ordered journal.
        insert_sorted(self.journal, clue_id, key=lambda c: EVIDENCE[c]["time"])
        for sid, delta in ev["suspicion"].items():
            self.suspicion[sid] = max(0, self.suspicion[sid] + delta)
        self.selected_clue = clue_id
        self.say(f"Found: {ev['name']}. {ev['desc']}")
        self._spend(1)
        return True

    def can_confront(self, sid):
        s = SUSPECTS[sid]
        return (sid in self.interviewed and sid not in self.confronted
                and s["contradicted_by"] in self.collected)

    def interview(self, sid):
        s = SUSPECTS.get(sid)
        if self.status != "playing" or self.final_call:
            return False
        if s is None or s["room"] != self.pos:
            return False
        if sid not in self.interviewed:
            self.interviewed.add(sid)
            self.say(f'{s["name"]} ({s["role"]}): "{s["alibi"]}"')
            self.say(f'{s["short"]} adds: "{s["tip"]}"')
            self._spend(1)
        elif self.can_confront(sid):
            self.confronted.add(sid)
            clue = self.name_of(s["contradicted_by"])
            self.suspicion[sid] += s["slip_suspicion"]
            self.say(f'You show {s["short"]} the {clue}. "{s["slip"]}"')
            self._spend(1)
        else:
            self.say(f'{s["short"]} has nothing more to say. Fresh evidence might '
                     f"change that.")
        return True

    # ---------------------------------------------------------- sorted displays
    def ranked_suspects(self):
        """Suspect ids ranked from most to least suspicious (Bubble Sort)."""
        return bubble_sort(list(SUSPECTS), key=lambda s: self.suspicion[s], reverse=True)

    def interview_queue(self):
        """Not-yet-interviewed suspects, most suspicious first (Selection Sort)."""
        waiting = [s for s in SUSPECTS if s not in self.interviewed]
        return selection_sort(waiting, key=lambda s: self.suspicion[s], reverse=True)

    def ready_to_confront(self):
        return [s for s in SUSPECTS if self.can_confront(s)]

    # ---------------------------------------------------------------- recursion
    def select_clue(self, clue_id):
        if clue_id in self.collected:
            self.selected_clue = clue_id
            self.say(f"{self.name_of(clue_id)}: {EVIDENCE[clue_id]['desc']}")

    def trace(self, start=None):
        """Follow the clue web outward from a clue (Recursion)."""
        if start is None:
            start = self.selected_clue
        if start is None and KEY_CLUE in self.collected:
            start = KEY_CLUE
        if start is None and self.journal:
            start = self.journal[0]
        if start is None:
            self.say("You have no evidence to trace yet. Search the rooms first.")
            return []
        chain = trace_chain(start, CLUE_LINKS, self.collected)
        self.last_chain = chain
        names = " -> ".join(self.name_of(c) for c in chain)
        pointed = {EVIDENCE[c]["suspect"] for c in chain if EVIDENCE[c]["suspect"]}
        who = ", ".join(SUSPECTS[s]["short"] for s in selection_sort(list(pointed))) \
            or "no one yet"
        self.say(f"Tracing from the {self.name_of(start)}: {names}. "
                 f"{len(chain)} linked clue(s). Points toward: {who}.")
        return chain

    def proof_for(self, sid):
        """Trace the murder weapon's clue chain and see what it proves about `sid`.

        Returns (chain, missing) where `missing` is the set of required
        categories (motive / means / opportunity) the chain does not yet prove.
        """
        chain = trace_chain(KEY_CLUE, CLUE_LINKS, self.collected)
        proven = {EVIDENCE[c]["category"] for c in chain if EVIDENCE[c]["suspect"] == sid}
        return chain, REQUIRED_CATEGORIES - proven

    # --------------------------------------------------------------- accusation
    def accuse(self, sid):
        """Accuse a suspect. Returns 'win', 'wrong' or 'no_proof'."""
        if self.status != "playing" or sid not in SUSPECTS:
            return None
        name = SUSPECTS[sid]["name"]
        if sid != CULPRIT:
            outcome = "wrong"
            self.say(f"You accuse {name}, but the facts do not fit. The real killer "
                     f"is still free.")
        else:
            chain, missing = self.proof_for(sid)
            if missing:
                outcome = "no_proof"
                lacking = ", ".join(selection_sort(list(missing)))
                if KEY_CLUE not in self.collected:
                    lacking += " (you have not even secured the murder weapon)"
                self.say(f"You accuse {name}, and your instinct is right, but the "
                         f"case falls apart in court. Your clue chain does not "
                         f"prove: {lacking}.")
            else:
                self._win(chain)
                return "win"
        self.attempts -= 1
        if self.attempts <= 0 or self.final_call:
            self._lose()
        else:
            self.say(f"Accusations left: {self.attempts}.")
        return outcome

    def _win(self, chain):
        self.status = "won"
        self.proof_chain = chain
        self.score = 500 + 50 * len(self.collected) + 10 * self.ap + 150 * self.attempts
        self.result_title = "CASE CLOSED"
        self.result_text = (f"You arrested {SUSPECTS[CULPRIT]['name']}. "
                            f"{SOLUTION_TEXT}")

    def _lose(self):
        self.status = "lost"
        self.result_title = "THE CASE GOES COLD"
        reason = ("You ran out of accusations." if self.attempts <= 0
                  else "Time ran out.")
        self.result_text = (f"{reason} The killer was {SUSPECTS[CULPRIT]['name']}. "
                            f"{SOLUTION_TEXT}")
