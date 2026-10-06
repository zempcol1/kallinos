"""Main Menu state — the animated title screen."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

import settings as s
from game.state_machine import State
from systems.sprites import laurel, title
from systems.sprites.pixel_art import lerp
from ui.widgets import draw_fade_strip, draw_ornament_rules, draw_shadowed_text, font

if TYPE_CHECKING:
    from game.game import Game


def _ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


class MainMenu(State):
    """Aegean sunset with a gilded logo and New Game / Continue / Quit.

    The scene is painted at the world's pixel size and animated (stars,
    clouds, gulls, sea glitter, golden motes from Athena's olive). The intro
    fades in, the logo drops into place and the menu appears; any key skips
    the intro. Choosing New Game fades to black before the game starts.
    """

    MENU_OPTIONS = ["New Game", "Continue", "Quit"]
    DISABLED = {"Continue"}            # needs save/load
    DISABLED_NOTICE = "No saved journey yet. Begin a new one!"

    FADE_IN_MS = 1000
    LOGO_DELAY_MS = 400
    LOGO_DROP_MS = 900
    MENU_DELAY_MS = 1300
    MENU_FADE_MS = 500
    FADE_OUT_MS = 700
    SHINE_EVERY_MS = 5200
    SHINE_MS = 1000
    NOTICE_MS = 2200
    SHAKE_MS = 300

    LOGO_Y = 92                        # logo center, screen pixels
    MENU_Y = 404
    MENU_SPACING = 42

    # (y, length, speed px/ms, start x) for drifting clouds, logical pixels
    CLOUDS = [(30, 70, 0.0016, 10), (48, 46, 0.0024, 150), (66, 92, 0.0012, 60),
              (82, 38, 0.0030, 200), (96, 60, 0.0020, 120)]
    GULLS = [(40, 0.010, 0), (52, 0.008, 90), (34, 0.012, 170)]   # (y, speed, offset)
    MOTES = 12

    def __init__(self, game: Game) -> None:
        super().__init__(game)
        self._selected = 0
        self._time = 0.0
        self._leaving_at: float | None = None
        self._notice_at = -1e9
        self._canvas = pygame.Surface((title.WIDTH, title.HEIGHT))
        self._scaled = pygame.Surface((title.WIDTH * s.SCALE, title.HEIGHT * s.SCALE))

    def enter(self, params: dict | None = None) -> None:
        self._selected = 0
        self._time = 0.0
        self._leaving_at = None
        self._notice_at = -1e9

    # ── Input ────────────────────────────────────────────────────────────────

    def handle_events(self, events: list[pygame.event.Event]) -> None:
        if self._leaving_at is not None:
            return
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if self._time < self.MENU_DELAY_MS + self.MENU_FADE_MS:
                self._time = self.MENU_DELAY_MS + self.MENU_FADE_MS   # skip the intro
                continue
            if event.key in (pygame.K_UP, pygame.K_w):
                self._selected = (self._selected - 1) % len(self.MENU_OPTIONS)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._selected = (self._selected + 1) % len(self.MENU_OPTIONS)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                self._select_option()

    def _select_option(self) -> None:
        choice = self.MENU_OPTIONS[self._selected]
        if choice in self.DISABLED:
            self._notice_at = self._time
        elif choice == "New Game":
            self._leaving_at = self._time
        elif choice == "Quit":
            self.game.quit()

    def update(self, dt: float) -> None:
        self._time += dt
        if self._leaving_at is not None and self._time - self._leaving_at >= self.FADE_OUT_MS:
            self._leaving_at = None
            self.game.new_game()

    # ── Scene ────────────────────────────────────────────────────────────────

    def _paint_scene(self) -> None:
        t = self._time
        canvas = self._canvas
        canvas.blit(title.sky(), (0, 0))
        for x, y, phase in title.stars():
            glow = 0.5 + 0.5 * math.sin(t / 700 + phase)
            if glow > 0.3:
                canvas.set_at((x, y), lerp(canvas.get_at((x, y)), (255, 246, 222), glow))
        for i, (y, length, speed, start) in enumerate(self.CLOUDS):
            x = (start + t * speed) % (title.WIDTH + length) - length
            canvas.blit(title.cloud(length, i), (round(x), y))
        canvas.blit(title.islands(), (0, 0))
        canvas.blit(title.sea(), (0, title.HORIZON))
        self._paint_glitter(canvas, t)
        canvas.blit(title.headland(), (0, 0))
        for i, (y, speed, offset) in enumerate(self.GULLS):
            x = (offset + t * speed) % (title.WIDTH + 20) - 10
            bob = round(math.sin(t / 700 + i * 2))
            canvas.blit(title.gull(int(t // 240 + i) % 2), (round(x), y + bob))
        canvas.blit(title.foreground(), (0, 0))
        self._paint_motes(canvas, t)
        pygame.transform.scale(canvas, self._scaled.get_size(), self._scaled)

    @staticmethod
    def _paint_glitter(canvas: pygame.Surface, t: float) -> None:
        """The sun's path on the water: dashes that sway and flicker."""
        sea_height = title.HEIGHT - title.HORIZON
        for row, y in enumerate(range(title.HORIZON + 1, title.HEIGHT, 2)):
            depth = (y - title.HORIZON) / sea_height
            half = title.SUN_RADIUS * (0.7 + depth * 1.8)
            color = lerp(title.GLINT, title.SEA_BANDS[3], depth * 0.85)
            for k in range(3):
                if (int(t / 170) + row * 3 + k) % 5 == 0:
                    continue
                x = title.SUN[0] + half * math.sin(row * 1.7 + k * 2.1 + t / 1500 * (1 + k * 0.3))
                w = 1 + (row + k) % 4
                pygame.draw.line(canvas, title.SUN_CORE if depth < 0.12 else color,
                                 (round(x - w / 2), y), (round(x + w / 2), y))
            # Faint glints far from the sun path, drifting with the swell
            gx = (row * 53 - t * 0.004 * (1 + depth)) % title.WIDTH
            if math.sin(t / 600 + row) > 0.55:
                glint = lerp(title.SEA_BANDS[1], title.GLINT, 0.4 - depth / 3)
                canvas.set_at((round(gx), y), glint)

    def _paint_motes(self, canvas: pygame.Surface, t: float) -> None:
        """Golden motes rising from Athena's olive, a hint of what is to come."""
        for i in range(self.MOTES):
            life = (t / 3600 + i / self.MOTES) % 1.0
            x = 14 + (i * 29) % 78 + math.sin(life * math.tau + i) * 3
            y = 112 - life * 70
            brightness = math.sin(life * math.pi)
            if 0 <= x < title.WIDTH and 0 <= y < title.HEIGHT:
                under = canvas.get_at((round(x), round(y)))
                canvas.set_at((round(x), round(y)), lerp(under, s.COLOR_TITLE_GOLD, brightness))

    # ── Rendering ────────────────────────────────────────────────────────────

    def render(self, surface: pygame.Surface) -> None:
        self._paint_scene()
        surface.blit(self._scaled, (0, 0))
        draw_fade_strip(surface, pygame.Rect(0, 0, s.SCREEN_WIDTH, 220), alpha=110)
        draw_fade_strip(surface, pygame.Rect(0, 300, s.SCREEN_WIDTH, s.SCREEN_HEIGHT - 300),
                        alpha=190, fade_down=False)

        self._render_logo(surface)
        menu_alpha = _ease_out((self._time - self.MENU_DELAY_MS) / self.MENU_FADE_MS)
        if menu_alpha > 0:
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._render_menu(layer)
            self._render_footer(layer)
            layer.set_alpha(int(255 * menu_alpha))
            surface.blit(layer, (0, 0))

        fade = 0.0
        if self._time < self.FADE_IN_MS:
            fade = 1 - self._time / self.FADE_IN_MS
        if self._leaving_at is not None:
            fade = (self._time - self._leaving_at) / self.FADE_OUT_MS
        if fade > 0:
            veil = pygame.Surface(surface.get_size())
            veil.set_alpha(int(255 * min(1.0, fade)))
            surface.blit(veil, (0, 0))

    def _render_logo(self, surface: pygame.Surface) -> None:
        progress = _ease_out((self._time - self.LOGO_DELAY_MS) / self.LOGO_DROP_MS)
        if progress <= 0:
            return
        cx = s.SCREEN_WIDTH // 2
        logo = title.logo()
        rect = logo.get_rect(center=(cx, self.LOGO_Y - round((1 - progress) * 24)))
        if progress < 1:
            logo = logo.copy()
            logo.set_alpha(int(255 * progress))
        surface.blit(logo, rect)

        # A shine sweeps across the gilded letters now and then
        since = (self._time - self.LOGO_DELAY_MS - self.LOGO_DROP_MS) % self.SHINE_EVERY_MS
        if progress >= 1 and since < self.SHINE_MS:
            band_x = -60 + (rect.w + 120) * since / self.SHINE_MS
            band = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.polygon(band, (255, 255, 255, 150),
                                [(band_x, 0), (band_x + 26, 0),
                                 (band_x - 14, rect.h), (band_x - 40, rect.h)])
            band.blit(title.logo_silhouette(), (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
            surface.blit(band, rect)

        # Greek name above, subtitle with ornaments below
        greek = font(22).render("Κ  Α  Λ  Λ  Ι  Ν  Ο  Σ", True, s.COLOR_ACCENT_GOLD)
        greek.set_alpha(int(200 * progress))
        surface.blit(greek, greek.get_rect(center=(cx, rect.top - 12)))
        sub_font = font(26)
        sub = sub_font.render("R I S E   O F   A   M O R T A L", True, s.COLOR_SAND)
        sub_rect = sub.get_rect(center=(cx, rect.bottom + 22))
        sub_shadow = sub_font.render("R I S E   O F   A   M O R T A L", True, s.COLOR_BLACK)
        for img, offset in ((sub_shadow, 2), (sub, 0)):
            img.set_alpha(int(255 * progress))
            surface.blit(img, sub_rect.move(offset, offset))
        draw_ornament_rules(surface, sub_rect)

    def _render_menu(self, surface: pygame.Surface) -> None:
        cx = s.SCREEN_WIDTH // 2
        menu_font = font(36)
        shake = 0
        since_notice = self._time - self._notice_at
        if since_notice < self.SHAKE_MS:
            shake = round(math.sin(since_notice / 25) * 5)
        for i, option in enumerate(self.MENU_OPTIONS):
            y = self.MENU_Y + i * self.MENU_SPACING
            selected = i == self._selected
            disabled = option in self.DISABLED
            if disabled:
                color = (128, 124, 140)
            elif selected:
                pulse = 0.5 + 0.5 * math.sin(self._time / 260)
                color = lerp(s.COLOR_ACCENT_GOLD, s.COLOR_TITLE_GOLD, pulse)
            else:
                color = s.COLOR_SAND
            text = menu_font.render(option, True, color)
            rect = text.get_rect(center=(cx + (shake if selected and disabled else 0), y))
            draw_shadowed_text(surface, option, menu_font, rect.topleft, color)
            if selected:
                sway = round(math.sin(self._time / 300) * 2)
                left, right = laurel(flip=True), laurel()
                surface.blit(left, left.get_rect(midright=(rect.left - 12 - sway, y)))
                surface.blit(right, right.get_rect(midleft=(rect.right + 12 + sway, y)))

        if since_notice < self.NOTICE_MS:
            notice = font(24).render(self.DISABLED_NOTICE, True, s.COLOR_TEXT_LIGHT)
            notice.set_alpha(int(255 * min(1.0, (self.NOTICE_MS - since_notice) / 400)))
            y = self.MENU_Y + len(self.MENU_OPTIONS) * self.MENU_SPACING
            surface.blit(notice, notice.get_rect(center=(cx, y)))

    def _render_footer(self, surface: pygame.Surface) -> None:
        y = s.SCREEN_HEIGHT - 26
        small = font(20)
        hint = "Up / Down  choose   ·   Enter  confirm"
        hint_surf = small.render(hint, True, s.COLOR_TEXT_DIM)
        draw_shadowed_text(surface, hint, small, hint_surf.get_rect(midtop=(s.SCREEN_WIDTH // 2,
                                                                            y)).topleft,
                           s.COLOR_TEXT_DIM)
        draw_shadowed_text(surface, s.GAME_VERSION, small, (16, y), s.COLOR_TEXT_DIM)
        copy = "© 2026 Kallinos"
        copy_surf = small.render(copy, True, s.COLOR_TEXT_DIM)
        draw_shadowed_text(surface, copy, small,
                           copy_surf.get_rect(topright=(s.SCREEN_WIDTH - 16, y)).topleft,
                           s.COLOR_TEXT_DIM)
