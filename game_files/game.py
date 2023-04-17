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
shoot = False

# load images

# bullet
bullet_img = pygame.image.load('../images/icons/bullet.png').convert_alpha()

# colors
BG = (139, 131, 120)
RED = (255, 0, 0)


def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 300), (settings.SCREEN_WIDTH, 300))


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, health=100):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.health = health
        self.max_health = self.health
        self.ammo = ammo
        self.start_ammo = ammo
        self.shoot_cooldown = 0
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
        animation_types = ['Idle', 'Run', 'Jump', 'Death']
        for animation in animation_types:
            # reset temp list of images
            temp_list = []
            # count the number of files in that animations folder
            num_of_frames = len(os.listdir(f'../images/{self.char_type}/{animation}'))
            for i in range(num_of_frames):  # adds list of idle animation frames to index 0 in animation_list
                img = pygame.image.load(f'../images/{self.char_type}/{animation}/{i}.png').convert_alpha()
                img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
                temp_list.append(img)
            self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

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

    def shoot(self):
        # creates a bullet at the end of the Soldiers barrel
        if self.shoot_cooldown == 0 and self.ammo > 0:
            self.shoot_cooldown = 20
            bullet = Bullet(self.rect.centerx + (0.6 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1  # reduces ammo

    def update_animation(self):
        ANIMATION_COOLDOWN = 100  # Amount of time to wait before showing next frame
        self.image = self.animation_list[self.action][self.frame_index]  # updates image to frame in current list
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            # checks if enough time has passed since the last update
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):  # loops the animation
            if self.action == 3:  # if the player is dead don't loop death animation
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0

    def update_action(self, new_action):
        # If new action is different
        if new_action != self.action:
            self.action = new_action
            # update animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def check_alive(self):
        if self.health <= 0:
            self.health = 0
            self.speed = 0
            self.alive = False
            self.update_action(3)

    def draw(self):
        screen.blit(pygame.transform.flip(self.image, self.flip, False), self.rect)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.speed = 10
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        # moves bullet
        self.rect.x += (self.direction * self.speed)
        # check if bullet leaves screen
        if self.rect.right < 0 or self.rect.left > settings.SCREEN_WIDTH:
            self.kill()

        # check collision
        if pygame.sprite.spritecollide(player, bullet_group, False):
            if player.alive:
                player.health -= 5
                self.kill()
        if pygame.sprite.spritecollide(enemy, bullet_group, False):
            if enemy.alive:
                enemy.health -= 25
                self.kill()




# create sprite groups
bullet_group = pygame.sprite.Group()

player = Soldier('player', 200, 200, 1.5, 5, 20)
enemy = Soldier('enemy', 300, 300, 1.5, 5, 20)

run = True


def handle_event():
    global run, moving_left, moving_right, shoot
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
            if event.key == pygame.K_SPACE:
                shoot = True
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
            if event.key == pygame.K_SPACE:
                shoot = False


while run:
    clock.tick(FPS)

    draw_bg()

    player.draw()
    player.update()

    enemy.draw()
    enemy.update()

    # update and draw groups
    bullet_group.update()
    bullet_group.draw(screen)

    if player.alive:
        # shooting
        if shoot:
            player.shoot()
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
