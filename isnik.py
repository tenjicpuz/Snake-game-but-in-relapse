"""
SNAKE: RELAPSE EDITION
A polished Pygame Snake game with a menu, pause/restart flow, score tracking,
and optional online end-screen music fetched into memory (no local MP3 required).

Run:
    python -m pip install -r requirements.txt
    python isnik.py

Controls:
    Arrow keys / WASD : Move
    P                  : Pause / resume
    R                  : Restart after a game over
    Enter              : Start / restart
    Escape             : Return to menu / quit from menu
"""

from __future__ import annotations

import io
import json
import random
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pygame

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

APP_NAME = "SNAKE: RELAPSE EDITION"
ROWS = 25
COLS = 25
TILE = 24
BOARD_W = COLS * TILE
BOARD_H = ROWS * TILE
SIDEBAR_W = 220
WINDOW_W = BOARD_W + SIDEBAR_W
WINDOW_H = BOARD_H
FPS = 60
START_SPEED = 8
MAX_SPEED = 17

# Music is fetched from the repository and loaded from memory.
# This avoids requiring the player to download a separate MP3 file.
MUSIC_URL = (
    "https://raw.githubusercontent.com/"
    "tenjicpuz/Snake-game-but-in-relapse/main/kanibalismo.mp3"
)
MUSIC_VOLUME = 0.45
MUSIC_ENABLED = True

SAVE_PATH = Path.home() / ".snake_relapse_highscore.json"

# Palette
BG = (11, 14, 20)
PANEL = (17, 22, 31)
GRID = (25, 32, 43)
WHITE = (238, 243, 250)
MUTED = (139, 151, 169)
CYAN = (68, 220, 224)
CYAN_DARK = (28, 111, 123)
YELLOW = (255, 207, 79)
RED = (255, 91, 105)
GREEN = (91, 232, 158)
BLACK = (5, 7, 11)


def load_high_score() -> int:
    """Load the saved high score; gracefully handle a missing/corrupt file."""
    try:
        data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
        return max(0, int(data.get("high_score", 0)))
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_high_score(score: int) -> None:
    """Persist a high score in the user's home directory."""
    try:
        SAVE_PATH.write_text(
            json.dumps({"high_score": int(score)}, indent=2),
            encoding="utf-8",
        )
    except OSError:
        # The game remains playable even if the machine blocks file writes.
        pass


def fetch_online_music() -> bool:
    """Fetch online audio into RAM. Never writes the MP3 to disk."""
    if not MUSIC_ENABLED:
        return False

    try:
        request = urllib.request.Request(
            MUSIC_URL,
            headers={"User-Agent": "SnakeRelapseEdition/1.0"},
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            audio_bytes = response.read()

        if not audio_bytes:
            return False

        pygame.mixer.music.load(io.BytesIO(audio_bytes), "mp3")
        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        return True
    except (urllib.error.URLError, TimeoutError, OSError, pygame.error):
        return False


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    position: tuple[int, int],
    anchor: str = "topleft",
) -> pygame.Rect:
    """Render text with a chosen anchor."""
    image = font.render(text, True, color)
    rect = image.get_rect()
    setattr(rect, anchor, position)
    surface.blit(image, rect)
    return rect


def rounded_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    radius: int = 12,
    border_color: tuple[int, int, int] | None = None,
    border_width: int = 1,
) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border_color:
        pygame.draw.rect(
            surface, border_color, rect, width=border_width, border_radius=radius
        )


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        self.audio_available = False
        try:
            pygame.mixer.init()
            self.audio_available = True
        except pygame.error:
            # Audio devices may not be available on every system.
            self.audio_available = False

        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
        pygame.display.set_caption(APP_NAME)
        self.clock = pygame.time.Clock()

        self.font_tiny = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 17)
        self.font_medium = pygame.font.SysFont("arial", 24, bold=True)
        self.font_large = pygame.font.SysFont("arial", 42, bold=True)
        self.font_title = pygame.font.SysFont("arial", 48, bold=True)

        self.high_score = load_high_score()
        self.state = "menu"  # menu, playing, paused, game_over
        self.score = 0
        self.snake: list[tuple[int, int]] = []
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.food = (0, 0)
        self.move_timer = 0.0
        self.last_time = time.perf_counter()
        self.music_status = "Music loads on game over"
        self.new_record = False
        self.reset_round()

    def reset_round(self) -> None:
        center = (COLS // 2, ROWS // 2)
        self.snake = [center, (center[0] - 1, center[1]), (center[0] - 2, center[1])]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.move_timer = 0.0
        self.food = self.spawn_food()
        self.new_record = False

    def spawn_food(self) -> tuple[int, int]:
        free_cells = [
            (x, y)
            for y in range(ROWS)
            for x in range(COLS)
            if (x, y) not in self.snake
        ]
        return random.choice(free_cells) if free_cells else (-1, -1)

    def start_game(self) -> None:
        self.reset_round()
        self.state = "playing"
        self.music_status = "Music loads on game over"

    def end_game(self) -> None:
        self.state = "game_over"
        self.new_record = self.score > self.high_score
        if self.new_record:
            self.high_score = self.score
            save_high_score(self.high_score)

        if self.audio_available:
            self.music_status = "Loading online music..."
            pygame.mixer.music.stop()
            if fetch_online_music():
                pygame.mixer.music.play()
                self.music_status = "Online music playing"
            else:
                self.music_status = "Music unavailable (offline?)"
        else:
            self.music_status = "Audio device unavailable"

    def set_direction(self, direction: tuple[int, int]) -> None:
        # Disallow a 180-degree turn, which would cause instant self-collision.
        if direction != (-self.direction[0], -self.direction[1]):
            self.next_direction = direction

    def handle_key(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.set_direction((0, -1))
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.set_direction((0, 1))
        elif key in (pygame.K_LEFT, pygame.K_a):
            self.set_direction((-1, 0))
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.set_direction((1, 0))
        elif key == pygame.K_p:
            if self.state == "playing":
                self.state = "paused"
            elif self.state == "paused":
                self.state = "playing"
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.state in ("menu", "game_over"):
                self.start_game()
            elif self.state == "paused":
                self.state = "playing"
        elif key == pygame.K_r and self.state == "game_over":
            self.start_game()
        elif key == pygame.K_ESCAPE:
            if self.state in ("playing", "paused", "game_over"):
                if self.audio_available:
                    pygame.mixer.music.stop()
                self.state = "menu"
            else:
                pygame.event.post(pygame.event.Event(pygame.QUIT))

    def update_game(self, dt: float) -> None:
        if self.state != "playing":
            return

        speed = min(MAX_SPEED, START_SPEED + self.score // 4)
        self.move_timer += dt
        move_interval = 1.0 / speed

        while self.move_timer >= move_interval:
            self.move_timer -= move_interval
            self.direction = self.next_direction

            head_x, head_y = self.snake[0]
            dx, dy = self.direction
            new_head = (head_x + dx, head_y + dy)

            # Wall collision.
            if not (0 <= new_head[0] < COLS and 0 <= new_head[1] < ROWS):
                self.end_game()
                return

            # Moving into the tail's current cell is legal if the tail moves away.
            body_to_check = self.snake[:-1]
            if new_head in body_to_check:
                self.end_game()
                return

            self.snake.insert(0, new_head)

            if new_head == self.food:
                self.score += 1
                self.food = self.spawn_food()
                if self.food == (-1, -1):
                    self.end_game()
                    return
            else:
                self.snake.pop()

    def draw_board(self) -> None:
        board = pygame.Rect(0, 0, BOARD_W, BOARD_H)
        pygame.draw.rect(self.screen, BG, board)

        # Subtle grid gives the board a deliberate arcade aesthetic.
        for x in range(0, BOARD_W + 1, TILE):
            pygame.draw.line(self.screen, GRID, (x, 0), (x, BOARD_H), 1)
        for y in range(0, BOARD_H + 1, TILE):
            pygame.draw.line(self.screen, GRID, (0, y), (BOARD_W, y), 1)

        # Food has a small inset so it doesn't touch grid lines.
        fx, fy = self.food
        if fx >= 0:
            food_rect = pygame.Rect(
                fx * TILE + 5, fy * TILE + 5, TILE - 10, TILE - 10
            )
            pygame.draw.rect(self.screen, YELLOW, food_rect, border_radius=6)
            pygame.draw.circle(
                self.screen, (255, 238, 168),
                (food_rect.x + 5, food_rect.y + 4), 2
            )

        # Draw body first, then a brighter head.
        for index, (x, y) in enumerate(reversed(self.snake)):
            rect = pygame.Rect(x * TILE + 2, y * TILE + 2, TILE - 4, TILE - 4)
            color = CYAN if index == len(self.snake) - 1 else CYAN_DARK
            pygame.draw.rect(self.screen, color, rect, border_radius=6)

        if self.snake:
            hx, hy = self.snake[0]
            head = pygame.Rect(hx * TILE + 2, hy * TILE + 2, TILE - 4, TILE - 4)
            pygame.draw.rect(self.screen, CYAN, head, border_radius=7)
            # Eyes face the current movement direction.
            eye_color = BLACK
            if self.direction == (1, 0):
                eyes = [(head.right - 6, head.y + 7), (head.right - 6, head.bottom - 7)]
            elif self.direction == (-1, 0):
                eyes = [(head.x + 6, head.y + 7), (head.x + 6, head.bottom - 7)]
            elif self.direction == (0, -1):
                eyes = [(head.x + 7, head.y + 6), (head.right - 7, head.y + 6)]
            else:
                eyes = [(head.x + 7, head.bottom - 6), (head.right - 7, head.bottom - 6)]
            for eye in eyes:
                pygame.draw.circle(self.screen, eye_color, eye, 2)

    def draw_sidebar(self) -> None:
        x = BOARD_W
        pygame.draw.rect(self.screen, PANEL, (x, 0, SIDEBAR_W, WINDOW_H))
        pygame.draw.line(self.screen, GRID, (x, 0), (x, WINDOW_H), 2)

        left = x + 22
        draw_text(self.screen, "RELAPSE", self.font_medium, CYAN, (left, 26))
        draw_text(self.screen, "SNAKE ARCADE", self.font_tiny, MUTED, (left, 55))

        rounded_panel(self.screen, pygame.Rect(left, 94, SIDEBAR_W - 44, 88), BG, 12, GRID)
        draw_text(self.screen, "CURRENT SCORE", self.font_tiny, MUTED, (left + 14, 108))
        draw_text(self.screen, f"{self.score:04d}", self.font_large, WHITE, (left + 12, 128))

        rounded_panel(self.screen, pygame.Rect(left, 196, SIDEBAR_W - 44, 72), BG, 12, GRID)
        draw_text(self.screen, "BEST SCORE", self.font_tiny, MUTED, (left + 14, 208))
        draw_text(self.screen, f"{self.high_score:04d}", self.font_medium, YELLOW, (left + 14, 231))

        draw_text(self.screen, "CONTROLS", self.font_small, WHITE, (left, 300))
        controls = [
            ("MOVE", "Arrows / WASD"),
            ("PAUSE", "P"),
            ("START", "Enter / Space"),
            ("MENU", "Esc"),
        ]
        y = 332
        for label, value in controls:
            draw_text(self.screen, label, self.font_tiny, MUTED, (left, y))
            draw_text(self.screen, value, self.font_tiny, WHITE, (left, y + 19))
            y += 47

        pygame.draw.line(self.screen, GRID, (left, 548), (WINDOW_W - 22, 548), 1)
        draw_text(self.screen, "ONLINE AUDIO", self.font_tiny, MUTED, (left, 564))
        status_color = GREEN if "playing" in self.music_status.lower() else MUTED
        status_lines = self.wrap_text(self.music_status, self.font_tiny, SIDEBAR_W - 48)
        for i, line in enumerate(status_lines[:3]):
            draw_text(self.screen, line, self.font_tiny, status_color, (left, 586 + i * 18))

        draw_text(self.screen, "RELAPSE EDITION  •  v1.0", self.font_tiny, MUTED,
                  (left, WINDOW_H - 28))

    @staticmethod
    def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if font.size(candidate)[0] <= max_width:
                current = candidate
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def draw_overlay(self, title: str, subtitle: str, accent=CYAN) -> None:
        overlay = pygame.Surface((BOARD_W, BOARD_H), pygame.SRCALPHA)
        overlay.fill((3, 6, 10, 190))
        self.screen.blit(overlay, (0, 0))

        card = pygame.Rect(42, 188, BOARD_W - 84, 220)
        rounded_panel(self.screen, card, PANEL, 18, GRID, 2)
        draw_text(self.screen, title, self.font_title, accent,
                  (BOARD_W // 2, card.y + 44), "midtop")
        draw_text(self.screen, subtitle, self.font_small, WHITE,
                  (BOARD_W // 2, card.y + 112), "midtop")
        draw_text(self.screen, "ENTER  /  SPACE  TO CONTINUE",
                  self.font_tiny, MUTED, (BOARD_W // 2, card.y + 163), "midtop")

    def draw(self) -> None:
        self.screen.fill(BG)
        self.draw_board()
        self.draw_sidebar()

        if self.state == "menu":
            self.draw_overlay("SNAKE: RELAPSE", "A classic arcade run. How long can you survive?")
            draw_text(self.screen, "COLLECT FOOD  •  AVOID WALLS  •  BEAT YOUR BEST",
                      self.font_tiny, MUTED, (BOARD_W // 2, 426), "midtop")
        elif self.state == "paused":
            self.draw_overlay("PAUSED", "Take a breath. Your run is waiting.", YELLOW)
        elif self.state == "game_over":
            self.draw_overlay("GAME OVER", f"Final score: {self.score}", RED)
            if self.new_record:
                draw_text(self.screen, "NEW PERSONAL BEST!",
                          self.font_small, YELLOW, (BOARD_W // 2, 414), "midtop")
            draw_text(self.screen, "Press R to retry  •  Esc for menu",
                      self.font_tiny, MUTED, (BOARD_W // 2, 444), "midtop")

        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            now = time.perf_counter()
            dt = min(now - self.last_time, 0.1)
            self.last_time = now

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key(event.key)

            self.update_game(dt)
            self.draw()
            self.clock.tick(FPS)

        if self.audio_available:
            pygame.mixer.music.stop()
        pygame.quit()


def main() -> None:
    try:
        SnakeGame().run()
    except KeyboardInterrupt:
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    main()
