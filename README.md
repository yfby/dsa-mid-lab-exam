# Detective Case Zero

A single-case detective game built with **Python + pygame-ce**.
Midterm Lab Exam project, **Group 9**.

You investigate *The Blackwood Manor Poisoning*: search seven rooms, interview five
suspects, collect evidence, and name the killer before dawn. Naming the right suspect is
not enough. You must **prove motive, means and opportunity** with a chain of clues.

## Team

| Member | Primary role | Main code contribution |
|---|---|---|
| Bryan Nino C. Behiga | Team coordinator and integrator | _e.g. `game_state.py` integration, `ui.py` scene flow_ |
| Harvey Kyle T. Ybanez| Gameplay programmer | _e.g. `Game.accuse`, win/loss rules, action points_ |
| Gian L. Edralin | Data structures and algorithms programmer | _e.g. `algorithms.py`_ |
| Prince Heart C. Go | Interface and asset designer | _e.g. `ui.py` drawing code_ |
| Sam Kerby V. Bernales | QA, documentation and release lead | _e.g. `tests/`, this README_ |

*(Fill in your real names and the files/functions each person wrote.)*

## Setup and launch

- **Framework:** pygame-ce 2.5.x
- **Python:** 3.13 (see `.python-version`)
- **Package manager:** [uv](https://docs.astral.sh/uv/)

```bash
git clone <your-repo-url>
cd detective-case-zero
uv sync            # installs pygame-ce into .venv
uv run main.py     # launches the game
```

Without uv: `pip install -r requirements.txt` then `python main.py`.

The window is resizable. The game scales to fit smaller screens.

## Objective and rules

- Seven rooms are linked on a floor plan. You start in the **Foyer**.
- You have **70 actions**. Moving, searching a spot, and interviewing each cost 1.
  Reading a clue and tracing a chain are free.
- Each clue changes the **suspicion score** of the people it points to. Some clues
  *lower* suspicion (alibis). Some are red herrings.
- Interview each suspect to hear their alibi and a tip. When you later find evidence that
  contradicts their story, **confront** them for extra information.
- Press **Trace** to follow a clue's links through your journal. A clue only links to
  clues you have already found.
- **Accuse** a suspect. You have **3 accusations**.
  - Wrong suspect: you lose an accusation.
  - Right suspect without enough proof: the case collapses and you lose an accusation.
    The game tells you which of *motive / means / opportunity* is missing.
  - Right suspect with a chain proving all three: **you win**.
- If the 70 actions run out, dawn breaks and you get **one forced final accusation**.
- Win or lose, press **R** to play again.

## Controls

| Key / mouse | Action |
|---|---|
| Arrow keys or WASD | Move to the neighbouring room |
| Click a highlighted room | Move there |
| 1-9 or click a row | Search a spot / interview / confront / re-read a clue |
| Click a journal entry | Read that clue again |
| T or the Trace button | Trace the clue chain from the selected clue |
| J or the Accuse button | Open the accusation screen (then 1-5 or click) |
| Esc | Pause (Resume / Restart / Quit) |
| R / Q | Restart / quit (on pause and end screens) |

## Feature map (required course concepts)

Each concept changes how the game plays. Nothing here uses the built-in `sort()` or
`sorted()`. The sorting functions are written by hand in `algorithms.py`.

| Concept | Where it is written | Where the game uses it | What the player sees |
|---|---|---|---|
| **Bubble Sort** | `algorithms.py` -> `bubble_sort()` | `game_state.py` -> `Game.ranked_suspects()` | **Suspect Board** ranks suspects by suspicion, highest first. It reorders live as clues arrive. |
| **Insertion Sort** | `algorithms.py` -> `insert_sorted()` (the insertion step) and `insertion_sort()` | `game_state.py` -> `Game.examine()` | **Case Journal**: each new clue is inserted into the already ordered list by the time of the event, not by when you found it. |
| **Selection Sort** | `algorithms.py` -> `find_extreme_index()` and `selection_sort()` | `game_state.py` -> `Game.interview_queue()` | **Next Interview** panel selects the most suspicious suspect you have not questioned yet. |
| **Tuple** | `case_data.py` -> `ROOMS` keys `(x, y)`, `START_POS`, `DIRECTIONS` `(dx, dy)`, evidence `"time": (hour, minute)` | `Game.pos`, `Game.neighbours()`, `Game.move_to()`, journal ordering key | Room coordinates on the floor plan, movement, and the clock times in the journal. |
| **Set** | `game_state.py` -> `Game.collected`, `Game.interviewed`, `Game.confronted`; `case_data.py` -> `REQUIRED_CATEGORIES` | `examine()` (unique evidence), `trace_chain()` (which clues are unlocked), `proof_for()` (set difference: required minus proven) | Evidence is never counted twice. Accusation feedback names the missing categories. |
| **Dictionary** | `case_data.py` -> `ROOMS`, `SUSPECTS`, `EVIDENCE`, `CLUE_LINKS`; `Game.suspicion` | Everywhere: suspect profiles and alibis, evidence data, live suspicion scores | Interviews, clue text, suspicion bars. |
| **Recursion** | `algorithms.py` -> `trace_chain()` | `Game.trace()` (Trace button) and `Game.proof_for()` (accusation) | Tracing follows linked clues through your journal. The win condition depends on the traced chain. |

### Recursion details

`trace_chain(node, graph, unlocked, visited)` has two **base cases**:

1. `node in visited`: already traced, so stop (prevents loops).
2. `node not in unlocked`: the clue has not been found, so the chain breaks here.

Otherwise it adds the clue to `visited` and calls itself on each linked clue. Every call
either adds one new clue or returns immediately, so the recursion is bounded by the
14 clues in the case. It is used for a game decision (the proof check), not for animation
or the main loop.

### Small traces to practice for the defense

**Bubble Sort** on suspicion scores `[50, 105, 5]`, largest first:
pass 1 compares (50, 105) and swaps, giving `[105, 50, 5]`; then compares (50, 5), no
swap. Pass 2 makes no swaps, so it stops. Result `[105, 50, 5]`.

**Insertion** of a clue at 21:05 into journal times `[16:00, 19:40, 21:15]`:
21:15 > 21:05, so it shifts right; 19:40 < 21:05, so the loop stops. The clue lands in
the gap: `[16:00, 19:40, 21:05, 21:15]`.

**Selection** on `[("pike", 15), ("vera", 20), ("crane", 10)]`, largest first:
position 0: scan all, pick vera (20), swap with position 0. Position 1: scan the
remaining two, pick pike (15), already in place. Done.

**Recursion** with found clues `{E02, E04, E01}`: `trace_chain("E02")` visits E02, then
its link E04, then E04's link E01. E01's only link is E04, which is already visited, so
that call returns (base case 1). E02's other links (E03, E05, E13) are not found, so they
return immediately (base case 2). Chain: `E02 -> E04 -> E01`.

## A winning route (for demos)

Start in the Foyer. The minimum proof needs five clues:

1. Foyer: search the coat closet (Muddy Dress Shoes).
2. Move up to the **Study**: search all three spots (note, glass, footprints).
3. Move up to the **Garden**: search the flowerbed (Digitalis Vial).
4. Press **J**, choose **Dr. Silas Crane**.

Why it works: tracing from the Poisoned Brandy Glass reaches the Digitalis Vial (means),
the Blackmail Note via the vial (motive), and the Muddy Shoes via the footprints
(opportunity). Interview everyone and search all rooms for the full story and a higher score.

## Tests

```bash
uv run python -m unittest discover -s tests -t . -v
```

| Test file | What it covers |
|---|---|
| `tests/test_algorithms.py` | All three sorts on an **empty list**, a **one-item list** and a **short game-data list**, plus ascending/descending, stability, input not mutated, `insert_sorted`, and recursion base cases and cycles |
| `tests/test_game.py` | Movement and walls, evidence set + chronological journal, suspicion, rankings, interviews and confrontation, tracing, win / no-proof / wrong / out-of-actions, restart |

## Project layout

```
main.py          entry point
ui.py            pygame-ce drawing and input
game_state.py    game rules and state (no pygame)
case_data.py     rooms, suspects, evidence, clue links
algorithms.py    bubble / insertion / selection sort + recursive trace
tests/           unit tests
```

## Credits and assets

No external art, sound or font files are used. Everything is drawn with pygame
primitives, and text uses pygame's built-in default font. All story text, names and
characters are original to this project.

