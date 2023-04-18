import sys
import os
import random
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
TILE_SIZE = 40

# Player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False

# load images
bullet_img = pygame.image.load('../images/icons/bullet.png').convert_alpha()
grenade_img = pygame.image.load('../images/icons/grenade.png').convert_alpha()
health_box_img = pygame.image.load('../images/icons/health_box.png').convert_alpha()
ammo_box_img = pygame.image.load('../images/icons/ammo_box.png').convert_alpha()
grenade_box_img = pygame.image.load('../images/icons/grenade_box.png').convert_alpha()
item_boxes = {
    'Health': health_box_img,
    'Ammo': ammo_box_img,
    'Grenade': grenade_box_img
}

# colors
BG = (139, 131, 120)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

font = pygame.font.SysFont('Futura', 30)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    pygame.draw.line(screen, RED, (0, 300), (settings.SCREEN_WIDTH, 300))


class Soldier(pygame.sprite.Sprite):
    def __init__(self, char_type, x, y, scale, speed, ammo, grenades=0, health=100):
        pygame.sprite.Sprite.__init__(self)
        self.alive = True
        self.char_type = char_type
        self.speed = speed
        self.health = health
        self.max_health = self.health
        self.ammo = ammo
        self.start_ammo = ammo
        self.grenades = grenades
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

        # ai specific variables
        self.move_counter = 0
        self.vision = pygame.Rect(0, 0, 150, 20)
        self.idling = False
        self.idling_counter = 0

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
            bullet = Bullet(self.rect.centerx + (0.75 * self.rect.size[0] * self.direction), self.rect.centery,
                            self.direction)
            bullet_group.add(bullet)
            self.ammo -= 1  # reduces ammo

    def ai(self):
        if self.alive and player.alive:
            if not self.idling and random.randint(1, 200) == 1:  # if random # = 1 then ai enemy will idle
                self.update_action(0)  # Idle animation
                self.idling = True
                self.idling_counter = 50
            if self.vision.colliderect(player.rect):  # if the enemy can 'see' the player
                # stop running and face player
                self.update_action(0)
                self.shoot()
            else:
                if not self.idling:
                    if self.direction == 1:
                        ai_moving_right = True
                    else:
                        ai_moving_right = False
                    ai_moving_left = not ai_moving_right
                    self.move(ai_moving_left, ai_moving_right)
                    self.update_action(1)  # Run animation

                    self.vision.center = (self.rect.centerx + 75 * self.direction, self.rect.centery)
                    self.move_counter += 1
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False
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


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        # check for collision with Player
        if pygame.sprite.collide_rect(self, player):
            # check box type
            if self.item_type == 'Health':
                player.health += 25
                if player.health > player.max_health:
                    player.health = player.max_health
            elif self.item_type == 'Ammo':
                player.ammo += 15
            elif self.item_type == 'Grenade':
                player.grenades += 3
            # delete box
            self.kill()


class HealthBar():
    def __init__(self, x, y, health, max_health):
        self.x = x
        self.y = y
        self.health = health
        self.max_health = max_health

    def draw(self, health):
        # update w/ new health
        self.health = health
        ratio = self.health / self.max_health
        pygame.draw.rect(screen, BLACK, (self.x - 2, self.y - 2, 154, 24))
        pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
        pygame.draw.rect(screen, GREEN, (self.x, self.y, 150 * ratio, 20))


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
        for bad_guy in enemy_group:
            if pygame.sprite.spritecollide(bad_guy, bullet_group, False):
                if bad_guy.alive:
                    bad_guy.health -= 25
                    self.kill()


class Grenade(pygame.sprite.Sprite):
    def __init__(self, x, y, direction):
        pygame.sprite.Sprite.__init__(self)
        self.timer = 100
        self.vel_y = -11
        self.speed = 7
        self.image = grenade_img
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        # check collision w/ floor
        if self.rect.bottom + dy > 300:
            dy = 300 - self.rect.bottom
            self.speed = 0

        # check for collision w/ wall (bounces off of walls)
        if self.rect.left + dx < 0 or self.rect.right + dx > settings.SCREEN_WIDTH:
            self.direction *= -1
            dx = self.direction * self.speed

        # update position
        self.rect.x += dx
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 2)
            explosion_group.add(explosion)
            # damage nearby Soldiers
            if abs(self.rect.centerx - player.rect.centerx) < TILE_SIZE * 2 and \
                    abs(self.rect.centery - player.rect.centery) < TILE_SIZE * 2:
                player.health -= 50
            for bad_guy in enemy_group:
                if abs(self.rect.centerx - bad_guy.rect.centerx) < TILE_SIZE * 2 and \
                        abs(self.rect.centery - bad_guy.rect.centery) < TILE_SIZE * 2:
                    bad_guy.health -= 50


class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y, scale):
        pygame.sprite.Sprite.__init__(self)
        self.images = []
        for num in range(1, 6):
            img = pygame.image.load(f'../images/Explosion/exp{num}.png').convert_alpha()
            img = pygame.transform.scale(img, (int(img.get_width() * scale), int(img.get_height() * scale)))
            self.images.append(img)
        self.frame_index = 0
        self.image = self.images[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.counter = 0

    def update(self):
        EXPLOSION_SPEED = 4
        # update animation
        self.counter += 1
        if self.counter >= EXPLOSION_SPEED:
            self.counter = 0
            self.frame_index += 1
            # if animation complete delete explosion
            if self.frame_index >= len(self.images):
                self.kill()
            else:
                self.image = self.images[self.frame_index]


# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()

# temp create item boxes
item_box = ItemBox('Health', 100, 260)
item_box_group.add(item_box)
item_box = ItemBox('Ammo', 400, 260)
item_box_group.add(item_box)
item_box = ItemBox('Grenade', 500, 260)
item_box_group.add(item_box)

player = Soldier('player', 200, 200, 1.5, 5, grenades=5, ammo=20)
health_bar = HealthBar(10, 10, player.health, player.health)
enemy = Soldier('enemy', 300, 250, 1.5, speed=2, ammo=20)
enemy2 = Soldier('enemy', 700, 250, 1.5, speed=2, ammo=20)
enemy_group.add(enemy)
enemy_group.add(enemy2)

run = True


def handle_event():
    global run, moving_left, moving_right, shoot, grenade, grenade_thrown
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
            if event.key == pygame.K_q:
                grenade = True
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
            if event.key == pygame.K_q:
                grenade = False
                grenade_thrown = False


while run:
    clock.tick(FPS)

    draw_bg()

    health_bar.draw(player.health)

    # show player stats
    draw_text('AMMO: ', font, WHITE, 10, 35)
    for x in range(player.ammo):
        screen.blit(bullet_img, (135 + (x * 10), 50))
    draw_text('GRENADES: ', font, WHITE, 10, 75)
    for x in range(player.grenades):
        screen.blit(grenade_img, (200 + (x * 15), 90))

    player.draw()
    player.update()

    for enemy in enemy_group:
        enemy.ai()
        enemy.draw()
        enemy.update()

    # update and draw groups
    bullet_group.update()
    bullet_group.draw(screen)
    explosion_group.update()
    explosion_group.draw(screen)
    item_box_group.update()
    item_box_group.draw(screen)
    grenade_group.update()
    grenade_group.draw(screen)

    if player.alive:
        # shooting
        if shoot:
            player.shoot()
        elif grenade and not grenade_thrown and player.grenades > 0:
            grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),
                              player.rect.top, player.direction)
            grenade_group.add(grenade)
            player.grenades -= 1
            grenade_thrown = True
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
