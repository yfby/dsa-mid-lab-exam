"""Static case data for Detective Case Zero: "The Blackwood Manor Poisoning".

Required course concepts that live in this file:
    TUPLES      - room coordinates (x, y), evidence times (hour, minute),
                  movement directions (dx, dy)
    DICTIONARIES - ROOMS, SUSPECTS and EVIDENCE profiles, CLUE_LINKS graph
    SETS        - REQUIRED_CATEGORIES (what a case needs to be proven)
"""

CASE_TITLE = "The Blackwood Manor Poisoning"

CASE_INTRO = (
    "Lord Alaric Blackwood was found slumped in his study at 21:45, a brandy glass "
    "beside him. Five people were in the manor that night. Search the rooms, "
    "question the guests, and name the killer before dawn. A hunch is not enough: "
    "you must be able to PROVE motive, means and opportunity."
)

SOLUTION_TEXT = (
    "Dr. Silas Crane had been forging heart-medicine prescriptions. When Lord Alaric "
    "threatened to expose him, Crane laced the brandy with digitalis, slipped out "
    "through the French doors and threw the empty vial into the roses."
)

START_POS = (1, 2)  # tuple: the Foyer
ACTION_POINTS = 50  # moves, searches and interviews each cost 1
MAX_ATTEMPTS = 3  # wrong accusations allowed before the case goes cold
CULPRIT = "crane"
KEY_CLUE = "E02"  # the murder weapon: every proof chain starts here
REQUIRED_CATEGORIES = {"motive", "means", "opportunity"}  # set

# Movement directions as (dx, dy) tuples.
DIRECTIONS = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}

# Rooms are keyed by their (x, y) grid coordinate tuple.
ROOMS = {
    (1, 0): {
        "name": "Garden",
        "blurb": "Cold night air and damp flowerbeds beneath the study windows.",
    },
    (0, 1): {
        "name": "Library",
        "blurb": "Leather-bound books and a fireplace gone cold.",
    },
    (1, 1): {
        "name": "Study",
        "blurb": "The crime scene. Lord Blackwood's armchair is still warm.",
    },
    (2, 1): {
        "name": "Dining Room",
        "blurb": "A long table, still set for the dinner party.",
    },
    (0, 2): {"name": "Wine Cellar", "blurb": "Dusty racks and a single swinging bulb."},
    (1, 2): {
        "name": "Foyer",
        "blurb": "The grand entrance hall, with a telephone on the hall table.",
    },
    (2, 2): {"name": "Kitchen", "blurb": "Copper pots and the smell of burnt sugar."},
}

# Suspect profiles. `contradicted_by` is the evidence that breaks their alibi.
SUSPECTS = {
    "crane": {
        "name": "Dr. Silas Crane",
        "short": "Dr. Crane",
        "initial": "C",
        "role": "Family physician",
        "room": (1, 0),
        "color": (110, 170, 220),
        "base_suspicion": 10,
        "alibi": "I left the study before nine and spent the evening smoking in the "
        "garden. I never went back inside.",
        "tip": "Mr. Pike stormed out of the dining room tonight, waving a letter about "
        "his dismissal.",
        "contradicted_by": "E06",
        "slip": "All right! I did go back through the French doors to check on Alaric. "
        "He was already slumped in his chair. I panicked and ran.",
        "slip_suspicion": 10,
    },
    "pike": {
        "name": "Harlan Pike",
        "short": "Mr. Pike",
        "initial": "P",
        "role": "Butler",
        "room": (2, 1),
        "color": (200, 160, 100),
        "base_suspicion": 15,
        "alibi": "I was polishing the silver in the pantry from nine till ten. "
        "Ask Mrs. Finch.",
        "tip": "Miss Vera was quarrelling with his lordship about the will. "
        "You may find papers in the library.",
        "contradicted_by": "E05",
        "slip": "I poured his lordship's brandy at five past nine and took the tray "
        "away. I never touched that glass again!",
        "slip_suspicion": 5,
    },
    "vera": {
        "name": "Vera Blackwood",
        "short": "Miss Vera",
        "initial": "V",
        "role": "Niece",
        "room": (0, 1),
        "color": (205, 120, 175),
        "base_suspicion": 20,
        "alibi": "I was in the library all evening with a book. Uncle's death is "
        "a tragedy.",
        "tip": "Imogen Hale slammed a door after Uncle refused her offer. "
        "Check the dining table for that contract.",
        "contradicted_by": "E07",
        "slip": "Yes, Uncle cut me out of his will. But I was reading when it "
        "happened. I would never hurt him!",
        "slip_suspicion": 5,
    },
    "hale": {
        "name": "Imogen Hale",
        "short": "Ms. Hale",
        "initial": "H",
        "role": "Business partner",
        "room": (1, 2),
        "color": (130, 200, 140),
        "base_suspicion": 15,
        "alibi": "I was on the hall telephone with my lawyer from nine until half "
        "past. The phone log will show it.",
        "tip": "Dr. Crane looked rattled at dinner. He argued with Alaric in the "
        "study before the brandy was poured.",
        "contradicted_by": "E09",
        "slip": "Alaric refused my buyout and I was furious. But I was on the phone "
        "when he died. Check the log!",
        "slip_suspicion": 5,
    },
    "finch": {
        "name": "Dolores Finch",
        "short": "Mrs. Finch",
        "initial": "F",
        "role": "Cook",
        "room": (2, 2),
        "color": (225, 190, 90),
        "base_suspicion": 5,
        "alibi": "I was baking in the kitchen all night. Mr. Pike kept me company "
        "when he could.",
        "tip": "The doctor handed over his coat tonight and his shoes were caked "
        "in garden mud. Try the coat closet by the front door.",
        "contradicted_by": "E13",
        "slip": "That rat poison is mine, for the cellar mice! The tin was sealed "
        "when I last saw it.",
        "slip_suspicion": 5,
    },
}

# Evidence. `time` is an (hour, minute) tuple for when the event HAPPENED, so
# the journal can keep clues in chronological order. `suspect` is who the clue
# points to (or None); `suspicion` is how the clue changes each suspect's score.
EVIDENCE = {
    "E01": {
        "name": "Torn Blackmail Note",
        "spot": "the wastepaper bin",
        "room": (1, 1),
        "time": (19, 40),
        "category": "motive",
        "suspect": "crane",
        "suspicion": {"crane": 25},
        "desc": "A torn note in Alaric's hand: 'I know about the forged "
        "prescriptions, S. Pay by midnight or the medical board hears of it.'",
    },
    "E02": {
        "name": "Poisoned Brandy Glass",
        "spot": "the side table",
        "room": (1, 1),
        "time": (21, 15),
        "category": "scene",
        "suspect": None,
        "suspicion": {"pike": 10},
        "desc": "A half-empty brandy glass with a bitter, foxglove smell. The "
        "coroner suspects digitalis, a heart medicine. This is your murder weapon.",
    },
    "E03": {
        "name": "Muddy Footprints",
        "spot": "the French doors",
        "room": (1, 1),
        "time": (21, 20),
        "category": "scene",
        "suspect": None,
        "suspicion": {"crane": 5, "pike": 5},
        "desc": "Size-ten shoe prints in garden mud lead from the French doors "
        "to the armchair. Someone came in from outside.",
    },
    "E04": {
        "name": "Empty Digitalis Vial",
        "spot": "the flowerbed",
        "room": (1, 0),
        "time": (21, 25),
        "category": "means",
        "suspect": "crane",
        "suspicion": {"crane": 30},
        "desc": "A vial labelled 'Dr. S. Crane - Heartwell Pharmacy - Digitalis', "
        "tossed into the roses in a hurry.",
    },
    "E05": {
        "name": "Butler's Brandy Tray",
        "spot": "the serving counter",
        "room": (2, 2),
        "time": (21, 5),
        "category": "opportunity",
        "suspect": "pike",
        "suspicion": {"pike": 15},
        "desc": "Pike's tray: a decanter and two clean glasses. He poured "
        "Alaric's drink at five past nine.",
    },
    "E06": {
        "name": "Muddy Dress Shoes",
        "spot": "the coat closet",
        "room": (1, 2),
        "time": (21, 35),
        "category": "opportunity",
        "suspect": "crane",
        "suspicion": {"crane": 25},
        "desc": "Size-ten dress shoes, caked in garden mud and hidden behind the "
        "coats. A monogram inside reads 'S.C.'",
    },
    "E07": {
        "name": "Revised Will",
        "spot": "the writing desk",
        "room": (0, 1),
        "time": (17, 30),
        "category": "motive",
        "suspect": "vera",
        "suspicion": {"vera": 30},
        "desc": "A new will that cuts Vera out entirely. Alaric signed it yesterday.",
    },
    "E08": {
        "name": "Gambling Debt Notice",
        "spot": "the bookshelf",
        "room": (0, 1),
        "time": (16, 0),
        "category": "motive",
        "suspect": "vera",
        "suspicion": {"vera": 20},
        "desc": "An overdue casino notice addressed to Vera Blackwood. A debt "
        "only an inheritance could clear.",
    },
    "E09": {
        "name": "Rejected Buyout Offer",
        "spot": "the dining table",
        "room": (2, 1),
        "time": (18, 45),
        "category": "motive",
        "suspect": "hale",
        "suspicion": {"hale": 25},
        "desc": "Imogen's offer to buy Blackwood Industries, stamped REJECTED "
        "in red ink.",
    },
    "E10": {
        "name": "Hall Phone Log",
        "spot": "the hall table",
        "room": (1, 2),
        "time": (21, 0),
        "category": "alibi",
        "suspect": "hale",
        "suspicion": {"hale": -20},
        "desc": "The hall line was in use from 21:00 to 21:30. Imogen was "
        "talking to her lawyer the whole time.",
    },
    "E11": {
        "name": "Pantry Silver Log",
        "spot": "the pantry shelf",
        "room": (2, 2),
        "time": (21, 10),
        "category": "alibi",
        "suspect": "pike",
        "suspicion": {"pike": -20},
        "desc": "Initialled by Mrs. Finch: Pike was polishing silver in the "
        "pantry from 21:10, right after pouring the brandy.",
    },
    "E12": {
        "name": "Monogrammed Cigar Stub",
        "spot": "the garden bench",
        "room": (1, 0),
        "time": (21, 18),
        "category": "opportunity",
        "suspect": "crane",
        "suspicion": {"crane": 15},
        "desc": "A fresh cigar stub on the bench by the French doors, band "
        "stamped 'S.C.' Whoever smoked it was watching the study window.",
    },
    "E13": {
        "name": "Opened Rat Poison Tin",
        "spot": "the wine rack",
        "room": (0, 2),
        "time": (20, 0),
        "category": "means",
        "suspect": "pike",
        "suspicion": {"pike": 10},
        "desc": "A tin of rat poison with its lid pried open. Pike holds the "
        "cellar key, but the coroner found no arsenic.",
    },
    "E14": {
        "name": "Dismissal Notice",
        "spot": "the sideboard",
        "room": (2, 1),
        "time": (17, 0),
        "category": "motive",
        "suspect": "pike",
        "suspicion": {"pike": 20},
        "desc": "A signed notice dismissing Harlan Pike without a pension, "
        "effective Monday.",
    },
}

# Pairs of clues that connect to each other. Tracing a chain follows these links.
CLUE_LINK_PAIRS = [
    ("E02", "E04"),  # poisoned glass <-> digitalis vial
    ("E02", "E03"),  # glass <-> footprints at the same scene
    ("E02", "E05"),  # glass <-> the tray it was poured from
    ("E02", "E13"),  # glass <-> poison tin (ruled out later)
    ("E04", "E01"),  # vial <-> forged prescriptions in the blackmail note
    ("E03", "E06"),  # footprints <-> muddy shoes
    ("E03", "E12"),  # footprints <-> cigar stub by the French doors
    ("E05", "E11"),  # tray <-> pantry log
    ("E05", "E14"),  # tray <-> butler's dismissal
    ("E07", "E08"),  # Vera's will and her debts (separate thread)
    ("E09", "E10"),  # Hale's buyout and her phone alibi (separate thread)
]


def build_clue_graph(pairs):
    """Turn link pairs into a two-way graph: {clue_id: [linked clue ids]}."""
    graph = {clue_id: [] for clue_id in EVIDENCE}
    for first, second in pairs:
        graph[first].append(second)
        graph[second].append(first)
    return graph


CLUE_LINKS = build_clue_graph(CLUE_LINK_PAIRS)
