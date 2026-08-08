import pygame
import random
import sys
import os
import json
import math
import numpy as np

CELL_SIZE = 20
GRID_COLS = 40
GRID_ROWS = 25
HEADER_HEIGHT = 100
PLAY_WIDTH = CELL_SIZE * GRID_COLS
PLAY_HEIGHT = CELL_SIZE * GRID_ROWS
WIDTH = PLAY_WIDTH
HEIGHT = PLAY_HEIGHT + HEADER_HEIGHT
FPS = 60

HIGHSCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "snake_highscore.json")

COL_BG_TOP = (10, 12, 30)
COL_BG_BOTTOM = (24, 10, 38)
COL_GRID_LIGHT = (34, 40, 66)
COL_GRID_DARK = (26, 31, 54)
COL_BORDER = (90, 220, 170)
COL_HEAD = (140, 250, 180)
COL_TAIL = (25, 120, 85)
COL_FOOD = (255, 95, 95)
COL_FOOD_GLOW = (255, 150, 90)
COL_TEXT = (232, 236, 245)
COL_TEXT_DIM = (145, 155, 180)
COL_ACCENT = (100, 220, 255)
COL_DANGER = (255, 80, 80)
COL_PANEL = (16, 18, 34)

MOVE_INTERVAL_BASE = 0.13
MOVE_INTERVAL_MIN = 0.055
SPEEDUP_EVERY = 30      # points
SPEEDUP_AMOUNT = 0.008

MENU, PLAYING, PAUSED, GAMEOVER = range(4)

def _tone(freq, duration_ms, volume=0.4, sample_rate=44100):
    n = max(1, int(sample_rate * duration_ms / 1000))
    t = np.linspace(0, duration_ms / 1000, n, False)
    wave = np.sin(freq * t * 2 * np.pi)
    fade_len = max(1, int(n * 0.08))
    env = np.ones(n)
    env[:fade_len] = np.linspace(0, 1, fade_len)
    env[-fade_len:] = np.linspace(1, 0, fade_len)
    wave *= env
    audio = (wave * volume * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack((audio, audio)))
    return pygame.sndarray.make_sound(stereo)


def _sweep(f_start, f_end, duration_ms, volume=0.4, sample_rate=44100):
    n = max(1, int(sample_rate * duration_ms / 1000))
    t = np.linspace(0, duration_ms / 1000, n, False)
    freqs = np.linspace(f_start, f_end, n)
    phase = np.cumsum(2 * np.pi * freqs / sample_rate)
    wave = np.sin(phase)
    fade_len = max(1, int(n * 0.05))
    env = np.ones(n)
    env[:fade_len] = np.linspace(0, 1, fade_len)
    env[-fade_len:] = np.linspace(1, 0, fade_len)
    wave *= env
    audio = (wave * volume * 32767).astype(np.int16)
    stereo = np.ascontiguousarray(np.column_stack((audio, audio)))
    return pygame.sndarray.make_sound(stereo)


class SoundManager:
 
    def __init__(self):
        self.enabled = True
        self.available = False
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.eat_sfx = _sweep(520, 1050, 110, 0.35)
            self.gameover_sfx = _sweep(420, 70, 550, 0.45)
            self.start_sfx = _tone(700, 130, 0.30)
            self.turn_sfx = _tone(260, 35, 0.10)
            self.pause_sfx = _tone(500, 90, 0.20)
            self.available = True
        except Exception:
            self.available = False

    def play(self, sound):
        if self.available and self.enabled:
            try:
                sound.play()
            except Exception:
                pass

    def toggle(self):
        self.enabled = not self.enabled


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "age", "color", "radius")

    def __init__(self, x, y, color):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(60, 200)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.life = random.uniform(0.35, 0.75)
        self.age = 0.0
        self.color = color
        self.radius = random.uniform(2, 4)

    def update(self, dt):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= 0.90
        self.vy *= 0.90

    def alive(self):
        return self.age < self.life

    def draw(self, surf):
        t = max(0.0, 1 - (self.age / self.life))
        alpha = int(255 * t)
        r = max(1, int(self.radius * t * 2))
        s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (r, r), r)
        surf.blit(s, (self.x - r, self.y - r))


class SnakeGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Snake with Dani")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.SysFont("consolas", 54, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 28, bold=True)
        self.font_small = pygame.font.SysFont("consolas", 18)
        self.font_score = pygame.font.SysFont("consolas", 24, bold=True)

        self.sound = SoundManager()
        self.high_score = self.load_high_score()

        self.stars = [
            (random.randint(0, WIDTH), random.randint(0, HEADER_HEIGHT - 10),
             random.uniform(1.0, 2.4), random.uniform(0, math.pi * 2))
            for _ in range(40)
        ]

        self.state = MENU
        self.time_elapsed = 0.0
        self.reset_game()

    def load_high_score(self):
        try:
            with open(HIGHSCORE_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("high_score", 0))
        except Exception:
            return 0

    def save_high_score(self):
        try:
            with open(HIGHSCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score}, f)
        except Exception:
            pass

    def reset_game(self):
        cx, cy = GRID_COLS // 2, GRID_ROWS // 2
        self.snake = [(cx - 1, cy), (cx - 2, cy), (cx - 3, cy)]
        self.direction = (1, 0)
        self.next_direction = (1, 0)
        self.score = 0
        self.move_timer = 0.0
        self.move_interval = MOVE_INTERVAL_BASE
        self.particles = []
        self.flash_timer = 0.0
        self.food = self.spawn_food()
        self.food_pulse = 0.0

    def spawn_food(self):
        occupied = set(self.snake)
        empties = [
            (x, y)
            for x in range(GRID_COLS)
            for y in range(GRID_ROWS)
            if (x, y) not in occupied
        ]
        if not empties:
            return self.snake[0]
        return random.choice(empties)

    # input dengy yahan
    def handle_keydown(self, key):
        if self.state == MENU:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.reset_game()
                self.state = PLAYING
                self.sound.play(self.sound.start_sfx)
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif self.state == PLAYING:
            if key in (pygame.K_UP, pygame.K_w) and self.direction != (0, 1):
                self.next_direction = (0, -1)
            elif key in (pygame.K_DOWN, pygame.K_s) and self.direction != (0, -1):
                self.next_direction = (0, 1)
            elif key in (pygame.K_LEFT, pygame.K_a) and self.direction != (1, 0):
                self.next_direction = (-1, 0)
            elif key in (pygame.K_RIGHT, pygame.K_d) and self.direction != (-1, 0):
                self.next_direction = (1, 0)
            elif key == pygame.K_p:
                self.state = PAUSED
                self.sound.play(self.sound.pause_sfx)
            elif key == pygame.K_m:
                self.sound.toggle()
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif self.state == PAUSED:
            if key == pygame.K_p:
                self.state = PLAYING
                self.sound.play(self.sound.pause_sfx)
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

        elif self.state == GAMEOVER:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                self.reset_game()
                self.state = PLAYING
                self.sound.play(self.sound.start_sfx)
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def update(self, dt):
        self.time_elapsed += dt
        self.food_pulse += dt

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive()]

        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)

        if self.state != PLAYING:
            return

        self.move_timer += dt
        if self.move_timer >= self.move_interval:
            self.move_timer = 0.0
            self.step()

    def step(self):
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (head_x + dx, head_y + dy)

        # wall collision sy bvhanay jklye
        if not (0 <= new_head[0] < GRID_COLS and 0 <= new_head[1] < GRID_ROWS):
            self.trigger_game_over()
            return

        body_check = self.snake if new_head == self.food else self.snake[:-1]
        if new_head in body_check:
            self.trigger_game_over()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 10
            self.high_score = max(self.high_score, self.score)
            self.spawn_particles(new_head, COL_FOOD_GLOW)
            self.sound.play(self.sound.eat_sfx)
            self.food = self.spawn_food()
            self.move_interval = max(
                MOVE_INTERVAL_MIN,
                MOVE_INTERVAL_BASE - (self.score // SPEEDUP_EVERY) * SPEEDUP_AMOUNT,
            )
        else:
            self.snake.pop()

    def spawn_particles(self, grid_pos, color, count=18):
        px = grid_pos[0] * CELL_SIZE + CELL_SIZE / 2
        py = HEADER_HEIGHT + grid_pos[1] * CELL_SIZE + CELL_SIZE / 2
        for _ in range(count):
            self.particles.append(Particle(px, py, color))

    def trigger_game_over(self):
        self.state = GAMEOVER
        self.flash_timer = 0.35
        self.sound.play(self.sound.gameover_sfx)
        head = self.snake[0]
        self.spawn_particles(head, COL_DANGER, count=26)
        if self.score >= self.high_score:
            self.high_score = self.score
            self.save_high_score()

    def grid_to_px(self, gx, gy):
        return gx * CELL_SIZE, HEADER_HEIGHT + gy * CELL_SIZE

    def draw_background(self):
        # vertical gradient
        for y in range(HEIGHT):
            t = y / HEIGHT
            r = int(COL_BG_TOP[0] + (COL_BG_BOTTOM[0] - COL_BG_TOP[0]) * t)
            g = int(COL_BG_TOP[1] + (COL_BG_BOTTOM[1] - COL_BG_TOP[1]) * t)
            b = int(COL_BG_TOP[2] + (COL_BG_BOTTOM[2] - COL_BG_TOP[2]) * t)
            pygame.draw.line(self.screen, (r, g, b), (0, y), (WIDTH, y))

        # twinkling stars in header strip
        for (x, y, size, phase) in self.stars:
            twinkle = (math.sin(self.time_elapsed * 2 + phase) + 1) / 2
            alpha = int(80 + twinkle * 160)
            s = pygame.Surface((int(size * 2) + 1, int(size * 2) + 1), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 255, 255, alpha), (int(size), int(size)), max(1, int(size)))
            self.screen.blit(s, (x, y))

    def draw_playfield(self):
        # checkerboard
        for gx in range(GRID_COLS):
            for gy in range(GRID_ROWS):
                px, py = self.grid_to_px(gx, gy)
                color = COL_GRID_LIGHT if (gx + gy) % 2 == 0 else COL_GRID_DARK
                pygame.draw.rect(self.screen, color, (px, py, CELL_SIZE, CELL_SIZE))

        # glowing border around playfield
        for i, alpha in enumerate([60, 40, 25]):
            s = pygame.Surface((PLAY_WIDTH + i * 8, PLAY_HEIGHT + i * 8), pygame.SRCALPHA)
            pygame.draw.rect(
                s, (*COL_BORDER, alpha), s.get_rect(), width=2, border_radius=10
            )
            self.screen.blit(s, (-i * 4, HEADER_HEIGHT - i * 4))
        pygame.draw.rect(
            self.screen, COL_BORDER, (0, HEADER_HEIGHT, PLAY_WIDTH, PLAY_HEIGHT), width=2
        )

    def draw_snake(self):
        n = len(self.snake)
        for i, (gx, gy) in enumerate(self.snake):
            px, py = self.grid_to_px(gx, gy)
            t = i / max(1, n - 1)
            color = tuple(
                int(COL_HEAD[c] + (COL_TAIL[c] - COL_HEAD[c]) * t) for c in range(3)
            )
            rect = (px + 1, py + 1, CELL_SIZE - 2, CELL_SIZE - 2)
            radius = 8 if i == 0 else 6
            pygame.draw.rect(self.screen, color, rect, border_radius=radius)

            if i == 0:
                # eyes, oriented with direction of travel
                dx, dy = self.direction
                cx, cy = px + CELL_SIZE / 2, py + CELL_SIZE / 2
                perp = (-dy, dx)
                eye_off = 4
                for sign in (-1, 1):
                    ex = cx + dx * 4 + perp[0] * eye_off * sign
                    ey = cy + dy * 4 + perp[1] * eye_off * sign
                    pygame.draw.circle(self.screen, (15, 20, 25), (int(ex), int(ey)), 2)

    def draw_food(self):
        gx, gy = self.food
        px, py = self.grid_to_px(gx, gy)
        cx, cy = px + CELL_SIZE / 2, py + CELL_SIZE / 2
        pulse = (math.sin(self.food_pulse * 6) + 1) / 2

        glow_r = int(CELL_SIZE * (0.9 + pulse * 0.35))
        s = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*COL_FOOD_GLOW, 70), (glow_r, glow_r), glow_r)
        self.screen.blit(s, (cx - glow_r, cy - glow_r))

        r = int(CELL_SIZE * 0.38 + pulse * 1.5)
        pygame.draw.circle(self.screen, COL_FOOD, (int(cx), int(cy)), r)
        pygame.draw.circle(
            self.screen, (255, 220, 210), (int(cx - r * 0.35), int(cy - r * 0.35)), max(1, r // 3)
        )

    def draw_particles(self):
        for p in self.particles:
            p.draw(self.screen)

    def draw_header(self):
        panel = pygame.Surface((WIDTH, HEADER_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(panel, (*COL_PANEL, 210), panel.get_rect())
        self.screen.blit(panel, (0, 0))
        pygame.draw.line(self.screen, COL_BORDER, (0, HEADER_HEIGHT - 1), (WIDTH, HEADER_HEIGHT - 1), 2)

        title = self.font_med.render("SNAKE", True, COL_ACCENT)
        self.screen.blit(title, (20, 18))

        score_txt = self.font_score.render(f"SCORE  {self.score}", True, COL_TEXT)
        self.screen.blit(score_txt, (20, 58))

        hs_txt = self.font_score.render(f"BEST  {self.high_score}", True, COL_TEXT_DIM)
        self.screen.blit(hs_txt, (WIDTH - hs_txt.get_width() - 20, 58))

        mute_txt = self.font_small.render(
            "SOUND: ON (M)" if self.sound.enabled else "SOUND: OFF (M)", True, COL_TEXT_DIM
        )
        self.screen.blit(mute_txt, (WIDTH - mute_txt.get_width() - 20, 22))

    def draw_center_text_block(self, lines, y_start, gap=44):
        y = y_start
        for text, font, color in lines:
            surf = font.render(text, True, color)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            self.screen.blit(surf, rect)
            y += gap

    def draw_menu(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 130), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))

        glow = (math.sin(self.time_elapsed * 3) + 1) / 2
        title_color = tuple(int(COL_ACCENT[c] * (0.7 + glow * 0.3)) for c in range(3))

        self.draw_center_text_block(
            [
                ("SNAKE", self.font_big, title_color),
                ("Arrow Keys / WASD to move", self.font_small, COL_TEXT_DIM),
                ("Press SPACE to Start", self.font_med, COL_TEXT),
                (f"Best Score: {self.high_score}", self.font_small, COL_TEXT_DIM),
            ],
            HEIGHT // 2 - 100,
            56,
        )

    def draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))
        self.draw_center_text_block(
            [
                ("PAUSED", self.font_big, COL_ACCENT),
                ("Press P to Resume", self.font_med, COL_TEXT),
            ],
            HEIGHT // 2 - 30,
            56,
        )

    def draw_gameover(self):
        if self.flash_timer > 0:
            alpha = int(180 * (self.flash_timer / 0.35))
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.rect(overlay, (*COL_DANGER, alpha), overlay.get_rect())
            self.screen.blit(overlay, (0, 0))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))

        new_best = " (NEW BEST!)" if self.score >= self.high_score and self.score > 0 else ""
        self.draw_center_text_block(
            [
                ("GAME OVER", self.font_big, COL_DANGER),
                (f"Score: {self.score}{new_best}", self.font_med, COL_TEXT),
                (f"Best: {self.high_score}", self.font_small, COL_TEXT_DIM),
                ("Press SPACE to Restart", self.font_med, COL_ACCENT),
            ],
            HEIGHT // 2 - 110,
            50,
        )

    def draw(self):
        self.draw_background()
        self.draw_playfield()
        self.draw_food()
        self.draw_snake()
        self.draw_particles()
        self.draw_header()

        if self.state == MENU:
            self.draw_menu()
        elif self.state == PAUSED:
            self.draw_pause()
        elif self.state == GAMEOVER:
            self.draw_gameover()

        pygame.display.flip()

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    self.handle_keydown(event.key)

            self.update(dt)
            self.draw()


if __name__ == "__main__":
    game = SnakeGame()
    game.run()