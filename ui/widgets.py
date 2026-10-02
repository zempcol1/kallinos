"""Reusable drawing helpers for panels, bars, and text boxes."""

from __future__ import annotations

import functools

import pygame

import settings as s


@functools.cache
def font(size: int) -> pygame.font.Font:
    """Shared default font at a given size (created once)."""
    return pygame.font.Font(None, size)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect,
               fill: tuple = s.COLOR_DIALOGUE_BG,
               border: tuple | None = s.COLOR_ACCENT_GOLD, border_width: int = 2) -> None:
    """Semi-transparent panel with an optional border."""
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    panel.fill(fill)
    surface.blit(panel, rect)
    if border:
        pygame.draw.rect(surface, border, rect, border_width)


def draw_bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float,
             color: tuple, back: tuple = (60, 60, 60)) -> None:
    """Horizontal fill bar (HP, XP...) with ``ratio`` clamped to 0–1."""
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, back, rect)
    pygame.draw.rect(surface, color, (rect.x, rect.y, int(rect.w * ratio), rect.h))


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
