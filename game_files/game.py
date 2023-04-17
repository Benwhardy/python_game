import sys

import pygame

from game_files import settings

pygame.init()

screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
pygame.display.set_caption('Ben\'s Game')

# set framerate
clock = pygame.time.Clock()
FPS = 60

# Player action variables
moving_left = False
moving_right = False

BG = (139, 131, 120)


def draw_bg():
    screen.fill(BG)


class Soldier(pygame.sprite.Sprite):
    def __init__(self,char_type,  x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.flip = False
        img = pygame.image.load(f'../images/{self.char_type}/Idle/0.png')
        self.image = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
        self.rect = img.get_rect()
        self.rect.center = (x, y)

    def move(self, moving_left, moving_right):
        # dx and dy represent delta x,y (the amount of change in the coordinates)
        dx = 0
        dy = 0

        if moving_left:
            dx = -self.speed
            self.flip = True
            self.direction = -1
        if moving_right:
            dx = self.speed
            self.flip = False
            self.direction = 1

        # update player rectangle
        self.rect.x += dx
        self.rect.y += dy

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


player = Soldier('player', 200, 200, 1.5, 5)
enemy = Soldier('enemy', 300, 300, 1.5, 5)

run = True


def handle_event():
    global run, moving_left, moving_right
    for event in pygame.event.get():  # Quit game
        if event.type == pygame.QUIT:
            run = False
        # KEYBOARD INPUT
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and event.mod == pygame.KMOD_LCTRL:
                pass  # Debugging functionality
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_ESCAPE:
                run = False
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False


while run:

    clock.tick(FPS)

    draw_bg()

    player.draw()
    enemy.draw()

    player.move(moving_left, moving_right)

    handle_event()

    pygame.display.update()

pygame.quit()
