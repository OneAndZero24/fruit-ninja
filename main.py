import pygame
import random
import math
import os
import sys
import json
from collections import deque

pygame.init()

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Ninja - Enhanced")

# Load assets
bg = pygame.transform.scale(pygame.image.load("imgs/background.png"), (WIDTH, HEIGHT))
fruit_images = [pygame.image.load(name) for name in ["imgs/apple.png", "imgs/banana.png", "imgs/orange.png"]]
fruit_images = [pygame.transform.scale(img, (64, 64)) for img in fruit_images]
bomb_image = pygame.transform.scale(pygame.image.load("imgs/bomb.png"), (64, 64))

font = pygame.font.SysFont("Arial", 32)
large_font = pygame.font.SysFont("Arial", 48)

SAVE_PATH = "save.json"
best_score = 0
if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r") as f:
        best_score = json.load(f).get("best_score", 0)

clock = pygame.time.Clock()
trail = deque(maxlen=15)
SLASH_RADIUS = 20

score = 0
lives = 3
game_over = False
splash_effects = []
split_fruits = []
combo_hits = []
combo_display = []

class Fruit:
    def __init__(self, is_bomb=False):
        self.is_bomb = is_bomb
        self.image = bomb_image if is_bomb else random.choice(fruit_images)
        self.original = self.image
        self.x = random.randint(100, WIDTH - 100)
        self.y = HEIGHT + 50
        self.speed_x = random.uniform(-3, 3)
        self.speed_y = random.uniform(-15, -20)
        self.gravity = 0.3
        self.alive = True
        self.angle = 0
        self.spin = random.uniform(-3, 3)

    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.speed_y += self.gravity
        self.angle = (self.angle + self.spin) % 360

    def draw(self):
        if self.alive:
            rotated = pygame.transform.rotate(self.original, self.angle)
            rect = rotated.get_rect(center=(self.x + 32, self.y + 32))
            screen.blit(rotated, rect.topleft)

    def is_off_screen(self):
        return self.y > HEIGHT + 64

    def is_hit_by_trail(self, trail):
        for pos in trail:
            dist = math.hypot(pos[0] - (self.x + 32), pos[1] - (self.y + 32))
            if dist < SLASH_RADIUS + 32:
                return True
        return False

class SplitFruit:
    def __init__(self, img, pos, direction):
        self.image = pygame.transform.scale(img, (32, 32))
        self.x, self.y = pos
        self.vx = direction * 5
        self.vy = -5
        self.gravity = 0.2
        self.lifetime = 30

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self):
        screen.blit(self.image, (self.x, self.y))

def draw_splashes():
    for splash in splash_effects:
        pygame.draw.circle(screen, splash["color"], splash["pos"], splash["radius"])
        splash["radius"] += 2
        splash["lifetime"] -= 1
    splash_effects[:] = [s for s in splash_effects if s["lifetime"] > 0]

def draw_combo_text():
    for combo in combo_display:
        alpha = max(0, 255 - (pygame.time.get_ticks() - combo["time"]))
        if alpha > 0:
            surface = font.render(f"Combo x{combo['count']}! +{combo['bonus']}", True, (255, 215, 0))
            surface.set_alpha(alpha)
            screen.blit(surface, combo["pos"])
    combo_display[:] = [c for c in combo_display if pygame.time.get_ticks() - c["time"] < 1000]

def reset_game():
    global fruits, score, lives, splash_effects, trail, game_over, combo_hits, split_fruits
    fruits = []
    score = 0
    lives = 3
    splash_effects = []
    trail.clear()
    game_over = False
    combo_hits = []
    split_fruits = []

# Initial setup
fruits = []
SPAWN_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(SPAWN_EVENT, 1000)
running = True

while running:
    screen.blit(bg, (0, 0))
    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over and event.type == SPAWN_EVENT:
            burst = random.random() < 0.2
            count = random.randint(4, 7) if burst else 1
            for _ in range(count):
                is_bomb = random.random() < 0.1
                fruits.append(Fruit(is_bomb))
        elif game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            reset_game()

    if not game_over:
        trail.appendleft(mouse_pos)
        sliced_this_frame = []

        for fruit in fruits:
            if fruit.alive and fruit.is_hit_by_trail(trail):
                fruit.alive = False
                if fruit.is_bomb:
                    game_over = True
                    if score > best_score:
                        best_score = score
                        with open(SAVE_PATH, "w") as f:
                            json.dump({"best_score": best_score}, f)
                else:
                    score += 1
                    sliced_this_frame.append(pygame.time.get_ticks())
                    splash_effects.append({"pos": (int(fruit.x + 32), int(fruit.y + 32)), "radius": 10, "lifetime": 15, "color": (255, 50, 50)})
                    split_fruits.append(SplitFruit(fruit.original, (fruit.x + 16, fruit.y + 16), -1))
                    split_fruits.append(SplitFruit(fruit.original, (fruit.x + 32, fruit.y + 16), 1))

        combo_hits = [t for t in combo_hits if pygame.time.get_ticks() - t < 1000]
        combo_hits.extend(sliced_this_frame)
        if len(combo_hits) >= 3:
            bonus = 10
            score += bonus
            combo_display.append({
                "time": pygame.time.get_ticks(),
                "count": len(combo_hits),
                "bonus": bonus,
                "pos": mouse_pos
            })
            combo_hits = []

        for fruit in fruits:
            fruit.move()
            fruit.draw()

        for i in range(1, len(trail)):
            start, end = trail[i - 1], trail[i]
            alpha = int(255 * (1 - i / len(trail)))
            trail_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(trail_surf, (255, 255, 255, alpha), start, end, 8)
            screen.blit(trail_surf, (0, 0))

        fruits = [f for f in fruits if f.alive and not f.is_off_screen()]
        for fruit in fruits:
            if fruit.alive and fruit.is_off_screen() and not fruit.is_bomb:
                fruit.alive = False
                lives -= 1
                if lives <= 0:
                    game_over = True
                    if score > best_score:
                        best_score = score
                        with open(SAVE_PATH, "w") as f:
                            json.dump({"best_score": best_score}, f)

        split_fruits = [f for f in split_fruits if f.update()]
        for f in split_fruits:
            f.draw()

        draw_splashes()
        draw_combo_text()

        screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (10, 10))
        screen.blit(font.render(f"Best: {best_score}", True, (255, 255, 0)), (10, 40))
        screen.blit(font.render(f"Lives: {lives}", True, (255, 0, 0)), (10, 70))
    else:
        screen.blit(large_font.render("Game Over", True, (255, 0, 0)), (WIDTH // 2 - 120, HEIGHT // 2 - 60))
        screen.blit(font.render(f"Score: {score}", True, (255, 255, 255)), (WIDTH // 2 - 50, HEIGHT // 2))
        screen.blit(font.render(f"Best Score: {best_score}", True, (255, 255, 0)), (WIDTH // 2 - 80, HEIGHT // 2 + 40))
        screen.blit(font.render("Press R to Restart", True, (200, 200, 200)), (WIDTH // 2 - 100, HEIGHT // 2 + 80))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
