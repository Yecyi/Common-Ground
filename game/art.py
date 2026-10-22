"""Original pixel art for Common Ground. All sprites are bottom-centre anchored.

Art is drawn from code so the team can edit every colour and shape. No downloaded
art, fonts or texture packs are required. Call ``export_assets`` to regenerate
the PNG reference sheet in assets/.
"""
from __future__ import annotations

import random
from pathlib import Path

import pygame


INK = (42, 55, 51)
CREAM = (246, 229, 187)


def rect(s, color, box, radius=0):
    pygame.draw.rect(s, color, box, border_radius=radius)


def new(size):
    return pygame.Surface(size, pygame.SRCALPHA)


def export_icon(folder):
    """Original app mark: a shared-root sprout and sunrise, in crisp pixels."""
    from PIL import Image

    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    s = new((64, 64))
    rect(s, (29, 59, 48), (0, 0, 64, 64), 13)
    rect(s, (38, 76, 57), (4, 4, 56, 56), 10)
    gold = (233, 191, 105)
    light = (246, 231, 184)
    sage = (150, 183, 124)
    pygame.draw.circle(s, gold, (46, 17), 7)
    rect(s, light, (45, 6, 2, 2))
    rect(s, gold, (56, 16, 2, 2))
    rect(s, gold, (53, 8, 2, 2))
    rect(s, light, (31, 26, 3, 25))
    pygame.draw.polygon(s, sage, [(31, 33), (21, 32), (14, 25), (13, 18), (21, 18), (29, 24)])
    pygame.draw.line(s, (193, 211, 150), (17, 22), (30, 32), 2)
    pygame.draw.polygon(s, (191, 207, 144), [(33, 39), (43, 36), (49, 30), (49, 24), (42, 24), (35, 30)])
    pygame.draw.line(s, light, (35, 36), (45, 28), 1)
    # Three people share the ground beneath the plant.
    for x in (20, 32, 44):
        pygame.draw.circle(s, gold if x != 32 else light, (x, 47), 3)
        rect(s, gold if x != 32 else light, (x - 4, 51, 8, 4), 2)
    rect(s, sage, (15, 57, 34, 2), 1)
    png = folder / "icon.png"
    pygame.image.save(pygame.transform.scale(s, (256, 256)), str(png))
    with Image.open(png) as image:
        image.save(folder / "icon.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


class Art:
    """Cached 32px tiles and transparent sprites, with two world palettes."""

    NAMES = ("player", "mira", "rowan", "amani", "theo", "tree", "house",
             "workshop", "pump", "litter", "crate", "plot", "bench",
             "noticeboard", "flower", "rock", "deadtree", "sign", "rope",
             "flood", "soot", "dispute", "plot_seed", "plot_sprout")
    PEOPLE = ("player", "mira", "rowan", "amani", "theo")
    FACINGS = ("down", "up", "left", "right")

    def __init__(self, custom_dir=None):
        """``custom_dir`` may hold hand-made PNGs that replace the drawn art.

        A file named like ``tree_restored.png`` or ``tile_grass_polluted.png``
        takes the place of the matching sprite. Walking frames for people are
        named ``player_left_1_polluted.png`` (name, facing, step, state).
        Anything missing or unreadable falls back to the art drawn in code.
        """
        self.custom_dir = Path(custom_dir) if custom_dir else None
        self._sprites = {}
        self._tiles = {}
        self._people = {}
        for restored in (False, True):
            for name in self.NAMES:
                self._sprites[name, restored] = self._custom(name, restored) or self._make_sprite(name, restored)
            for kind in ("grass", "path", "water", "bridge"):
                tile = self._custom(f"tile_{kind}", restored)
                if tile is not None and tile.get_size() != (32, 32):
                    tile = pygame.transform.scale(tile, (32, 32))
                self._tiles[kind, restored] = tile or self._make_tile(kind, restored)

    def _custom(self, name, restored):
        if self.custom_dir is None:
            return None
        path = self.custom_dir / f"{name}_{'restored' if restored else 'polluted'}.png"
        try:
            return pygame.image.load(str(path)) if path.is_file() else None
        except (pygame.error, OSError):
            return None

    def sprite(self, name: str, restored: bool = False) -> pygame.Surface:
        return self._sprites[name, bool(restored)]

    def person(self, name: str, facing: str = "down", step: int = 0, supported: bool = False) -> pygame.Surface:
        """A person facing a direction; step 0 stands, 1 and 2 are the walking frames."""
        key = name, facing, step, bool(supported)
        if key not in self._people:
            custom = self._custom(f"{name}_{facing}_{step}", supported) if self.custom_dir else None
            if custom is None and name in self.PEOPLE and facing == "down" and step == 0:
                custom = self._sprites[name, bool(supported)]
            elif custom is None:
                custom = self._custom(name, supported)
            self._people[key] = custom or self._person(name, facing, step, supported)
        return self._people[key]

    def tile(self, kind: str, restored: bool = False) -> pygame.Surface:
        return self._tiles[kind, bool(restored)]

    def _make_tile(self, kind, restored):
        s = new((32, 32))
        rng = random.Random(127 + len(kind))
        if kind == "grass":
            base = (96, 148, 90) if restored else (117, 125, 112)
            s.fill(base)
            colors = [(x + 5, y + 9, z + 2) for x, y, z in [base]]
            colors += [(base[0] - 9, base[1] - 7, base[2] - 7)]
            for _ in range(20):
                x, y = rng.randrange(31), rng.randrange(31)
                rect(s, rng.choice(colors), (x, y, 2, 1))
            if restored:
                for x, y in ((6, 17), (24, 6)):
                    rect(s, (156, 176, 104), (x, y, 1, 2))
        elif kind == "path":
            s.fill((209, 188, 138) if restored else (170, 166, 150))
            for _ in range(18):
                x, y = rng.randrange(31), rng.randrange(31)
                rect(s, (196, 175, 128) if restored else (160, 156, 141), (x, y, 2, 1))
            for x, y in ((5, 9), (23, 24), (16, 18)):
                rect(s, (223, 204, 156) if restored else (185, 181, 165), (x, y, 3, 1))
        elif kind == "water":
            s.fill((64, 152, 164) if restored else (98, 117, 121))
            for x, y, w in ((3, 6, 10), (18, 13, 10), (-3, 23, 14), (24, 29, 9)):
                rect(s, (125, 196, 186) if restored else (128, 142, 140), (x, y, w, 1))
                rect(s, (84, 168, 170) if restored else (108, 128, 128), (x + 3, y + 2, w, 1))
            if not restored:
                rect(s, (126, 130, 106), (18, 4, 7, 3))
                rect(s, (133, 137, 109), (22, 6, 8, 2))
        else:
            s.fill((94, 103, 83))
            for y in range(0, 32, 6):
                rect(s, (166, 126, 86) if restored else (136, 124, 98), (0, y, 32, 5))
                rect(s, (194, 152, 102) if restored else (155, 140, 110), (0, y, 32, 1))
                rect(s, (96, 86, 67), (4, y + 2, 2, 1))
                rect(s, (96, 86, 67), (26, y + 2, 2, 1))
        return s

    def _person(self, name, facing="down", step=0, supported=False):
        """Draw one person. Residents who carry a lot stoop a little until supported."""
        s = new((24, 36))
        pygame.draw.ellipse(s, (30, 41, 37, 65), (3, 29, 19, 6))
        coats = {"player": (56, 137, 136), "mira": (192, 104, 85),
                 "rowan": (116, 143, 99), "amani": (207, 161, 73),
                 "theo": (102, 117, 153)}
        skin = {"player": (213, 166, 119), "mira": (183, 126, 92),
                "rowan": (224, 178, 137), "amani": (135, 91, 65),
                "theo": (198, 143, 106)}[name]
        hair = {"player": (53, 60, 53), "mira": (68, 54, 49),
                "rowan": (152, 144, 120), "amani": (49, 47, 44),
                "theo": (78, 60, 48)}[name]
        c = coats[name]
        resident = name != "player"
        if resident:
            shift = 16 if supported else -14
            c = tuple(max(0, min(255, v + shift)) for v in c)
        hy = 1 if resident and not supported else 0
        rect(s, INK, (6, 16, 13, 15))
        rect(s, c, (7, 15, 11, 14))
        rect(s, tuple(max(0, v - 19) for v in c), (16, 18, 3, 10))
        # Arms swing against the legs.
        rect(s, skin, (4, 19 + (1 if step == 1 else -1 if step == 2 else 0), 3, 7))
        rect(s, skin, (18, 19 + (1 if step == 2 else -1 if step == 1 else 0), 3, 7))
        for x, raised in ((7, step == 2), (14, step == 1)):
            rect(s, (57, 64, 57), (x, 28, 4, 3 if raised else 5))
            rect(s, (46, 49, 43), (x - 1, 30 if raised else 32, 6, 2))
        rect(s, hair, (6, 3 + hy, 13, 13), 3)
        rect(s, skin, (8, 7 + hy, 10, 9))
        rect(s, hair, (7, 4 + hy, 12, 4))
        rect(s, hair, (6, 7 + hy, 3, 5))
        eyes, mouth = (53, 50, 42), (174, 118, 91)
        if facing == "up":
            rect(s, hair, (7, 5 + hy, 12, 11), 3)
        elif facing in ("left", "right"):
            back = (14, 5 + hy, 5, 10) if facing == "left" else (7, 5 + hy, 5, 10)
            rect(s, hair, back, 2)
            rect(s, eyes, (10 if facing == "left" else 16, 10 + hy, 1, 2))
            rect(s, tuple(max(0, v - 25) for v in skin), (8 if facing == "left" else 18, 12 + hy, 1, 2))
            rect(s, mouth, (9 if facing == "left" else 16, 14 + hy, 2, 1))
        else:
            rect(s, eyes, (11, 10 + hy, 1, 2))
            rect(s, eyes, (16, 10 + hy, 1, 2))
            if supported:
                rect(s, mouth, (12, 14, 5, 1))
                rect(s, mouth, (11, 13, 1, 1))
                rect(s, mouth, (17, 13, 1, 1))
            else:
                rect(s, mouth, (13, 14 + hy, 3, 1))
        if name == "player":
            rect(s, (231, 193, 104), (7, 15, 12, 3))
            rect(s, (231, 193, 104), (15, 17, 3, 6))
            rect(s, (69, 83, 69), (6, 18, 2, 9))
            rect(s, (236, 214, 163), (10, 20, 4, 3))
            if facing == "up":
                rect(s, (69, 83, 69), (8, 17, 9, 9), 2)
        elif name == "mira":
            rect(s, (232, 207, 157), (9, 18, 2, 8))
            rect(s, hair, (18, 7 + hy, 3, 10))
            rect(s, (237, 214, 169), (13, 20, 3, 3))
        elif name == "rowan":
            rect(s, (185, 158, 110), (4, 6 + hy, 18, 3))
            rect(s, (189, 165, 117), (7, 2 + hy, 12, 5))
            rect(s, (225, 211, 171), (9, 22, 7, 5))
        elif name == "amani":
            rect(s, (219, 202, 160), (5, 3 + hy, 14, 4))
            rect(s, (201, 185, 150), (5, 7 + hy, 3, 8))
            rect(s, (201, 185, 150), (17, 7 + hy, 3, 8))
            rect(s, (240, 222, 174), (8, 16, 10, 2))
            rect(s, (117, 104, 74), (13, 22, 3, 5))
        elif name == "theo":
            rect(s, (192, 151, 73), (6, 4 + hy, 14, 4))
            rect(s, (213, 173, 94), (8, 1 + hy, 10, 4))
            rect(s, (58, 73, 91), (9, 18, 7, 10))
            rect(s, (190, 191, 167), (10, 21, 5, 2))
        return s

    def _make_sprite(self, name, restored):
        if name in self.PEOPLE:
            return self._person(name, "down", 0, restored)
        if name == "tree":
            s = new((64, 80))
            pygame.draw.ellipse(s, (33, 53, 40, 55), (7, 65, 52, 12))
            rect(s, (84, 78, 56), (27, 36, 11, 39))
            rect(s, (127, 110, 72), (29, 39, 4, 34))
            pygame.draw.line(s, (85, 77, 55), (29, 56), (15, 37), 6)
            pygame.draw.line(s, (85, 77, 55), (35, 48), (47, 30), 5)
            colors = ((57, 102, 73), (74, 125, 80), (99, 145, 86), (132, 158, 99)) if restored else ((89, 103, 83), (105, 119, 90), (121, 131, 99), (138, 142, 108))
            clusters = ((8, 25, 27, 26, 0), (28, 22, 29, 29, 0), (17, 9, 31, 30, 1), (5, 20, 27, 23, 1), (29, 13, 28, 25, 1), (17, 6, 27, 25, 2), (10, 18, 28, 21, 2), (30, 15, 20, 19, 2), (19, 7, 20, 8, 3))
            for x, y, w, h, col in clusters:
                rect(s, colors[col], (x, y, w, h), 6)
            for x, y in ((12, 29), (21, 16), (37, 31), (43, 21), (28, 39), (20, 28)):
                rect(s, colors[3], (x, y, 5, 2))
            if restored:
                for x, y in ((19, 24), (37, 20), (27, 37)):
                    rect(s, (226, 188, 93), (x, y, 3, 3))
            else:
                pygame.draw.line(s, (83, 81, 60), (12, 48), (6, 44), 2)
                rect(s, (157, 142, 101), (43, 63, 5, 2))
            return s
        if name in ("house", "workshop"):
            s = new((128, 112))
            pygame.draw.ellipse(s, (39, 50, 41, 55), (5, 92, 120, 17))
            wall = (219, 196, 147) if restored else (186, 179, 149)
            rect(s, (90, 89, 68), (15, 40, 102, 65))
            rect(s, wall, (18, 42, 96, 59))
            rect(s, (164, 144, 105), (18, 89, 96, 12))
            roof = (164, 92, 67) if restored else (132, 113, 90)
            pygame.draw.polygon(s, INK, [(8, 48), (26, 16), (104, 16), (123, 48)])
            pygame.draw.polygon(s, roof, [(11, 45), (28, 18), (102, 18), (119, 45)])
            for y in (25, 34, 43):
                pygame.draw.line(s, (181, 119, 83) if restored else (150, 132, 103), (26 - (y - 18)//2, y), (104 + (y - 18)//2, y), 2)
                for x in range(29 + (5 if y == 34 else 0), 110, 17):
                    rect(s, (131, 89, 69) if restored else (113, 107, 85), (x, y - 6, 1, 5))
            rect(s, (79, 85, 73), (56, 61, 24, 40))
            rect(s, (122, 110, 75), (59, 64, 18, 37))
            rect(s, (196, 166, 92), (73, 80, 2, 2))
            for x in (29, 91):
                rect(s, (92, 100, 80), (x - 2, 58, 18, 23))
                rect(s, (121, 176, 168) if restored else (128, 153, 143), (x, 60, 14, 18))
                rect(s, (228, 210, 161), (x + 6, 60, 2, 18))
                rect(s, (228, 210, 161), (x, 68, 14, 2))
                rect(s, (237, 215, 161), (x - 3, 81, 20, 3))
            rect(s, (222, 211, 174), (54, 101, 29, 4))
            rect(s, (183, 172, 139), (51, 105, 35, 3))
            if name == "workshop":
                rect(s, (92, 97, 83), (85, 2, 15, 29))
                rect(s, (118, 117, 95), (82, 1, 21, 5))
                rect(s, (73, 88, 78), (45, 48, 46, 10))
                for x in range(50, 87, 6):
                    rect(s, (209, 194, 144), (x, 51, 3, 3))
                if not restored:
                    rect(s, (111, 112, 92), (91, 65, 12, 3))
                    pygame.draw.line(s, (115, 112, 87), (105, 90), (98, 83), 2)
            elif restored:
                for x in (25, 101):
                    rect(s, (119, 114, 70), (x, 88, 9, 10))
                    rect(s, (82, 132, 78), (x - 3, 83, 15, 7), 2)
                    rect(s, (228, 173, 112), (x + 2, 82, 3, 3))
            return s
        if name == "pump":
            s = new((46, 54))
            pygame.draw.ellipse(s, (33, 49, 41, 55), (3, 44, 40, 8))
            rect(s, (112, 120, 98), (6, 41, 34, 8), 3)
            rect(s, (164, 162, 129), (10, 42, 26, 4))
            c = (64, 130, 124) if restored else (107, 116, 99)
            rect(s, INK, (18, 17, 13, 26))
            rect(s, c, (20, 18, 9, 25))
            rect(s, (146, 177, 149) if restored else (142, 145, 118), (20, 18, 3, 23))
            rect(s, c, (25, 18, 13, 6))
            rect(s, c, (35, 20, 5, 10))
            rect(s, (60, 72, 60), (17, 12, 13, 6))
            pygame.draw.line(s, (65, 75, 62), (18, 15), (9, 5), 3)
            rect(s, (137, 108, 71), (5, 3, 10, 4), 1)
            rect(s, (62, 85, 70), (16, 40, 17, 3))
            if restored:
                rect(s, (166, 211, 196), (36, 32, 2, 6))
                rect(s, (94, 158, 158), (30, 43, 11, 2))
            else:
                rect(s, (169, 131, 85), (24, 28, 6, 4))
            return s
        if name == "litter":
            s = new((30, 20))
            pygame.draw.ellipse(s, (40, 46, 39, 40), (1, 12, 28, 7))
            rect(s, (138, 119, 88), (3, 8, 11, 7))
            rect(s, (172, 150, 110), (4, 7, 9, 4))
            rect(s, (121, 137, 126), (16, 6, 6, 10), 1)
            rect(s, (165, 170, 144), (17, 5, 4, 3))
            rect(s, (210, 202, 169), (10, 12, 9, 5))
            rect(s, (187, 118, 92), (23, 12, 4, 4))
            return s
        if name == "crate":
            s = new((30, 30))
            pygame.draw.ellipse(s, (30, 44, 34, 55), (1, 23, 28, 6))
            rect(s, (88, 81, 58), (3, 6, 24, 21))
            rect(s, (169, 139, 92), (4, 7, 22, 18))
            for x in (6, 13, 21):
                rect(s, (127, 108, 71), (x, 8, 1, 17))
            rect(s, (199, 170, 112), (3, 7, 24, 3))
            rect(s, (127, 108, 71), (3, 22, 24, 3))
            rect(s, (80, 132, 127), (11, 12, 9, 8))
            rect(s, (224, 218, 170), (14, 13, 3, 6))
            rect(s, (224, 218, 170), (12, 15, 7, 2))
            return s
        if name == "plot":
            s = new((52, 34))
            rect(s, (121, 106, 75), (1, 10, 50, 22), 4)
            rect(s, (99, 84, 59), (4, 12, 44, 17), 2)
            for y in (15, 22, 28):
                rect(s, (146, 121, 80), (6, y, 40, 1))
            if restored:
                for x, y in ((10, 15), (23, 13), (37, 15), (16, 26), (32, 26)):
                    rect(s, (74, 122, 69), (x, y - 9, 2, 10))
                    rect(s, (106, 151, 78), (x - 4, y - 7, 4, 3))
                    rect(s, (125, 164, 86), (x + 2, y - 5, 4, 3))
                    rect(s, (235, 186, 91), (x - 1, y - 10, 4, 3))
            else:
                for x, y in ((11, 19), (33, 20), (23, 26)):
                    rect(s, (146, 138, 96), (x, y - 4, 2, 5))
                    rect(s, (146, 138, 96), (x - 2, y - 4, 4, 1))
            return s
        if name == "bench":
            s = new((54, 36))
            pygame.draw.ellipse(s, (33, 43, 35, 45), (1, 27, 52, 8))
            for x in (9, 42):
                rect(s, (66, 80, 64), (x, 10, 4, 23))
            for y in (7, 14):
                rect(s, (150, 116, 77), (4, y, 47, 5))
                rect(s, (189, 152, 101), (4, y, 47, 1))
            rect(s, (171, 134, 85), (2, 23, 51, 6))
            rect(s, (201, 165, 112), (2, 23, 51, 2))
            return s
        if name == "noticeboard":
            s = new((48, 56))
            pygame.draw.ellipse(s, (33, 43, 35, 45), (3, 49, 42, 6))
            for x in (9, 35):
                rect(s, (112, 95, 65), (x, 14, 4, 39))
            rect(s, (94, 85, 59), (3, 8, 42, 32))
            rect(s, (167, 139, 91), (6, 11, 36, 26))
            pygame.draw.polygon(s, (104, 92, 64), [(0, 10), (24, 0), (48, 10)])
            rect(s, (236, 219, 173), (10, 16, 13, 16))
            rect(s, (223, 210, 164), (27, 14, 10, 19))
            for y in (20, 24, 28):
                rect(s, (154, 143, 110), (12, y, 8, 1))
            rect(s, (176, 120, 85), (30, 18, 5, 5))
            return s
        if name == "flower":
            s = new((18, 20))
            rect(s, (75, 116, 66), (8, 7, 2, 11))
            rect(s, (110, 144, 75), (4, 12, 4, 3))
            rect(s, (110, 144, 75), (10, 10, 4, 3))
            petals = (233, 192, 119) if restored else (162, 153, 115)
            for box in ((6, 2, 6, 4), (4, 5, 4, 5), (10, 5, 4, 5), (6, 9, 6, 3)):
                rect(s, petals, box)
            rect(s, (158, 113, 65), (8, 6, 2, 3))
            return s
        if name == "deadtree":
            s = new((64, 80))
            pygame.draw.ellipse(s, (33, 53, 40, 55), (9, 66, 46, 11))
            bark, light = (92, 82, 64), (140, 126, 98)
            rect(s, bark, (28, 34, 9, 41))
            rect(s, light, (30, 38, 3, 35))
            tips = ((14, 26), (50, 22), (30, 12), (8, 24), (56, 20), (18, 10))
            for (x, y), (a, b, w) in zip(tips, (((32, 48), (14, 26), 5), ((32, 42), (50, 22), 4), ((32, 38), (30, 12), 4),
                                                ((20, 32), (8, 24), 3), ((44, 30), (56, 20), 3), ((22, 30), (18, 10), 2))):
                pygame.draw.line(s, bark, a, b, w)
            if restored:
                # The old tree wakes: young leaves and a few gold buds on every branch tip.
                for x, y in (*tips, (24, 20), (40, 16)):
                    rect(s, (120, 168, 96), (x - 3, y - 3, 7, 5), 2)
                    rect(s, (232, 196, 112), (x, y - 5, 2, 2))
            else:
                rect(s, (60, 62, 52), (24, 70, 16, 3))
                rect(s, (157, 142, 101), (44, 66, 5, 2))
            return s
        if name == "sign":
            s = new((48, 40))
            pygame.draw.ellipse(s, (33, 43, 35, 45), (2, 33, 44, 6))
            if not restored:
                # A hand-lettered protest sign, faded by weather: "What about Riverside?"
                rect(s, (112, 95, 65), (22, 12, 4, 26))
                rect(s, (94, 85, 59), (5, 3, 38, 20), 2)
                rect(s, (228, 214, 170), (7, 5, 34, 16), 2)
                for y, w in ((8, 24), (13, 18)):
                    rect(s, (150, 140, 110), (10, y, w, 2))
                rect(s, (176, 120, 85), (33, 14, 4, 4))
            else:
                # The delivery cart that replaced it: parcels packed for every street.
                rect(s, (104, 84, 56), (5, 14, 36, 14), 3)
                rect(s, (166, 134, 88), (7, 15, 32, 11), 2)
                rect(s, (104, 84, 56), (38, 8, 3, 10))
                rect(s, (104, 84, 56), (38, 8, 8, 2))
                rect(s, (84, 132, 127), (10, 8, 10, 8), 1)
                rect(s, (224, 186, 100), (22, 10, 9, 6), 1)
                for x in (13, 33):
                    pygame.draw.circle(s, (60, 66, 58), (x, 31), 5)
                    pygame.draw.circle(s, (200, 190, 150), (x, 31), 2)
            return s
        if name == "rope":
            s = new((56, 32))
            pygame.draw.ellipse(s, (33, 43, 35, 45), (0, 26, 56, 6))
            for x in (4, 48):
                rect(s, (66, 80, 64), (x, 8, 4, 22))
                rect(s, (197, 153, 74), (x - 1, 6, 6, 4), 1)
            pygame.draw.lines(s, (176, 120, 85), False, [(8, 11), (18, 16), (28, 18), (38, 16), (48, 11)], 2)
            return s
        if name == "flood":
            # Water lines left on the wall by floods nobody planned for.
            s = new((128, 112))
            fade = 0.45 if restored else 1.0
            rect(s, (110, 96, 70, int(70 * fade)), (18, 88, 96, 13))
            for x in range(18, 114, 4):
                rect(s, (92, 86, 70, int(170 * fade)), (x, 86 + (x // 4) % 2, 4, 2))
                if x % 12 == 6:
                    rect(s, (92, 86, 70, int(120 * fade)), (x, 78, 4, 1))
            return s
        if name == "soot":
            # Soot around the mill chimney; the workshop route leaves it clean.
            s = new((128, 112))
            fade = 0.0 if restored else 1.0
            rect(s, (50, 48, 44, int(215 * fade)), (82, 0, 21, 9), 2)
            rect(s, (50, 48, 44, int(130 * fade)), (86, 9, 4, 20))
            rect(s, (50, 48, 44, int(110 * fade)), (96, 9, 3, 14))
            rect(s, (70, 66, 58, int(95 * fade)), (92, 20, 16, 11), 3)
            return s
        if name == "dispute":
            # A former mill worker and a Riverside resident, apart and tense or close and calm.
            s = new((64, 36))
            xs = (12, 28) if restored else (0, 40)
            s.blit(self._person("theo", "down", 0, restored), (xs[0], 0))
            s.blit(self._person("amani", "down", 0, restored), (xs[1], 0))
            return s
        if name in ("plot_seed", "plot_sprout"):
            s = new((52, 34))
            rect(s, (121, 106, 75), (1, 10, 50, 22), 4)
            rect(s, (99, 84, 59), (4, 12, 44, 17), 2)
            for y in (15, 22, 28):
                rect(s, (146, 121, 80), (6, y, 40, 1))
            for x, y in ((10, 15), (23, 13), (37, 15), (16, 26), (32, 26)):
                if name == "plot_seed":
                    rect(s, (168, 150, 98), (x, y, 3, 2))
                    rect(s, (110, 150, 82), (x + 1, y - 2, 1, 2))
                else:
                    rect(s, (74, 122, 69), (x, y - 5, 2, 6))
                    rect(s, (106, 151, 78), (x - 3, y - 5, 4, 2))
                    rect(s, (125, 164, 86), (x + 2, y - 4, 4, 2))
            return s
        s = new((32, 24))
        pygame.draw.ellipse(s, (40, 46, 36, 40), (0, 17, 32, 6))
        pygame.draw.polygon(s, (112, 120, 103), [(2, 18), (6, 8), (19, 4), (28, 12), (30, 20), (17, 23)])
        pygame.draw.polygon(s, (150, 153, 127), [(6, 8), (19, 4), (24, 11), (11, 13)])
        rect(s, (131, 139, 111), (6, 17, 7, 2))
        return s

    def export_assets(self, folder):
        """Export the same art used in game, including the two atmosphere states."""
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        for restored in (False, True):
            suffix = "restored" if restored else "polluted"
            for name in self.NAMES:
                pygame.image.save(self.sprite(name, restored), str(folder / f"{name}_{suffix}.png"))
            for kind in ("grass", "path", "water", "bridge"):
                pygame.image.save(self.tile(kind, restored), str(folder / f"tile_{kind}_{suffix}.png"))
        # Walking frames for the player: templates for hand-drawn animation.
        for facing in self.FACINGS:
            for step in (0, 1, 2):
                pygame.image.save(self._person("player", facing, step, False), str(folder / f"player_{facing}_{step}_polluted.png"))
        # Reference sheet: every sprite, struggling village above and recovering village below.
        placements, top = [], 12
        for restored in (False, True):
            x, row = 12, 0
            for name in self.NAMES:
                sprite = self.sprite(name, restored)
                if x + sprite.get_width() > 748 and x > 12:
                    x, top, row = 12, top + row + 14, 0
                placements.append((sprite, (x, top)))
                x += sprite.get_width() + 12
                row = max(row, sprite.get_height())
            top += row + 30
        sheet = pygame.Surface((760, top), pygame.SRCALPHA)
        sheet.fill((238, 228, 200))
        for sprite, position in placements:
            sheet.blit(sprite, position)
        pygame.image.save(sheet, str(folder / "original_sprite_sheet.png"))
