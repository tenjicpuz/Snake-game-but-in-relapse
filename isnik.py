import pygame
import random
import time
import sys

ROWS = 25
COLUMNS = 25
TILE_SIZE = 25
GAME_WIDTH = TILE_SIZE * COLUMNS
GAME_HEIGHT = TILE_SIZE * ROWS

pygame.init()
window = pygame.display.set_mode((GAME_WIDTH, GAME_HEIGHT))
pygame.display.set_caption("Snakee Game ni Hernan")
clock = pygame.time.Clock()

def get_random(limit):
    return random.randint(0, limit-1) * TILE_SIZE

food = pygame.Rect(get_random(COLUMNS), get_random(ROWS), TILE_SIZE, TILE_SIZE)
snake = []
snake.append( pygame.Rect(get_random(COLUMNS), get_random(ROWS), TILE_SIZE, TILE_SIZE))
snake_velocity = [0, 0]

game_over = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                snake_velocity = (0, -TILE_SIZE)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                snake_velocity = (0, TILE_SIZE)
            elif event.key in (pygame.K_LEFT, pygame.K_a):
                snake_velocity = (-TILE_SIZE, 0)
            elif event.key in (pygame.K_RIGHT, pygame.K_d):
                snake_velocity = (TILE_SIZE, 0)
   
    if not game_over:
        for i in range(len(snake)-1, 0, -1):
            snake[i] = snake[i-1].copy()
        snake[0].move_ip(snake_velocity)

        if snake[0].colliderect(food):
            snake.append(food.copy())
            food = pygame.Rect(get_random(COLUMNS), get_random(ROWS), TILE_SIZE, TILE_SIZE)

        if not window.get_rect().contains(snake[0]):
            game_over = True

    window.fill("black")

    if game_over:
        window.fill("black")
        window2 = pygame.display.set_mode((TILE_SIZE * ROWS, TILE_SIZE * ROWS))
        pygame.display.set_caption("Kanibalismo II")
        clock = pygame.time.Clock()
        font_small = pygame.font.SysFont("Verdana", 35)

        pygame.mixer.init()
        pygame.mixer.music.load("kanibalismo.mp3")

        lyrics = [
            ("GAME OVER", 0),
            ("Kanibalismo, 'di ka matiis", 1.5),
            ("Kapag inalis mo, ika'y mami-miss", 7),
            ("Di nagmamalinis", 12), 
            ("Oh, ika'y mami-miss", 16)
        ]

        def show_line(line):
            window2.fill("black")
            text_surface = font_small.render(line, True, (255, 255, 255))
            x = window2.get_width() // 2 - text_surface.get_width() // 2
            y = window2.get_height() // 2 - text_surface.get_height() // 2
            window2.blit(text_surface, (x, y))
            pygame.display.update()


        pygame.mixer.music.play()
        start_time = time.time()
        current_index = 0

        running = True
        while running:
            now = time.time() - start_time
            if current_index < len(lyrics) and now >= lyrics[current_index][1]:
                show_line(lyrics[current_index][0])
                current_index += 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            clock.tick(30)

        pygame.quit()
        sys.exit()
    else:
        pygame.draw.rect(window, "yellow", food)
        for snake_part in snake:
            pygame.draw.rect(window, "skyblue", snake_part)

    pygame.display.update()
    clock.tick(10)
