import sys
import os

import pygame

from game_files import settings

pygame.init()

screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
pygame.display.set_caption('Ben\'s Game')

# set framerate
clock = pygame.time.Clock()
FPS = 60

# game variables
GRAVITY = 0.75

# Player action variables
moving_left = False
moving_right = False

BG = (139, 131, 120)
RED = (255, 0, 0)


def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 300), (settings.SCREEN_WIDTH, 300))


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.direction = 1
        self.vel_y = 0  # vertical velocity
        self.jump = False
        self.in_air = True  # assume player is in the air until it lands on something
        self.flip = False
        self.animation_list = []
        self.frame_index = 0  # Current index of the frame within the animation list
        self.action = 0  # Current index of the animation list being used
        self.update_time = pygame.time.get_ticks()

        # load images for players
        animation_types = ['Idle', 'Run', 'Jump']
        for animation in animation_types:
            # reset temp list of images
            temp_list = []
            # count the number of files in that animations folder
            num_of_frames = len(os.listdir(f'../images/{self.char_type}/{animation}'))
            for i in range(num_of_frames):  # adds list of idle animation frames to index 0 in animation_list
                img = pygame.image.load(f'../images/{self.char_type}/{animation}/{i}.png')
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
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

        # JUMP
        if self.jump and not self.in_air:
            self.vel_y = -11
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # check collision w/ floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.in_air = False

        # update player rectangle
        self.rect.x += dx
        self.rect.y += dy

    def update_animation(self):
        ANIMATION_COOLDOWN = 100
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def update_action(self, new_action):
        # If new action is different
        if new_action != self.action:
            self.action = new_action
            # update animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

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

        # PRESS
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and event.mod == pygame.KMOD_LCTRL:
                pass  # Debugging functionality
            if event.key == pygame.K_a:
                moving_left = True
            if event.key == pygame.K_d:
                moving_right = True
            if event.key == pygame.K_w and player.alive:
                player.jump = True
            if event.key == pygame.K_ESCAPE:
                run = False
        # RELEASE
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_a:
                moving_left = False
            if event.key == pygame.K_d:
                moving_right = False


while run:
    clock.tick(FPS)

    draw_bg()

    player.draw()
    player.update_animation()
    enemy.draw()

    if player.alive:
        if player.in_air:
            player.update_action(2)  # 2 = jump
        elif moving_left or moving_right:
            player.update_action(1)  # 1 = run animation
        else:
            player.update_action(0)  # 0 = idle animation
        player.move(moving_left, moving_right)

    handle_event()

    pygame.display.update()

pygame.quit()
