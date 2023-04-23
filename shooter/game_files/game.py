import os
import random
import csv
import pygame

import button
from settings import *

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Ben\'s Game')

# Player action variables
moving_left = False
moving_right = False
shoot = False
grenade = False
grenade_thrown = False  # when grenade_thrown is false player can throw grenade. Disallows holding q for multiple.

# load images
mountains_img = pygame.image.load('../images/background/mountain.png').convert_alpha()
sky_img = pygame.image.load('../images/background/sky_cloud.png')
tree_img = pygame.image.load('../images/background/pine1.png')
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

# Button images
start_img = pygame.image.load('../images/buttons/start_btn.png').convert_alpha()
exit_img = pygame.image.load('../images/buttons/exit_btn.png').convert_alpha()
restart_img = pygame.image.load('../images/buttons/restart_btn.png').convert_alpha()

# tiles
img_list = []
for x in range(TILE_TYPES):
    img = pygame.image.load(f'../images/tile/{x}.png')
    img = pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    img_list.append(img)

font = pygame.font.SysFont('Futura', 30)


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


def draw_bg():
    screen.fill(BG)
    width = sky_img.get_width()
    for x in range(5):  # loops the background images (uses parallax scrolling)
        screen.blit(sky_img, ((x * width) - bg_scroll * 0.5, 0))
        screen.blit(mountains_img,
                    ((x * width) - bg_scroll * 0.6, SCREEN_HEIGHT - mountains_img.get_height() - 100))
        screen.blit(tree_img, ((x * width) - bg_scroll * 0.8, SCREEN_HEIGHT - mountains_img.get_height()))


# reset level
def reset_level():
    enemy_group.empty()
    bullet_group.empty()
    grenade_group.empty()
    explosion_group.empty()
    item_box_group.empty()
    decoration_group.empty()
    water_group.empty()
    exit_group.empty()

    # empty tile list
    data = []
    for row in range(ROWS):
        r = [-1] * COLS
        data.append(r)
    return data


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
        self.width = self.image.get_width()
        self.height = self.image.get_height()

    def update(self):
        self.update_animation()
        self.check_alive()
        # update cooldown
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1

    def move(self, moving_left, moving_right):
        # dx and dy represent delta x,y (the amount of change in the coordinates)
        screen_scroll = 0
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
            self.vel_y = -12
            self.jump = False
            self.in_air = True

        self.vel_y += GRAVITY
        if self.vel_y > 10:
            self.vel_y = 10
        dy += self.vel_y

        # check for collision
        for tile in world.obstacle_list:
            # check x
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                dx = 0
                if self.char_type == 'enemy':  # turn ai character around if they hit a wall
                    self.direction *= -1
                    self.move_counter = 0

            # check y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                # if below ground (jumping)
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # if above ground (falling)
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    self.in_air = False
                    dy = tile[1].top - self.rect.bottom

        # check for collision w/ water
        if pygame.sprite.spritecollide(self, water_group, False):
            self.health = 0

        # check for collision w/ exit
        level_complete = False
        if pygame.sprite.spritecollide(self, exit_group, False):
            level_complete = True

        # check if player falls off map
        if self.rect.bottom > SCREEN_HEIGHT:
            self.health = 0

        # check if player going off of the screen
        if self.char_type == 'player':
            if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
                dx = 0
        # update player rectangle
        self.rect.x += dx
        self.rect.y += dy

        # update scroll from player position
        if self.char_type == 'player':
            if (self.rect.right > SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (
                    world.level_length * TILE_SIZE) - SCREEN_WIDTH) \
                    or (self.rect.left < SCROLL_THRESH and bg_scroll > abs(dx)):
                self.rect.x -= dx
                screen_scroll = -dx

        return screen_scroll, level_complete

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
                self.direction = player.direction * -1
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
                    # pygame.draw.rect(screen, RED, self.vision)
                    if self.move_counter > TILE_SIZE:
                        self.direction *= -1
                        self.move_counter *= -1
                else:
                    self.idling_counter -= 1
                    if self.idling_counter <= 0:
                        self.idling = False

        self.rect.x += screen_scroll

    def update_animation(self):
        ANIMATION_COOLDOWN = 100  # Amount of time to wait before showing next frame
        self.image = self.animation_list[self.action][self.frame_index]  # updates image to frame in current list
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            # checks if enough time has passed since the last update
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1
        if self.frame_index >= len(self.animation_list[self.action]):  # loops the animation
            if self.action == 3:  # if the player is dead don't loop Death animation
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


class World:
    def __init__(self):
        self.level_length = None
        self.obstacle_list = []

    def process_data(self, data):
        self.level_length = len(data[0])  # how wide the level is
        # iterate through each value in level data
        # to link a png from images
        for y, row in enumerate(data):
            for x, tile in enumerate(row):
                if tile >= 0:
                    img = img_list[tile]
                    img_rect = img.get_rect()
                    img_rect.x = x * TILE_SIZE
                    img_rect.y = y * TILE_SIZE
                    tile_data = (img, img_rect)
                    if 0 <= tile <= 8:  # obstacle tiles
                        self.obstacle_list.append(tile_data)
                    elif 9 <= tile <= 10:
                        water = Water(img, x * TILE_SIZE, y * TILE_SIZE)
                        water_group.add(water)
                    elif 11 <= tile <= 14:
                        decoration = Decoration(img, x * TILE_SIZE, y * TILE_SIZE)
                        decoration_group.add(decoration)
                    elif tile == 15:  # create player
                        player = Soldier('player', x * TILE_SIZE, y * TILE_SIZE, 1.65, 6, grenades=5, ammo=20)
                        health_bar = HealthBar(10, 10, player.health, player.health)
                    elif tile == 16:  # create enemy
                        enemy = Soldier('enemy', x * TILE_SIZE, y * TILE_SIZE, 1.65, speed=2, ammo=20)
                        enemy_group.add(enemy)
                    elif tile == 17:  # ammo box
                        item_box = ItemBox('Ammo', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 18:  # grenade box
                        item_box = ItemBox('Grenade', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 19:  # Health box
                        item_box = ItemBox('Health', x * TILE_SIZE, y * TILE_SIZE)
                        item_box_group.add(item_box)
                    elif tile == 20:  # EXIT
                        exit = Exit(img, x * TILE_SIZE, y * TILE_SIZE)
                        exit_group.add(exit)
        return player, health_bar

    def draw(self):
        for tile in self.obstacle_list:
            tile[1][0] += screen_scroll
            screen.blit(tile[0], tile[1])  # image, img_rect


class Decoration(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Water(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class Exit(pygame.sprite.Sprite):
    def __init__(self, img, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.image = img
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):
        self.rect.x += screen_scroll


class ItemBox(pygame.sprite.Sprite):
    def __init__(self, item_type, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.item_type = item_type
        self.image = item_boxes[self.item_type]
        self.rect = self.image.get_rect()
        self.rect.midtop = (x + TILE_SIZE // 2, y + (TILE_SIZE - self.image.get_height()))

    def update(self):

        self.rect.x += screen_scroll
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


class HealthBar:
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
        self.rect.x += (self.direction * self.speed) + screen_scroll
        # check if bullet leaves screen
        if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

        # check collision

        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect):
                self.kill()
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
        self.width = self.image.get_width()
        self.height = self.image.get_height()
        self.direction = direction

    def update(self):
        self.vel_y += GRAVITY
        dx = self.direction * self.speed
        dy = self.vel_y

        # check collision w/ floor
        for tile in world.obstacle_list:
            if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
                self.direction *= -1
                dx = self.direction * self.speed
                # check y direction
            if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
                self.speed = 0
                # if below ground (thrown up)
                if self.vel_y < 0:
                    self.vel_y = 0
                    dy = tile[1].bottom - self.rect.top
                # if above ground (falling)
                elif self.vel_y >= 0:
                    self.vel_y = 0
                    dy = tile[1].top - self.rect.bottom

        # check for collision w/ wall (bounces off of walls)
        if self.rect.left + dx < 0 or self.rect.right + dx > SCREEN_WIDTH:
            self.direction *= -1
            dx = self.direction * self.speed

        # update position
        self.rect.x += dx + screen_scroll
        self.rect.y += dy

        # countdown timer
        self.timer -= 1
        if self.timer <= 0:
            self.kill()
            explosion = Explosion(self.rect.x, self.rect.y, 2)
            explosion_group.add(explosion)
            # damage nearby Soldiers (abs accounts for the left and right of the grenade)
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
        # scroll
        self.rect.x += screen_scroll
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


class ScreenFade:
    def __init__(self, direction, color, speed):
        self.direction = direction
        self.color = color
        self.speed = speed
        self.fade_counter = 0

    def fade(self):
        fade_complete = False
        self.fade_counter += self.speed
        if self.direction == 1:  # whole screen fade
            pygame.draw.rect(screen, self.color, (0 - self.fade_counter, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
            pygame.draw.rect(screen, self.color,
                             (SCREEN_WIDTH // 2 + self.fade_counter, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.direction == 2:  # vertical fade down
            pygame.draw.rect(screen, self.color, (0, 0, SCREEN_WIDTH, 0 + self.fade_counter))
        if self.fade_counter >= SCREEN_WIDTH:
            fade_complete = True
        return fade_complete


# create fades
intro_fade = ScreenFade(1, BLACK, 4)
death_fade = ScreenFade(2, RED, 4)

# create the buttons
start_button = button.Button(SCREEN_WIDTH // 2 - 130, SCREEN_HEIGHT // 2 - 150, start_img, 1)
exit_button = button.Button(SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT // 2 + 50, exit_img, 1)
restart_button = button.Button(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 - 50, restart_img, 2)

# create sprite groups
enemy_group = pygame.sprite.Group()
bullet_group = pygame.sprite.Group()
grenade_group = pygame.sprite.Group()
explosion_group = pygame.sprite.Group()
item_box_group = pygame.sprite.Group()
decoration_group = pygame.sprite.Group()
water_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

# create empty tile lists
world_data = []
for row in range(ROWS):  # adds a -1 to each spot in each row
    r = [-1] * COLS
    world_data.append(r)
# load level data to create world
with open('../../level1_data.csv', newline='') as csvfile:
    # loads a number into the lists within world_data
    # that corresponds to a tile from images
    reader = csv.reader(csvfile, delimiter=',')
    for x, row in enumerate(reader):
        for y, tile in enumerate(row):
            world_data[x][y] = int(tile)

world = World()
player, health_bar = world.process_data(world_data)

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


def start_screen():
    global start_game, start_intro, run
    screen.fill(BG)
    # add button
    if start_button.draw(screen):  # if clicked
        start_game = True
        start_intro = True
    if exit_button.draw(screen):
        run = False


def update_and_draw_groups():
    player.draw()
    player.update()
    for enemy in enemy_group:
        enemy.ai()
        enemy.update()
        enemy.draw()
    # update and draw groups
    bullet_group.update()
    bullet_group.draw(screen)
    explosion_group.update()
    explosion_group.draw(screen)
    item_box_group.update()
    item_box_group.draw(screen)
    grenade_group.update()
    grenade_group.draw(screen)
    decoration_group.update()
    decoration_group.draw(screen)
    water_group.update()
    water_group.draw(screen)
    exit_group.update()
    exit_group.draw(screen)


def player_stats():
    global x
    # show player stats
    health_bar.draw(player.health)
    draw_text('AMMO: ', font, WHITE, 10, 35)
    for x in range(player.ammo):
        screen.blit(bullet_img, (135 + (x * 10), 50))
    draw_text('GRENADES: ', font, WHITE, 10, 75)
    for x in range(player.grenades):
        screen.blit(grenade_img, (200 + (x * 15), 90))


level = 1
start_game = False
start_intro = False
clock = pygame.time.Clock()

while run:
    clock.tick(FPS)

    if not start_game:  # main menu
        start_screen()
    else:
        draw_bg()
        world.draw()
        player_stats()
        update_and_draw_groups()

        if start_intro:
            if intro_fade.fade():
                start_intro = False
                intro_fade.fade_counter = 0  # reset fade_counter so that it can be run again

        if player.alive:
            # shooting
            if shoot:
                player.shoot()
            elif grenade and not grenade_thrown and player.grenades > 0:
                # creates the grenade just above/in front of player head
                grenade = Grenade(player.rect.centerx + (0.5 * player.rect.size[0] * player.direction),
                                  player.rect.top, player.direction)
                grenade_group.add(grenade)
                player.grenades -= 1
                grenade_thrown = True
            if player.in_air:
                player.update_action(2)  # 2 = jump
            elif moving_left or moving_right:
                player.update_action(1)  # 1 = Run animation
            else:
                player.update_action(0)  # 0 = idle animation
            screen_scroll, level_complete = player.move(moving_left, moving_right)
            bg_scroll -= screen_scroll
            # check if level is completed
            if level_complete:
                start_intro = True
                level += 1
                bg_scroll = 0
                world_data = reset_level()
                if level <= MAX_LEVELS:
                    with open(f'../level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)
        else:  # player dead
            screen_scroll = 0
            if death_fade.fade():
                if restart_button.draw(screen):
                    death_fade.fade_counter = 0  # reset counter so it can run again
                    start_intro = True
                    bg_scroll = 0
                    world_data = reset_level()
                    with open(f'../level{level}_data.csv', newline='') as csvfile:
                        reader = csv.reader(csvfile, delimiter=',')
                        for x, row in enumerate(reader):
                            for y, tile in enumerate(row):
                                world_data[x][y] = int(tile)
                    world = World()
                    player, health_bar = world.process_data(world_data)

    handle_event()
    pygame.display.update()

pygame.quit()
