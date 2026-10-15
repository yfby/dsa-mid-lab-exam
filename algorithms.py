"""Hand-written algorithms for Detective Case Zero.

Nothing in this file uses the built-in sort() or sorted().

Where the game calls each function (see also the feature map in README.md):
    bubble_sort      -> Game.ranked_suspects()   (Suspect Board, ranked by suspicion)
    insert_sorted    -> Game.examine()           (Case Journal, kept in time order)
    selection_sort   -> Game.interview_queue()   (who to interview next)
    trace_chain      -> Game.trace(), Game.proof_for()  (recursive clue tracing)

All sorts accept the same two optional arguments:
    key     - function that returns the value to compare (default: the item itself)
    reverse - True for largest-first, False for smallest-first
"""


def _identity(item):
    return item


def _out_of_order(left, right, reverse):
    """True when `left` should come AFTER `right` in the requested order."""
    if reverse:
        return left < right
    return left > right


# --------------------------------------------------------------------------
# Bubble Sort: repeated adjacent comparisons
# --------------------------------------------------------------------------
def bubble_sort(items, key=None, reverse=False):
    """Return a new sorted list using Bubble Sort.

    Walk the list comparing neighbours and swap any pair that is out of order.
    After each full pass the next-largest (or smallest) item has "bubbled" to
    its final place at the end, so every pass can stop one position earlier.
    If a whole pass makes no swap the list is already sorted, so we stop.
    """
    key = key or _identity
    data = list(items)  # copy so the caller's list is never changed

    for end in range(len(data) - 1, 0, -1):
        swapped = False
        for i in range(end):
            if _out_of_order(key(data[i]), key(data[i + 1]), reverse):
                data[i], data[i + 1] = data[i + 1], data[i]
                swapped = True
        if not swapped:
            break
    return data


# --------------------------------------------------------------------------
# Insertion Sort: insert one item into an already ordered list
# --------------------------------------------------------------------------
def insert_sorted(ordered, new_item, key=None, reverse=False):
    """Insert `new_item` into the already-ordered list `ordered` (in place).

    This is the inner step of Insertion Sort: shift every larger item one slot
    to the right, then drop the new item into the gap. Equal items keep their
    existing order (new items go after them), so the sort is stable.
    """
    key = key or _identity
    ordered.append(new_item)  # make room at the end
    i = len(ordered) - 2      # index of the last item that was already ordered
    while i >= 0 and _out_of_order(key(ordered[i]), key(new_item), reverse):
        ordered[i + 1] = ordered[i]  # shift right
        i -= 1
    ordered[i + 1] = new_item
    return ordered


def insertion_sort(items, key=None, reverse=False):
    """Return a new sorted list by inserting each item into a growing ordered list."""
    ordered = []
    for item in items:
        insert_sorted(ordered, item, key, reverse)
    return ordered


# --------------------------------------------------------------------------
# Selection Sort: repeatedly select the extreme remaining value
# --------------------------------------------------------------------------
def find_extreme_index(items, start, key=None, reverse=False):
    """Index of the smallest (or largest, if reverse) item in items[start:]."""
    key = key or _identity
    best = start
    for i in range(start + 1, len(items)):
        if reverse:
            better = key(items[i]) > key(items[best])
        else:
            better = key(items[i]) < key(items[best])
        if better:
            best = i
    return best


def selection_sort(items, key=None, reverse=False):
    """Return a new sorted list using Selection Sort.

    For each position, scan the remaining unsorted part, select the smallest
    (or largest) value, and swap it into place.
    """
    data = list(items)
    for i in range(len(data) - 1):
        chosen = find_extreme_index(data, i, key, reverse)
        if chosen != i:
            data[i], data[chosen] = data[chosen], data[i]
    return data


# --------------------------------------------------------------------------
# Recursion: follow connected clues
# --------------------------------------------------------------------------
def trace_chain(node, graph, unlocked, visited=None):
    """Recursively collect every clue connected to `node`.

    graph    - dict mapping a clue id to the list of clue ids it links to
    unlocked - set of clue ids the detective has actually found
    visited  - clue ids already traced, in the order they were reached

    Base cases (the recursion stops):
        1. the clue was already visited  -> prevents endless loops
        2. the clue has not been found yet -> the chain breaks here
    Each recursive call adds one new clue to `visited`, so the number of calls
    is bounded by the number of clues in the case.
    """
    if visited is None:
        visited = []
    if node in visited or node not in unlocked:
        return visited
    visited.append(node)
    for neighbour in graph.get(node, []):
        trace_chain(neighbour, graph, unlocked, visited)
    return visited
