"""Reusable drawing helpers for panels, bars, and text boxes."""

from __future__ import annotations

import functools

import pygame

import settings as s

PANEL_INSET = 5   # ornate panels: inner hairline distance from the border
PANEL_STUD = 6    # ornate panels: corner stud size
ORNAMENT_DIAMOND = 6


@functools.cache
def font(size: int) -> pygame.font.Font:
    """Shared default font at a given size (created once)."""
    return pygame.font.Font(None, size)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               fill: tuple = s.COLOR_DIALOGUE_BG,
               border: tuple | None = s.COLOR_ACCENT_GOLD, border_width: int = 2,
               ornate: bool = False) -> None:
    """Semi-transparent panel with an optional border.

    ``ornate`` adds an inner hairline with gold corner studs (dialogue, menus).
    """
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(fill)
    surface.blit(panel, rect)
    if not border:
        return
    pygame.draw.rect(surface, border, rect, border_width)
    if ornate:
        inner = rect.inflate(-PANEL_INSET * 2, -PANEL_INSET * 2)
        pygame.draw.rect(surface, tuple(c * 55 // 100 for c in border[:3]), inner, 1)
        for corner in (inner.topleft, inner.topright, inner.bottomleft, inner.bottomright):
            stud = pygame.Rect(0, 0, PANEL_STUD, PANEL_STUD)
            stud.center = corner
            pygame.draw.rect(surface, border, stud)


def draw_bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float,
             color: tuple, back: tuple = (60, 60, 60)) -> None:
    """Horizontal fill bar (HP, XP...) with ``ratio`` clamped to 0–1."""
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, back, rect)
    pygame.draw.rect(surface, color, (rect.x, rect.y, int(rect.w * ratio), rect.h))


@functools.cache
def _fade_strip(width: int, height: int, alpha: int, fade_down: bool) -> pygame.Surface:
    strip = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / max(1, height - 1)
        a = alpha * (1 - t if fade_down else t)
        pygame.draw.line(strip, (0, 0, 0, int(a)), (0, y), (width, y))
    return strip


def draw_fade_strip(surface: pygame.Surface, rect: pygame.Rect, alpha: int = 150,
                    fade_down: bool = True) -> None:
    """A black band that fades out downward (or upward): soft HUD backing."""
    surface.blit(_fade_strip(rect.w, rect.h, alpha, fade_down), rect)


def draw_shadowed_text(surface: pygame.Surface, text: str, text_font: pygame.font.Font,
                       pos: tuple[int, int], color: tuple = s.COLOR_WHITE) -> pygame.Rect:
    """Text with a 2px drop shadow; returns the text rect."""
    surface.blit(text_font.render(text, True, s.COLOR_BLACK), (pos[0] + 2, pos[1] + 2))
    return surface.blit(text_font.render(text, True, color), pos)


def draw_ornament_rules(surface: pygame.Surface, around: pygame.Rect, length: int = 70,
                        gap: int = 14, color: tuple = s.COLOR_ACCENT_GOLD) -> None:
    """Gold rules ending in diamonds on both sides of ``around`` (titles, subtitles)."""
    y = around.centery
    for side in (-1, 1):
        inner = around.left - gap if side < 0 else around.right + gap
        outer = inner + side * length
        pygame.draw.line(surface, color, (inner, y), (outer, y), 2)
        x = outer + side * ORNAMENT_DIAMOND
        r = ORNAMENT_DIAMOND - 1
        pygame.draw.polygon(surface, color, [(x, y - r), (x + r, y), (x, y + r), (x - r, y)])


def draw_text_box(surface: pygame.Surface, text: str, text_font: pygame.font.Font,
                  center: tuple[int, int], fill: tuple = (0, 0, 0, 180),
                  color: tuple = s.COLOR_WHITE, padding: tuple[int, int] = (20, 10)) -> None:
    """A single line of text on a tight translucent background (toasts, messages)."""
    text_surf = text_font.render(text, True, color)
    text_rect = text_surf.get_rect(center=center)
    draw_panel(surface, text_rect.inflate(*padding), fill=fill, border=None)
    surface.blit(text_surf, text_rect)


def wrap_text(text: str, text_font: pygame.font.Font, max_width: int) -> list[str]:
    """Greedy word wrap into lines that fit ``max_width`` pixels."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}" if current else word
        if current and text_font.size(candidate)[0] > max_width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines
