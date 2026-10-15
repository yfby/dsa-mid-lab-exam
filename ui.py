"""pygame-ce interface for Detective Case Zero.

All game rules live in game_state.py. This file only draws the game and turns
key presses / mouse clicks into calls on the Game object.

Screens (self.scene): title -> play <-> accuse / pause -> end
"""
import pygame

from case_data import (
    ACTION_POINTS, CASE_INTRO, CASE_TITLE, EVIDENCE, MAX_ATTEMPTS, ROOMS, SUSPECTS,
)
from game_state import Game

W, H = 1280, 780
FPS = 60

BG = (16, 18, 26)
PANEL = (27, 31, 44)
PANEL_HI = (40, 47, 66)
BORDER = (62, 70, 94)
TEXT = (232, 232, 238)
MUTED = (140, 148, 166)
AMBER = (240, 190, 90)
RED = (214, 80, 80)
GREEN = (96, 200, 132)
BLUE = (96, 156, 232)

CATEGORY_TAGS = {
    "motive": ("MOT", (222, 120, 120)),
    "means": ("MNS", (232, 170, 90)),
    "opportunity": ("OPP", (120, 180, 232)),
    "alibi": ("ALB", (120, 200, 140)),
    "scene": ("SCN", (170, 170, 192)),
}

MOVE_KEYS = {
    pygame.K_UP: "up", pygame.K_w: "up",
    pygame.K_DOWN: "down", pygame.K_s: "down",
    pygame.K_LEFT: "left", pygame.K_a: "left",
    pygame.K_RIGHT: "right", pygame.K_d: "right",
}
SUSPECT_ORDER = list(SUSPECTS)

# Layout rectangles
MAP_RECT = pygame.Rect(20, 80, 620, 360)
MSG_RECT = pygame.Rect(20, 450, 620, 320)
ACT_RECT = pygame.Rect(660, 80, 600, 200)
JOURNAL_RECT = pygame.Rect(660, 290, 295, 480)
BOARD_RECT = pygame.Rect(965, 290, 295, 480)


# ------------------------------------------------------------------ text helpers
def wrap(text, font, width):
    """Split text into lines that fit inside `width` pixels."""
    lines = []
    for paragraph in text.split("\n"):
        line = ""
        for word in paragraph.split(" "):
            trial = word if not line else line + " " + word
            if font.size(trial)[0] <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word
        lines.append(line)
    return lines


def fit(text, font, width):
    """Shorten text with '..' so it fits inside `width` pixels."""
    if font.size(text)[0] <= width:
        return text
    while text and font.size(text + "..")[0] > width:
        text = text[:-1]
    return text + ".."


def fmt_time(t):
    return f"{t[0]:02d}:{t[1]:02d}"


class App:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(f"Detective Case Zero - {CASE_TITLE}")
        try:
            dw, dh = pygame.display.get_desktop_sizes()[0]
        except (pygame.error, IndexError):
            dw, dh = W, H
        scale = min(1.0, (dw - 80) / W, (dh - 140) / H)
        size = (max(640, int(W * scale)), max(390, int(H * scale)))
        pygame.display.set_mode(size, pygame.RESIZABLE)

        # Everything is drawn on a fixed-size canvas, then scaled to the window.
        self.canvas = pygame.Surface((W, H))
        self.clock = pygame.time.Clock()
        self.f = {
            "title": pygame.font.Font(None, 76),
            "h1": pygame.font.Font(None, 38),
            "h2": pygame.font.Font(None, 27),
            "body": pygame.font.Font(None, 23),
            "small": pygame.font.Font(None, 19),
            "tiny": pygame.font.Font(None, 16),
        }
        self.game = Game()
        self.scene = "title"
        self.running = True
        self.hot = []          # clickable regions: (rect, action) built each frame
        self.hot_live = []     # the regions the player can click right now
        self.mouse = (0, 0)
        self.token = None      # animated detective position on the map
        self.tick = 0

    # ------------------------------------------------------------ window scaling
    def _view(self):
        win = pygame.display.get_surface()
        ww, wh = win.get_size()
        s = min(ww / W, wh / H)
        dw, dh = max(1, int(W * s)), max(1, int(H * s))
        return win, s, ((ww - dw) // 2, (wh - dh) // 2), (dw, dh)

    def canvas_pos(self, pos):
        _, s, (ox, oy), _ = self._view()
        return int((pos[0] - ox) / s), int((pos[1] - oy) / s)

    def present(self):
        win, s, offset, size = self._view()
        win.fill((0, 0, 0))
        if size == (W, H):
            win.blit(self.canvas, offset)
        else:
            win.blit(pygame.transform.smoothscale(self.canvas, size), offset)
        pygame.display.flip()

    # ---------------------------------------------------------------- main loop
    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle(event)
            self.mouse = self.canvas_pos(pygame.mouse.get_pos())
            self.tick += 1
            self.draw()
            self.present()
            self.clock.tick(FPS)
        pygame.quit()

    # -------------------------------------------------------------------- input
    def handle(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            self.on_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = self.canvas_pos(event.pos)
            for rect, action in reversed(self.hot_live):
                if rect.collidepoint(pos):
                    self.do(action)
                    break

    def on_key(self, key):
        g = self.game
        number = key - pygame.K_1          # 0..8 for the keys 1..9
        if self.scene == "title":
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.do(("start",))
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif self.scene == "play":
            if key in MOVE_KEYS:
                self.do(("dir", MOVE_KEYS[key]))
            elif 0 <= number <= 8:
                acts = g.actions()
                if number < len(acts):
                    self.do((acts[number]["kind"], acts[number]["id"]))
            elif key == pygame.K_t:
                self.do(("trace",))
            elif key == pygame.K_j:
                self.do(("accuse_open",))
            elif key == pygame.K_ESCAPE:
                self.scene = "pause"
        elif self.scene == "accuse":
            if 0 <= number < len(SUSPECT_ORDER):
                self.do(("accuse", SUSPECT_ORDER[number]))
            elif key == pygame.K_ESCAPE and not g.final_call:
                self.scene = "play"
        elif self.scene == "pause":
            if key == pygame.K_ESCAPE:
                self.scene = "play"
            elif key == pygame.K_r:
                self.do(("restart",))
            elif key == pygame.K_q:
                self.running = False
        elif self.scene == "end":
            if key == pygame.K_r:
                self.do(("restart",))
            elif key in (pygame.K_q, pygame.K_ESCAPE):
                self.running = False

    def do(self, action):
        g = self.game
        kind = action[0]
        if kind == "start":
            self.scene = "play"
        elif kind == "dir":
            g.move(action[1])
        elif kind == "move":
            g.move_to(action[1])
        elif kind == "examine":
            g.examine(action[1])
        elif kind == "interview":
            g.interview(action[1])
        elif kind == "select":
            g.select_clue(action[1])
        elif kind == "trace":
            g.trace()
        elif kind == "accuse_open":
            self.scene = "accuse"
        elif kind == "accuse":
            g.accuse(action[1])
            if g.status == "playing":
                self.scene = "play"
        elif kind == "resume":
            self.scene = "play"
        elif kind == "restart":
            self.game = Game()
            self.token = None
            self.scene = "play"
        elif kind == "quit":
            self.running = False
        self.sync_scene()

    def sync_scene(self):
        g = self.game
        if g.status != "playing" and self.scene in ("play", "accuse"):
            self.scene = "end"
        elif g.status == "playing" and g.final_call and self.scene == "play":
            self.scene = "accuse"   # out of time: the final accusation is forced

    # ------------------------------------------------------------ drawing utils
    def add_hot(self, rect, action):
        self.hot.append((pygame.Rect(rect), action))

    def text(self, string, font, color, pos, anchor="topleft"):
        image = self.f[font].render(string, True, color)
        rect = image.get_rect(**{anchor: pos})
        self.canvas.blit(image, rect)
        return rect

    def panel(self, rect, title, subtitle=""):
        pygame.draw.rect(self.canvas, PANEL, rect, border_radius=12)
        pygame.draw.rect(self.canvas, BORDER, rect, 1, border_radius=12)
        label = self.text(title, "h2", AMBER, (rect.x + 14, rect.y + 10))
        if subtitle:
            self.text(subtitle, "tiny", MUTED, (label.right + 10, rect.y + 16))

    def button(self, rect, label, action, color=AMBER, font="h2"):
        rect = pygame.Rect(rect)
        hover = rect.collidepoint(self.mouse)
        pygame.draw.rect(self.canvas, PANEL_HI if hover else PANEL, rect, border_radius=8)
        pygame.draw.rect(self.canvas, color, rect, 2, border_radius=8)
        self.text(label, font, color, rect.center, "center")
        self.add_hot(rect, action)

    def chip(self, label, color, topleft, width=34):
        rect = pygame.Rect(topleft, (width, 17))
        pygame.draw.rect(self.canvas, color, rect, border_radius=5)
        self.text(label, "tiny", BG, rect.center, "center")

    def dim(self):
        shade = pygame.Surface((W, H), pygame.SRCALPHA)
        shade.fill((6, 8, 12, 200))
        self.canvas.blit(shade, (0, 0))
        self.hot = []   # overlays block clicks on the screen underneath

    # ------------------------------------------------------------------ drawing
    def draw(self):
        self.hot = []
        self.canvas.fill(BG)
        if self.scene == "title":
            self.draw_title()
        else:
            self.draw_play()
            if self.scene == "accuse":
                self.draw_accuse()
            elif self.scene == "pause":
                self.draw_pause()
            elif self.scene == "end":
                self.draw_end()
        self.hot_live = self.hot

    # -- title ----------------------------------------------------------------
    def draw_title(self):
        c = self.canvas
        pygame.draw.rect(c, (22, 25, 36), (0, 0, W, 250))
        self.text("DETECTIVE", "title", AMBER, (W // 2, 70), "center")
        self.text("CASE ZERO", "title", TEXT, (W // 2, 135), "center")
        self.text(CASE_TITLE, "h1", MUTED, (W // 2, 200), "center")

        intro = pygame.Rect(240, 280, 800, 120)
        y = intro.y
        for line in wrap(CASE_INTRO, self.f["h2"], intro.width):
            self.text(line, "h2", TEXT, (intro.x, y))
            y += 30

        self.panel(pygame.Rect(240, 425, 800, 205), "HOW TO PLAY")
        tips = [
            "Move between rooms: arrow keys / WASD, or click a highlighted room.",
            "Press 1-9 (or click) to search for clues and interview suspects.",
            "Clues enter your journal in time order. Press T to trace a clue chain.",
            "Every move, search and interview costs one of your 70 actions.",
            "Press J when ready to accuse. You can prove the case only with "
            "motive, means and opportunity.",
        ]
        y = 468
        for tip in tips:
            self.text(tip, "body", TEXT, (260, y))
            y += 28

        self.button((W // 2 - 170, 655, 340, 54), "START INVESTIGATION  [Enter]",
                    ("start",), AMBER)
        self.text("Esc to quit", "small", MUTED, (W // 2, 735), "center")

    # -- header ---------------------------------------------------------------
    def draw_header(self):
        g = self.game
        c = self.canvas
        pygame.draw.rect(c, (11, 13, 19), (0, 0, W, 66))
        pygame.draw.line(c, BORDER, (0, 66), (W, 66))
        self.text("DETECTIVE CASE ZERO", "h1", AMBER, (20, 10))
        self.text(CASE_TITLE, "small", MUTED, (22, 42))

        # actions left
        frac = g.ap / ACTION_POINTS
        color = GREEN if frac > 0.5 else AMBER if frac > 0.2 else RED
        self.text(f"ACTIONS LEFT  {g.ap}", "small", TEXT, (500, 14))
        pygame.draw.rect(c, PANEL_HI, (500, 40, 240, 12), border_radius=6)
        pygame.draw.rect(c, color, (500, 40, int(240 * frac), 12), border_radius=6)

        # accusations left
        self.text("ACCUSATIONS LEFT", "small", TEXT, (800, 14))
        for i in range(MAX_ATTEMPTS):
            pos = (810 + i * 28, 46)
            pygame.draw.circle(c, RED if i < g.attempts else PANEL_HI, pos, 9)
            pygame.draw.circle(c, BORDER, pos, 9, 1)

        self.button((1090, 13, 170, 42), "ACCUSE  [J]", ("accuse_open",), RED, "h2")

    # -- play screen ----------------------------------------------------------
    def draw_play(self):
        self.draw_header()
        self.draw_map()
        self.draw_actions()
        self.draw_notes()
        self.draw_journal()
        self.draw_board()

    def room_rect(self, pos):
        return pygame.Rect(35 + pos[0] * 205, 118 + pos[1] * 98, 180, 80)

    def draw_map(self):
        c = self.canvas
        g = self.game
        self.panel(MAP_RECT, "MANOR FLOOR PLAN", "click a lit room or use arrow keys")

        for pos in ROOMS:                     # doors between neighbouring rooms
            for dx, dy in ((1, 0), (0, 1)):
                other = (pos[0] + dx, pos[1] + dy)
                if other not in ROOMS:
                    continue
                a, b = self.room_rect(pos), self.room_rect(other)
                if dx:
                    door = pygame.Rect(a.right, a.centery - 6, b.left - a.right, 12)
                else:
                    door = pygame.Rect(a.centerx - 6, a.bottom, 12, b.top - a.bottom)
                pygame.draw.rect(c, (120, 94, 56), door)

        reachable = set(g.neighbours().values())
        for pos, info in ROOMS.items():
            r = self.room_rect(pos)
            here = pos == g.pos
            adjacent = pos in reachable and not g.final_call
            hover = adjacent and r.collidepoint(self.mouse)
            pygame.draw.rect(c, (54, 64, 92) if hover else PANEL_HI, r, border_radius=10)
            border = AMBER if here else BLUE if adjacent else BORDER
            pygame.draw.rect(c, border, r, 3 if (here or adjacent) else 1, border_radius=10)
            self.text(info["name"], "h2", TEXT if (here or adjacent) else MUTED,
                      (r.x + 10, r.y + 8))
            if adjacent:
                self.add_hot(r, ("move", pos))

            # one dot per clue hidden in the room: filled once collected
            clues = [cid for cid, ev in EVIDENCE.items() if ev["room"] == pos]
            for i, cid in enumerate(clues):
                centre = (r.x + 18 + i * 17, r.bottom - 16)
                if cid in g.collected:
                    pygame.draw.circle(c, GREEN, centre, 6)
                else:
                    pygame.draw.circle(c, MUTED, centre, 6, 2)

            for sid, s in SUSPECTS.items():   # suspects wait in their rooms
                if s["room"] == pos:
                    centre = (r.right - 26, r.bottom - 26)
                    pygame.draw.circle(c, s["color"], centre, 15)
                    ring = TEXT if sid in g.interviewed else BG
                    pygame.draw.circle(c, ring, centre, 15, 2)
                    self.text(s["initial"], "body", BG, centre, "center")

        # the detective glides between rooms
        target = self.room_rect(g.pos).center
        target = (target[0] - 8, target[1] + 8)
        if self.token is None:
            self.token = [float(target[0]), float(target[1])]
        self.token[0] += (target[0] - self.token[0]) * 0.22
        self.token[1] += (target[1] - self.token[1]) * 0.22
        centre = (int(self.token[0]), int(self.token[1]))
        pygame.draw.circle(c, (0, 0, 0), (centre[0] + 2, centre[1] + 3), 15)
        pygame.draw.circle(c, AMBER, centre, 15)
        self.text("D", "body", BG, centre, "center")

        legend_y = MAP_RECT.bottom - 22
        self.text("D = you    colored circles = suspects (white ring = interviewed)    "
                  "dots = clues in room", "tiny", MUTED, (MAP_RECT.x + 14, legend_y))

    def draw_actions(self):
        g = self.game
        self.panel(ACT_RECT, f"IN THE {g.room['name'].upper()}",
                   "press the number or click")
        acts = g.actions()
        if not acts:
            self.text("Nothing more to do here. Try another room.", "body", MUTED,
                      (ACT_RECT.x + 16, ACT_RECT.y + 50))
        for i, act in enumerate(acts):
            row = pygame.Rect(ACT_RECT.x + 12, ACT_RECT.y + 42 + i * 34, 576, 30)
            hover = row.collidepoint(self.mouse)
            pygame.draw.rect(self.canvas, PANEL_HI if hover else (33, 38, 54), row,
                             border_radius=6)
            if act["kind"] == "interview":
                color = MUTED if act["done"] else BLUE
            else:
                color = MUTED if act["done"] else AMBER
            self.text(f"[{i + 1}]", "body", color, (row.x + 10, row.y + 6))
            self.text(act["label"], "body", color, (row.x + 52, row.y + 6))
            self.add_hot(row, (act["kind"], act["id"]))
        self.text("Moving, searching and interviewing each cost 1 action. "
                  "Tracing and reading clues is free.", "tiny", MUTED,
                  (ACT_RECT.x + 14, ACT_RECT.bottom - 24))

    def draw_notes(self):
        g = self.game
        self.panel(MSG_RECT, "CASE NOTES")
        inner = pygame.Rect(MSG_RECT.x + 16, MSG_RECT.y + 44, MSG_RECT.width - 32,
                            MSG_RECT.height - 56)
        y = inner.bottom
        for i, message in enumerate(reversed(g.messages)):
            font = self.f["body"] if i == 0 else self.f["small"]
            lines = wrap(message, font, inner.width)
            height = len(lines) * (font.get_linesize() + 1) + 8
            if y - height < inner.top:
                break
            y -= height
            for j, line in enumerate(lines):
                image = font.render(line, True, TEXT if i == 0 else MUTED)
                self.canvas.blit(image, (inner.x, y + j * (font.get_linesize() + 1)))

    def draw_journal(self):
        g = self.game
        r = JOURNAL_RECT
        self.panel(r, "CASE JOURNAL", "by time - Insertion Sort")
        if not g.journal:
            for i, line in enumerate(wrap("No evidence yet. Search the rooms to fill "
                                          "your journal.", self.f["body"], r.width - 32)):
                self.text(line, "body", MUTED, (r.x + 16, r.y + 52 + i * 24))
        for i, cid in enumerate(g.journal):
            ev = EVIDENCE[cid]
            row = pygame.Rect(r.x + 8, r.y + 42 + i * 26, r.width - 16, 24)
            if cid == g.selected_clue:
                pygame.draw.rect(self.canvas, PANEL_HI, row, border_radius=5)
            elif row.collidepoint(self.mouse):
                pygame.draw.rect(self.canvas, (34, 40, 56), row, border_radius=5)
            if cid in g.last_chain:
                pygame.draw.rect(self.canvas, AMBER, (row.x, row.y + 3, 4, 18))
            self.text(fmt_time(ev["time"]), "small", MUTED, (row.x + 10, row.y + 5))
            tag, color = CATEGORY_TAGS[ev["category"]]
            name = fit(ev["name"], self.f["small"], row.width - 118)
            self.text(name, "small", TEXT, (row.x + 56, row.y + 5))
            self.chip(tag, color, (row.right - 40, row.y + 4))
            self.add_hot(row, ("select", cid))
        self.text("MOT motive  MNS means  OPP opportunity", "tiny", MUTED,
                  (r.x + 14, r.bottom - 72))
        self.text("ALB alibi  SCN scene  amber bar = traced", "tiny",
                  MUTED, (r.x + 14, r.bottom - 57))
        self.button((r.x + 12, r.bottom - 40, r.width - 24, 30),
                    "TRACE CLUE CHAIN  [T]", ("trace",), AMBER, "body")

    def draw_board(self):
        g = self.game
        r = BOARD_RECT
        self.panel(r, "SUSPECT BOARD", "Bubble Sort")
        for rank, sid in enumerate(g.ranked_suspects(), start=1):
            s = SUSPECTS[sid]
            score = g.suspicion[sid]
            row = pygame.Rect(r.x + 8, r.y + 42 + (rank - 1) * 58, r.width - 16, 54)
            pygame.draw.rect(self.canvas, (33, 38, 54), row, border_radius=8)
            self.text(str(rank), "h1", MUTED, (row.x + 10, row.y + 12))
            pygame.draw.circle(self.canvas, s["color"], (row.x + 52, row.y + 16), 7)
            self.text(s["name"], "body", TEXT, (row.x + 64, row.y + 7))
            self.text(s["role"], "tiny", MUTED, (row.x + 64, row.y + 26))
            bar = pygame.Rect(row.x + 40, row.y + 40, 150, 7)
            pygame.draw.rect(self.canvas, PANEL_HI, bar, border_radius=3)
            fill = min(1.0, score / 120)
            heat = RED if fill > 0.6 else AMBER if fill > 0.3 else BLUE
            pygame.draw.rect(self.canvas, heat, (bar.x, bar.y, int(bar.width * fill), 7),
                             border_radius=3)
            self.text(str(score), "h2", heat, (row.right - 10, row.y + 8), "topright")
            if sid in g.interviewed:
                self.chip("I", GREEN, (row.right - 52, row.y + 32), 20)
            if sid in g.confronted:
                self.chip("C", AMBER, (row.right - 28, row.y + 32), 20)

        y = r.y + 42 + 5 * 58 + 8
        queue = g.interview_queue()
        self.text("NEXT INTERVIEW - Selection Sort", "tiny", AMBER, (r.x + 14, y))
        if queue:
            s = SUSPECTS[queue[0]]
            line = f"{s['short']} (suspicion {g.suspicion[queue[0]]}), in the " \
                   f"{ROOMS[s['room']]['name']}"
        else:
            line = "Everyone has been interviewed."
        for i, text in enumerate(wrap(line, self.f["small"], r.width - 28)):
            self.text(text, "small", TEXT, (r.x + 14, y + 18 + i * 18))
        y += 62
        self.text("READY TO CONFRONT", "tiny", AMBER, (r.x + 14, y))
        ready = g.ready_to_confront()
        if ready:
            line = ", ".join(f"{SUSPECTS[s]['short']} ({ROOMS[SUSPECTS[s]['room']]['name']})"
                             for s in ready)
        else:
            line = "No one yet. New clues may break an alibi."
        for i, text in enumerate(wrap(line, self.f["small"], r.width - 28)):
            self.text(text, "small", TEXT, (r.x + 14, y + 18 + i * 18))
        self.text("I = interviewed   C = confronted", "tiny", MUTED,
                  (r.x + 14, r.bottom - 20))

    # -- overlays ---------------------------------------------------------------
    def draw_accuse(self):
        g = self.game
        self.dim()
        box = pygame.Rect(330, 120, 620, 520)
        self.panel(box, "NAME THE KILLER")
        if g.final_call:
            msg = "Dawn has broken. This is your final accusation."
            color = RED
        else:
            msg = (f"Accusations left: {g.attempts}. To win you must prove motive, "
                   "means and opportunity with traced clues.")
            color = MUTED
        for i, line in enumerate(wrap(msg, self.f["small"], box.width - 32)):
            self.text(line, "small", color, (box.x + 16, box.y + 44 + i * 18))
        for i, sid in enumerate(SUSPECT_ORDER):
            s = SUSPECTS[sid]
            row = pygame.Rect(box.x + 16, box.y + 96 + i * 66, box.width - 32, 58)
            hover = row.collidepoint(self.mouse)
            pygame.draw.rect(self.canvas, PANEL_HI if hover else (33, 38, 54), row,
                             border_radius=8)
            pygame.draw.rect(self.canvas, s["color"], row, 2, border_radius=8)
            self.text(f"[{i + 1}]", "h2", AMBER, (row.x + 12, row.y + 16))
            self.text(s["name"], "h2", TEXT, (row.x + 60, row.y + 8))
            self.text(f"{s['role']}   |   suspicion {g.suspicion[sid]}", "small", MUTED,
                      (row.x + 60, row.y + 33))
            self.add_hot(row, ("accuse", sid))
        if not g.final_call:
            self.button((box.centerx - 100, box.bottom - 50, 200, 36), "CANCEL  [Esc]",
                        ("resume",), MUTED, "body")

    def draw_pause(self):
        self.dim()
        box = pygame.Rect(440, 230, 400, 320)
        self.panel(box, "PAUSED")
        self.button((box.x + 50, box.y + 70, 300, 48), "RESUME  [Esc]", ("resume",), GREEN)
        self.button((box.x + 50, box.y + 135, 300, 48), "RESTART CASE  [R]",
                    ("restart",), AMBER)
        self.button((box.x + 50, box.y + 200, 300, 48), "QUIT  [Q]", ("quit",), RED)

    def draw_end(self):
        g = self.game
        self.dim()
        won = g.status == "won"
        color = GREEN if won else RED
        box = pygame.Rect(240, 90, 800, 600)
        pygame.draw.rect(self.canvas, PANEL, box, border_radius=14)
        pygame.draw.rect(self.canvas, color, box, 3, border_radius=14)
        self.text(g.result_title, "title", color, (box.centerx, box.y + 56), "center")

        y = box.y + 110
        for line in wrap(g.result_text, self.f["h2"], box.width - 60):
            self.text(line, "h2", TEXT, (box.x + 30, y))
            y += 30

        y += 12
        stats = [f"Evidence found: {len(g.collected)} / {len(EVIDENCE)}",
                 f"Actions left: {g.ap}",
                 f"Accusations left: {max(0, g.attempts)}"]
        if won:
            stats.append(f"Final score: {g.score}")
        for line in stats:
            self.text(line, "body", AMBER if line.startswith("Final") else MUTED,
                      (box.x + 30, y))
            y += 26

        if won and g.proof_chain:
            y += 8
            self.text("Your proof chain:", "small", AMBER, (box.x + 30, y))
            names = " -> ".join(g.name_of(c) for c in g.proof_chain)
            for i, line in enumerate(wrap(names, self.f["small"], box.width - 60)):
                self.text(line, "small", TEXT, (box.x + 30, y + 20 + i * 18))

        self.button((box.x + 90, box.bottom - 70, 280, 48), "PLAY AGAIN  [R]",
                    ("restart",), GREEN)
        self.button((box.right - 370, box.bottom - 70, 280, 48), "QUIT  [Q]",
                    ("quit",), RED)


def run():
    App().run()
