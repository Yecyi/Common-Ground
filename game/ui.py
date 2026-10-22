"""Drawing helpers for the resolution-independent interface."""
from __future__ import annotations

import math

import pygame

INK = (32, 54, 47)
MUTED = (100, 113, 101)
PAPER = (247, 243, 228)
CREAM = (232, 227, 208)
GREEN = (42, 101, 79)
GOLD = (197, 153, 74)
WHITE = (255, 253, 245)


class UI:
    def __init__(self, surface):
        self.surface = surface
        self.fonts = {}
        self.large = False
        self.contrast = False
        self.buttons = []
        self.focus = 0
        self.mouse = (-1, -1)

    def font(self, size, bold=False):
        size = round(size * (1.13 if self.large else 1))
        key = size, bold
        if key not in self.fonts:
            self.fonts[key] = pygame.font.SysFont("segoeui,dejavusans,arial", size, bold=bold)
        return self.fonts[key]

    def text(self, text, pos, size=22, color=INK, bold=False, anchor="topleft"):
        if self.contrast:
            if color==MUTED:color=(44,58,48)
            elif color==INK:color=(10,24,18)
        img = self.font(size, bold).render(str(text), True, color)
        rect = img.get_rect(**{anchor: pos})
        self.surface.blit(img, rect)
        return rect

    def lines(self, text, width, size=22, bold=False):
        font = self.font(size, bold)
        output = []
        for paragraph in str(text).split("\n"):
            line = ""
            for word in paragraph.split():
                trial = (line + " " + word).strip()
                if font.size(trial)[0] > width and line:
                    output.append(line)
                    line = word
                else:
                    line = trial
            output.append(line)
        return output

    def paragraph(self, text, pos, width, size=22, color=INK, bold=False, gap=5):
        x, y = pos
        height = self.font(size, bold).get_linesize() + gap
        for line in self.lines(text, width, size, bold):
            self.text(line, (x, y), size, color, bold)
            y += height
        return y

    def panel(self, rect, color=PAPER, radius=18, border=True):
        rect = pygame.Rect(rect)
        shadow = pygame.Surface((rect.w+16, rect.h+20), pygame.SRCALPHA)
        pygame.draw.rect(shadow, (15, 29, 25, 65), (4, 8, rect.w, rect.h), border_radius=radius)
        self.surface.blit(shadow, (rect.x-4, rect.y-4))
        pygame.draw.rect(self.surface, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(self.surface, INK if self.contrast else (212, 214, 194), rect, 2 if self.contrast else 1, border_radius=radius)

    def shade(self, alpha=110):
        layer = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        layer.fill((14, 30, 27, alpha))
        self.surface.blit(layer, (0, 0))

    def begin(self):
        self.buttons = []

    def button(self, label, rect, action, hint="", primary=False, enabled=True, number=None, size=22):
        rect = pygame.Rect(rect)
        index = len(self.buttons)
        self.buttons.append((rect, action, enabled))
        active = enabled and (rect.collidepoint(self.mouse) or self.focus == index)
        color = GREEN if primary else WHITE
        if active:
            color = (31, 78, 61) if primary else (227, 233, 212)
        if not enabled:
            color = (224, 223, 210)
        pygame.draw.rect(self.surface, color, rect, border_radius=10)
        pygame.draw.rect(self.surface, INK if self.contrast else GOLD if active else (197, 205, 184), rect, 3 if self.contrast and active else 2 if active or self.contrast else 1, border_radius=10)
        fg = WHITE if primary else INK
        if not enabled:
            fg = MUTED
        left = rect.x + 18
        if number is not None:
            pygame.draw.circle(self.surface, GREEN, (left+13, rect.centery), 16)
            self.text(number, (left+13, rect.centery), 17, WHITE, True, "center")
            left += 40
        if hint:
            lines = self.lines(label, rect.right-left-15, 21, True)
            y = rect.y + 12
            for line in lines:
                self.text(line, (left, y), 21, fg, True)
                y += self.font(21, True).get_linesize() + 1
            for line in self.lines(hint, rect.right-left-15, 17):
                self.text(line, (left, y+3), 17, WHITE if primary else MUTED)
                y += self.font(17).get_linesize() + 1
        else:
            self.text(label, (left, rect.centery), size, fg, True, "midleft")
        return rect

    def selected(self):
        if self.buttons:
            self.focus %= len(self.buttons)
            _, action, enabled = self.buttons[self.focus]
            return action if enabled else None

    def clicked(self, pos):
        for i, (rect, action, enabled) in enumerate(self.buttons):
            if enabled and rect.collidepoint(pos):
                self.focus = i
                return action
        return None

    def keycap(self, key, pos, label=""):
        x, y = pos
        w = max(30, self.font(16, True).size(key)[0]+15)
        pygame.draw.rect(self.surface, (223, 228, 208), (x, y, w, 26), border_radius=5)
        self.text(key, (x+w/2, y+12), 16, INK, True, "center")
        if label:
            self.text(label, (x+w+8, y+1), 18, MUTED)
        return x+w+8 + self.font(18).size(label)[0]

    def symbol(self, kind, center, color, scale=1):
        x, y = center
        if kind == "environment":
            pygame.draw.ellipse(self.surface, color, (x-9*scale, y-13*scale, 19*scale, 25*scale))
            pygame.draw.line(self.surface, PAPER, (x-5*scale,y+10*scale),(x+5*scale,y-7*scale),2)
        elif kind == "equity":
            pygame.draw.circle(self.surface, color, (int(x-9*scale),int(y-5*scale)), int(6*scale),2)
            pygame.draw.circle(self.surface, color, (int(x+9*scale),int(y-5*scale)), int(6*scale),2)
            pygame.draw.arc(self.surface, color, (x-20*scale,y-3*scale,24*scale,23*scale),0,3.14,3)
            pygame.draw.arc(self.surface, color, (x-4*scale,y-3*scale,24*scale,23*scale),0,3.14,3)
        else:
            for radius in (5, 11, 17):
                pygame.draw.circle(self.surface,color,(int(x),int(y)),int(radius*scale),2)

    def vital(self, kind, center, value, color):
        """A living symbol for one community value: it grows, fills or brightens as the value rises.

        A sapling for the environment, a ring of seats around a table for equity,
        and a lantern whose light widens for resilience.
        """
        x, y = center
        s = self.surface
        edge = INK if self.contrast else (92, 104, 90)
        if kind == "environment":
            pygame.draw.ellipse(s, (176, 164, 126), (x - 18, y + 16, 36, 10))
            height = 7 + value * .27
            top = y + 21 - height
            pygame.draw.line(s, (99, 84, 55), (x, y + 21), (x, top), 3)
            for i in range(1 + int(value // 16)):
                side = -1 if i % 2 == 0 else 1
                ly = y + 19 - (i + 1) * height / (2 + int(value // 16))
                width = 8 + int(value // 20)
                pygame.draw.ellipse(s, color, (x - 1 - width if side < 0 else x + 1, ly - 3, width, 6))
            pygame.draw.circle(s, color, (x, round(top)), 3 + int(value // 25))
            if value >= 70:
                for dx, dy in ((-4, -4), (4, -2), (0, -7)):
                    pygame.draw.circle(s, (233, 191, 105), (x + dx, round(top) + dy), 2)
        elif kind == "equity":
            seats = 6
            filled = round(value / 100 * seats)
            pygame.draw.ellipse(s, (205, 176, 126), (x - 11, y - 3, 22, 13))
            pygame.draw.ellipse(s, edge, (x - 11, y - 3, 22, 13), 1)
            for i in range(seats):
                angle = math.tau * i / seats - math.pi / 2
                px, py = round(x + math.cos(angle) * 20), round(y + 3 + math.sin(angle) * 15)
                if i < filled:
                    pygame.draw.circle(s, color, (px, py - 2), 4)
                    pygame.draw.rect(s, color, (px - 4, py + 2, 8, 4), border_radius=2)
                else:
                    pygame.draw.circle(s, (160, 160, 140), (px, py), 4, 1)
        else:
            glow = pygame.Surface((80, 80), pygame.SRCALPHA)
            radius = 12 + value * .26
            for layer in range(4):
                pygame.draw.circle(glow, (*color, 22 + layer * 12), (40, 40), round(radius * (1 - layer * .2)))
            s.blit(glow, (x - 40, y - 40 + 2))
            pygame.draw.arc(s, edge, (x - 6, y - 17, 12, 12), 0, math.pi, 2)
            pygame.draw.rect(s, edge, (x - 9, y - 9, 18, 3), border_radius=1)
            pygame.draw.rect(s, (236, 226, 188), (x - 7, y - 6, 14, 17), border_radius=3)
            pygame.draw.rect(s, edge, (x - 7, y - 6, 14, 17), 2, border_radius=3)
            pygame.draw.ellipse(s, (247, 205, 104), (x - 3, y - 1, 6, 9))
            pygame.draw.rect(s, edge, (x - 9, y + 11, 18, 3), border_radius=1)

    def tooltip(self, lines, anchor):
        """A small readable card; the first line is bold."""
        width = max(self.font(17, i == 0).size(line)[0] for i, line in enumerate(lines)) + 28
        height = 16 + len(lines) * 24
        rect = pygame.Rect(anchor, (width, height))
        rect.right = min(rect.right, 1266)
        self.panel(rect, PAPER, 8)
        for i, line in enumerate(lines):
            self.text(line, (rect.x + 14, rect.y + 9 + i * 24), 17, INK if i == 0 else MUTED, i == 0)
