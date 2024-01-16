import pygame
import pytmx
import random
import json

WINDOW_SIZE = WIDTH, HEIGHT = 1080, 700
MAPS_DIR = "data/maps"
PLAYER_DIR = "data/images/player"
WEAPON_DIR = "data/weapon"

TILE_SIZE = 32
FREE_TILES = [1, 2, 3, 4, 5, 24, 14, 25, 15, 44, 34, 45, 35,
              71, 72, 73, 81, 82, 83, 91, 92, 93, 54, 64]
RR_AM = 15  # random rooms amount

FPS = 30
ENEMY_EVENT_TYPE = 30


class Room:
    def __init__(self, roomID, free_tiles):
        self.map = pytmx.load_pygame(f"{MAPS_DIR}/{roomID}")
        self.height = self.map.height
        self.width = self.map.width
        self.roomID = roomID
        self.tiles_map = [[self.map.tiledgidmap[self.map.get_tile_gid(j, i, 0)] for j in range(self.width)]
                          for i in range(self.height)]
        self.free_tiles = free_tiles
        self.enemies = []
        if roomID in ["start_room.tmx"]:
            self.enemies_am = 0
            self.clear = True
        else:
            self.enemies_am = len(self.enemies)
            self.clear = False
            self.spawn_enemies()

    def render(self, screen):
        for y in range(self.height):
            for x in range(self.width):
                image = self.map.get_tile_image(x, y, 0)
                screen.blit(image, (x * TILE_SIZE + 20,
                                    y * TILE_SIZE + 20))
        for enemy in self.enemies:
            enemy.render(screen)

    def get_tile(self, position):
        return self.tiles_map[position[1]][position[0]]

    def is_free(self, position):
        return self.get_tile(position) in self.free_tiles

    def crow_path(self, start, target):
        INF = 100
        x, y = start
        distance = [[INF] * self.width for _ in range(self.height)]
        distance[y][x] = 0
        prev = [[None] * self.width for _ in range(self.height)]
        queue = [(x, y)]
        while queue:
            x, y = queue.pop(0)
            for dx, dy in (1, 0), (0, 1), (-1, 0), (0, -1):
                next_x, next_y = x + dx, y + dy
                if 0 <= next_x < self.width and 0 < next_y < self.height and \
                        self.is_free((next_x, next_y)) and distance[next_y][next_x] == INF:
                    distance[next_y][next_x] = distance[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        x, y = target
        if distance[y][x] == INF or start == target:
            return start
        while prev[y][x] != start:
            x, y = prev[y][x]
        return x, y

    def roll_path(self, start, direction):
        curr_direction = direction.copy()
        new_direction = curr_direction.copy()
        next_x = start[0] + curr_direction[0]
        next_y = start[1] + curr_direction[1]
        changed_dir = False
        if not self.is_free((next_x, start[1])):
            new_direction[0] = -curr_direction[0]
            next_x = start[0] + new_direction[0]
        if not self.is_free((start[0], next_y)):
            new_direction[1] = -curr_direction[1]
            next_y = start[1] + new_direction[1]
        if not self.is_free((next_x, next_y)):
            new_direction = [-direction[0], -direction[1]]
            next_x = start[0] + new_direction[0]
            next_y = start[1] + new_direction[1]
        if new_direction != direction:
            if new_direction != [-direction[0], -direction[1]]:
                changed_dir = True
        return next_x, next_y, new_direction, changed_dir

    def boss_roll_path(self, start, direction):
        new_direction = direction
        next_x = start[0] + new_direction
        if not self.is_free((next_x, start[1])):
            new_direction = -new_direction
            next_x = start[0] + new_direction
        return next_x, start[1], new_direction

    def spawn_enemies(self):
        if self.clear or "treasure" in self.roomID:
            return
        self.enemies = []
        with open("data/maps/enemies_data.json") as f:
            enemies_data = json.load(f)
            for data in enemies_data[self.roomID[5:-4]]:
                if data[0] == "crow":
                    self.enemies.append(Crow(data[1]))
                if data[0] == "hay_roll":
                    self.enemies.append(HayRoll(data[1]))
                if data[0] == "scarecrow":
                    self.enemies.append(Boss(data[1]))
                if data[0] == "boss_hay_roll":
                    self.enemies.append(BossHayRoll(data[1]))
                if data[0] == "boss_hayfork":
                    self.enemies.append(BossHayfork(data[1]))
            self.enemies_am = len(self.enemies)


class LevelMap:
    def __init__(self, free_tiles):
        self.free_tiles = free_tiles
        self.id_map = [[f"room_{random.randint(1, RR_AM)}", f"room_{random.randint(1, RR_AM)}",
                        f"room_{random.randint(1, RR_AM)}", f"treasure_room_1"],
                       ["start_room", f"room_{random.randint(1, RR_AM)}",
                        f"room_{random.randint(1, RR_AM)}", "room_boss"],
                       [f"room_{random.randint(1, RR_AM)}", f"room_{random.randint(1, RR_AM)}",
                        f"room_{random.randint(1, RR_AM)}", f"treasure_room_2"]]
        self.map = [[Room(r + ".tmx", self.free_tiles) for r in row] for row in self.id_map]
        self.curr_room = self.map[1][0]
        self.cr_yx = (1, 0)
        self.map_tile_size = 48
        self.trsr_taken = False
        self.heal_taken = False

    def render(self, screen):
        self.curr_room.render(screen)
        self.block_edges()
        self.treasure_taken()
        map_net = pygame.image.load("data/images/map_net.png")
        clearCheck = {False: (76, 173, 105),
                      True: (103, 239, 146)}
        for y in range(3):
            for x in range(4):
                rect = pygame.Rect(x * self.map_tile_size + 852,
                                   y * self.map_tile_size + 80,
                                   self.map_tile_size, self.map_tile_size)
                screen.fill(clearCheck[self.map[y][x].clear], rect)
        screen.blit(map_net, (849, 77))
        icon = pygame.image.load(f"{PLAYER_DIR}/player_front.png")
        delta = (icon.get_width() - self.map_tile_size) // 2
        screen.blit(icon, ((self.cr_yx[1] * self.map_tile_size - delta + 852,
                            self.cr_yx[0] * self.map_tile_size - delta + 80)))

    def change_curr_room(self, position):
        self.cr_yx = (position[1], position[0])
        self.curr_room = self.map[position[1]][position[0]]
        self.curr_room.spawn_enemies()

    def get_curr_room(self):
        return self.cr_yx

    def block_edges(self):
        clears = sum([sum([j.clear for j in i]) for i in self.map])
        if self.cr_yx[0] - 1 not in range(3) and self.cr_yx != (1, 3):
            self.curr_room.tiles_map[0][12] = 12
            image = self.curr_room.map.get_tile_image(11, 0, 0)
            screen.blit(image, (12 * TILE_SIZE + 20, 20))
        if self.cr_yx[0] + 1 not in range(3):
            self.curr_room.tiles_map[16][12] = 32
            image = self.curr_room.map.get_tile_image(10, 16, 0)
            screen.blit(image, (12 * TILE_SIZE + 20, 16 * TILE_SIZE + 20))
        if self.cr_yx[1] - 1 not in range(3):
            self.curr_room.tiles_map[8][0] = 21
            image = self.curr_room.map.get_tile_image(0, 6, 0)
            screen.blit(image, (20, 8 * TILE_SIZE + 20))
        if self.cr_yx[1] + 1 not in range(3):
            self.curr_room.tiles_map[8][24] = 23
            image = self.curr_room.map.get_tile_image(24, 6, 0)
            screen.blit(image, (24 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))
        if (clears >= 5 and self.cr_yx == (0, 2) or
                clears >= 7 and self.cr_yx == (2, 2) or
                clears >= 11 and self.cr_yx == (1, 2)):
            self.curr_room.tiles_map[8][24] = 25
            image = self.curr_room.map.get_tile_image(24, 8, 0)
            screen.blit(image, (24 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))

    def treasure_taken(self):
        if self.trsr_taken and self.curr_room.roomID == "treasure_room_1.tmx":
            self.curr_room.tiles_map[8][12] = 1
            self.curr_room.clear = True
            image = self.curr_room.map.get_tile_image(4, 8, 0)
            screen.blit(image, (12 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))
        if self.heal_taken and self.curr_room.roomID == "treasure_room_2.tmx":
            self.curr_room.tiles_map[8][12] = 1
            self.curr_room.clear = True
            image = self.curr_room.map.get_tile_image(4, 8, 0)
            screen.blit(image, (12 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))


class Enemy:
    def __init__(self, position):
        self.hp = 5
        self.x, self.y = position
        self.image = pygame.image.load(f"{PLAYER_DIR}/player_front.png")
        self.delay = 250
        pygame.time.set_timer(ENEMY_EVENT_TYPE, self.delay)

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def change_pic(self, newpic):
        self.image = pygame.image.load(f"data/images/enemy/{newpic}")

    def render(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE + 20,
                                 self.y * TILE_SIZE + 20))


class Crow(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.change_pic("crow/crow_front.png")


class HayRoll(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.change_pic("hay_roll/hay_roll_1.png")
        self.picID = "1"
        self.hp = 3
        self.direction = [-1, -1]

    def set_direction(self, direction):
        self.direction = direction


class Boss(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.hp = 230
        self.hp_image = pygame.image.load("data/images/enemy/scarecrow/scarecrow_hp.png")
        self.bossbar_image = pygame.image.load("data/images/enemy/scarecrow/bossbar.png")
        self.change_pic("scarecrow/scarecrow.png")
        self.area = [(12, 8), (12, 7)]
        self.first_phase_state = 0
        self.fph_place = [(0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    def get_position(self):
        return self.area

    def set_position(self, position):
        self.x, self.y = position
        self.area = [position, tuple([position[0], position[1] - 1])]

    def first_phase_move(self):
        newpos = (12 + self.fph_place[self.first_phase_state][0],
                  8 + self.fph_place[self.first_phase_state][1])
        self.set_position(newpos)
        self.first_phase_state += 1
        self.first_phase_state = self.first_phase_state % 8

    def render(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE + 20,
                                 (self.y - 1) * TILE_SIZE + 20))
        for i in range(self.hp):
            screen.blit(self.hp_image, (550 + i * 2, 590))
        screen.blit(self.bossbar_image, (547, 587))


class BossHayRoll(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.change_pic("scarecrow/scarecrow_attack_2.png")
        self.picID = "1"
        self.direction = -1
        self.hp = 999

    def set_direction(self, direction):
        self.direction = direction


class BossHayfork(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.state = 0
        self.hp = 999
        self.change_pic("scarecrow/hollow.png")

    def check_state(self):
        self.state += 1
        self.state %= 15
        if 0 <= self.state <= 4:
            self.change_pic("scarecrow/hollow.png")
        if 5 <= self.state <= 9:
            self.change_pic("scarecrow/scarecrow_attack_warn.png")
        if 10 <= self.state <= 14:
            self.change_pic("scarecrow/scarecrow_attack_1.png")


class Player:
    def __init__(self, position, pic):
        self.x, self.y = position
        self.image = pygame.image.load(f"data/images/player/{pic}")
        self.hp_image = pygame.image.load(f"data/images/player/hp.png")
        self.hp = 6
        self.direction = "down"

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def change_pic(self, newpic):
        self.image = pygame.image.load(f"data/images/player/{newpic}")

    def render(self, screen):
        screen.blit(self.image, (self.x * TILE_SIZE + 20,
                                 self.y * TILE_SIZE + 20))
        for i in range(self.hp):
            screen.blit(self.hp_image, (20 + i * 50, 590))


class Weapon:
    def __init__(self, position):
        with open(f"{WEAPON_DIR}/weapons_data.json") as f:
            self.types = json.load(f)
        self.set_curr_weapon("sword")
        self.attack_area = []
        self.x = position[0]
        self.y = position[1]
        self.im_id = 1

    def set_curr_weapon(self, type):
        self.type = type
        self.damage = self.types[type]["atk"]
        self.x_area = self.types[type]["x_area"]
        self.y_area = self.types[type]["y_area"]
        self.attack_im = pygame.image.load(f"{WEAPON_DIR}/{self.type}_attack.png")
        self.info_im = pygame.image.load(f"{WEAPON_DIR}/{self.type}_info.png")
        self.info_im = pygame.transform.scale(self.info_im, (230, 230))

    def set_position(self, position):
        self.x = position[0]
        self.y = position[1]

    def attack(self, direction, screen):
        if self.im_id == 1:
            self.attack_im = pygame.image.load(f"{WEAPON_DIR}/{self.type}_attack.png")
            self.im_id = abs(self.im_id - 1)
        elif self.im_id == 0:
            self.attack_im = pygame.image.load(f"{WEAPON_DIR}/{self.type}_attack_2.png")
            self.im_id = abs(self.im_id - 1)
        if direction == "left":
            attack_area = [[self.x + i[0], self.y + i[1]] for i in self.types[self.type]["-x_area"]]
            shown_im = pygame.transform.rotate(self.attack_im, 90)
        elif direction == "right":
            attack_area = [[self.x + i[0], self.y + i[1]] for i in self.types[self.type]["x_area"]]
            shown_im = pygame.transform.rotate(self.attack_im, 270)
        elif direction == "down":
            attack_area = [[self.x + i[0], self.y + i[1]] for i in self.types[self.type]["y_area"]]
            shown_im = pygame.transform.rotate(self.attack_im, 180)
        elif direction == "up":
            attack_area = [[self.x + i[0], self.y + i[1]] for i in self.types[self.type]["-y_area"]]
            shown_im = pygame.transform.rotate(self.attack_im, 0)
        screen.blit(shown_im, (attack_area[0][0] * TILE_SIZE + 20,
                               attack_area[0][1] * TILE_SIZE + 20))
        return [tuple(i) for i in attack_area]

    def render(self, screen):
        screen.blit(self.info_im, (833, 300))


class Particle(pygame.sprite.Sprite):
    def __init__(self, pos, dx, dy, particle, border_rect):
        super().__init__(all_sprites)
        self.particle = [pygame.image.load(f"data/images/particles/{particle}_particle.png")]
        for scale in (1, 3, 5):
            self.particle.append(pygame.transform.scale(self.particle[0], (scale, scale)))
        self.image = random.choice(self.particle)
        self.rect = self.image.get_rect()
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.border_rect = border_rect

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if not self.rect.colliderect(self.border_rect):
            self.kill()


class Game:
    def __init__(self, player, map, weapon):
        self.player = player
        self.map = map
        self.weapon = weapon
        self.boss_music_start = False
        self.boss_defeated = False
        self.score = 0

    def render(self, screen):
        self.map.render(screen)
        self.player.render(screen)
        self.weapon.render(screen)

    def update_player(self):
        if self.player.hp <= 0:
            self.player.change_pic("hollow.png")
            return
        next_x, next_y = self.player.get_position()
        if pygame.key.get_pressed()[pygame.K_a] or pygame.key.get_pressed()[pygame.K_LEFT]:
            self.player.change_pic("player_left.png")
            self.player.direction = "left"
            next_x -= 1
        if pygame.key.get_pressed()[pygame.K_d] or pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.player.change_pic("player_right.png")
            self.player.direction = "right"
            next_x += 1
        if pygame.key.get_pressed()[pygame.K_w] or pygame.key.get_pressed()[pygame.K_UP]:
            self.player.change_pic("player_back.png")
            self.player.direction = "up"
            next_y -= 1
        if pygame.key.get_pressed()[pygame.K_s] or pygame.key.get_pressed()[pygame.K_DOWN]:
            self.player.change_pic("player_front.png")
            self.player.direction = "down"
            next_y += 1
        if self.map.curr_room.is_free((next_x, next_y)):
            self.player.set_position((next_x, next_y))
            self.weapon.set_position(self.player.get_position())
            clock.tick(FPS)
        self.check_move()

    def check_attack(self, screen):
        if self.player.hp <= 0:
            return
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            area = self.weapon.attack(self.player.direction, screen)
            for enemy in self.map.curr_room.enemies:
                if enemy.__class__.__name__ == "Boss":
                    if any([i in area for i in enemy.get_position()]):
                        enemy.hp -= self.weapon.damage
                if enemy.get_position() in area:
                    enemy.hp -= self.weapon.damage

    def check_move(self):
        curr = self.map.get_curr_room()
        if self.map.curr_room.get_tile(self.player.get_position()) == 14:
            self.map.change_curr_room((curr[1], curr[0] - 1))
            self.player.set_position((12, 15))
        if self.map.curr_room.get_tile(self.player.get_position()) == 15:
            self.map.change_curr_room((curr[1], curr[0] + 1))
            self.player.set_position((12, 1))
        if self.map.curr_room.get_tile(self.player.get_position()) == 24:
            self.map.change_curr_room((curr[1] - 1, curr[0]))
            self.player.set_position((23, 8))
        if self.map.curr_room.get_tile(self.player.get_position()) == 25:
            self.map.change_curr_room((curr[1] + 1, curr[0]))
            self.player.set_position((1, 8))

    def move_enemy(self):
        if self.player.hp <= 0:
            return
        for enemy in self.map.curr_room.enemies:
            if enemy.__class__.__name__ == "Crow":
                next_position = self.map.curr_room.crow_path(enemy.get_position(),
                                                             player.get_position())
                curr_position = enemy.get_position()
                if next_position[1] > curr_position[1]:
                    enemy.change_pic("crow/crow_front.png")
                elif next_position[1] < curr_position[1]:
                    enemy.change_pic("crow/crow_back.png")
                elif next_position[0] > curr_position[0]:
                    enemy.change_pic("crow/crow_right.png")
                elif next_position[0] < curr_position[0]:
                    enemy.change_pic("crow/crow_left.png")
                else:
                    enemy.change_pic("crow/crow_front.png")
                enemy.set_position(next_position)
            elif enemy.__class__.__name__ == "HayRoll":
                next_x, next_y, new_direction, changed_dir = self.map.curr_room.roll_path(enemy.get_position(),
                                                                                          enemy.direction)
                enemy.set_direction(new_direction)
                if changed_dir:
                    enemy.picID = ["", "2", "1"][int(enemy.picID)]
                    enemy.change_pic(f"hay_roll/hay_roll_{enemy.picID}.png")
                enemy.set_position((next_x, next_y))
            elif enemy.__class__.__name__ == "Boss":
                if enemy.hp > 115:
                    enemy.first_phase_move()
                else:
                    next_position = self.map.curr_room.crow_path(enemy.get_position()[0],
                                                                 player.get_position())
                    curr_position = enemy.get_position()[0]
                    if next_position[0] > curr_position[0]:
                        enemy.change_pic("scarecrow/scarecrow_3.png")
                    elif next_position[0] <= curr_position[0]:
                        enemy.change_pic("scarecrow/scarecrow_2.png")
                    enemy.set_position(next_position)
            elif enemy.__class__.__name__ == "BossHayRoll":
                next_x, next_y, direction = self.map.curr_room.boss_roll_path(enemy.get_position(), enemy.direction)
                enemy.set_direction(direction)
                enemy.set_position((next_x, next_y))
            elif enemy.__class__.__name__ == "BossHayfork":
                enemy.check_state()

    def check_room(self):
        if not self.boss_music_start and self.map.cr_yx == (1, 3):
            self.boss_music_start = True
            pygame.mixer.music.load("data/sound/Fever-Pitch.mp3")
            pygame.mixer.music.set_volume(0.10)
            pygame.mixer.music.play()

        if not self.map.curr_room.clear:
            if len(self.map.curr_room.enemies) == 0 and "treasure" not in self.map.curr_room.roomID:
                self.map.curr_room.clear = True
                if "boss" not in self.map.curr_room.roomID:
                    with open("data/maps/enemies_data.json") as f:
                        enemies_data = json.load(f)
                        self.score += len(enemies_data[self.map.curr_room.roomID[5:-4]]) * 1000
            for enemy in self.map.curr_room.enemies:
                if enemy.hp <= 0:
                    if enemy.__class__.__name__ == "Boss":
                        self.map.curr_room.enemies = []
                        hay_things_death.set_volume(2)
                        hay_things_death.play()
                        particles_pos = (enemy.get_position()[0][0] * TILE_SIZE + TILE_SIZE,
                                         enemy.get_position()[0][1] * TILE_SIZE + TILE_SIZE)
                        particles_rect = pygame.Rect(enemy.get_position()[0][0] * TILE_SIZE,
                                                     enemy.get_position()[0][1] * TILE_SIZE,
                                                     2 * TILE_SIZE, 3 * TILE_SIZE)
                        self.create_particles(particles_pos, "hay", particles_rect, 30)
                        pygame.mixer.music.load("data/sound/boss_defeated.mp3")
                        pygame.mixer.music.set_volume(0.10)
                        pygame.mixer.music.play()
                        self.score += 1000 * player.hp
                        self.boss_defeated = True
                    else:
                        particles_pos = (enemy.get_position()[0] * TILE_SIZE + TILE_SIZE,
                                         enemy.get_position()[1] * TILE_SIZE + TILE_SIZE)
                        particles_rect = pygame.Rect(enemy.get_position()[0] * TILE_SIZE,
                                                     enemy.get_position()[1] * TILE_SIZE,
                                                     2 * TILE_SIZE, 2 * TILE_SIZE)
                        if enemy.__class__.__name__ == "Crow":
                            crow_death.play()
                            self.create_particles(particles_pos, "crow", particles_rect, 10)
                        else:
                            hay_things_death.play()
                            self.create_particles(particles_pos, "hay", particles_rect, 10)
                        self.map.curr_room.enemies.remove(enemy)

    def check_treasure_room(self):
        if self.map.curr_room.roomID == "treasure_room_1.tmx":
            if self.map.curr_room.get_tile(self.player.get_position()) == 5:
                self.map.trsr_taken = True
                new_weapon = list(self.weapon.types.keys())[random.randint(1, 4)]
                self.weapon.set_curr_weapon(new_weapon)
                treasure_open.play()
        if self.map.curr_room.roomID == "treasure_room_2.tmx":
            if self.map.curr_room.get_tile(self.player.get_position()) == 5:
                self.map.heal_taken = True
                self.player.hp = random.randint(6, 9)
                treasure_open.play()

    def check_player_damage(self):
        if self.player.hp <= 0:
            return False
        crossed = False
        for i in self.map.curr_room.enemies:
            if i.__class__.__name__ == "Boss":
                crossed = self.player.get_position() in [j for j in i.get_position()]
            elif i.__class__.__name__ == "BossHayfork":
                crossed = 10 <= i.state <= 14 and self.player.get_position() == i.get_position()
            else:
                crossed = self.player.get_position() == i.get_position()
            if crossed:
                return crossed
        return crossed

    def create_particles(self, position, particle, border_rect, count):
        particle_count = count
        numbers = list(range(-5, -1)) + list(range(1, 6))
        for _ in range(particle_count):
            Particle(position, random.choice(numbers), random.choice(numbers), particle, border_rect)


def title(screen):
    screens = 4

    pygame.mixer.music.load("data/sound/Main-Menu-3-Snowdin.mp3")
    pygame.mixer.music.set_volume(1)
    pygame.mixer.music.play()

    while screens != 0:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                screens = 0
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                     screens -= 1
        if screens == 4:
            image = pygame.image.load("data/images/title.png")
        elif screens == 3:
            image = pygame.image.load("data/images/tutorial_1.png")
        elif screens == 2:
            image = pygame.image.load("data/images/tutorial_2.png")
        elif screens == 1:
            image = pygame.image.load("data/images/tutorial_3.png")
        screen.blit(image, (0, 0))
        pygame.display.flip()


def main():
    pygame.mixer.music.load("data/sound/Mort-s-Farm-Fun-Farm.mp3")
    pygame.mixer.music.set_volume(0.25)
    pygame.mixer.music.play()

    waiting = 0
    start_waiting = False

    cooldown = 0
    waiting_cooldown = False

    game_over = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == ENEMY_EVENT_TYPE:
                game.move_enemy()
            if game.check_player_damage():
                if not waiting_cooldown:
                    game.player.hp -= 1
                    if game.score - 500 >= 0:
                        game.score -= 500
                    particles_pos = (game.player.get_position()[0] * TILE_SIZE + TILE_SIZE,
                                     game.player.get_position()[1] * TILE_SIZE + TILE_SIZE)
                    particles_rect = pygame.Rect(game.player.get_position()[0] * TILE_SIZE,
                                                 game.player.get_position()[1] * TILE_SIZE,
                                                 2 * TILE_SIZE, 2 * TILE_SIZE)
                    game.create_particles(particles_pos, "chicken", particles_rect, 10)
                    player_damage.play()
                    waiting_cooldown = True
                if game.player.hp <= 0:
                    player_death.play()
                    game_over = True
                    pygame.mixer.music.stop()
                    start_waiting = True
        if game.boss_defeated:
            start_waiting = True
        game.update_player()
        game.check_room()
        game.check_treasure_room()
        screen.fill((76, 173, 105))
        game.render(screen)
        all_sprites.update()
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            if game.player.hp > 0:
                attack_wave.play()
                game.check_attack(screen)
                clock.tick(FPS - 10)
        all_sprites.draw(screen)
        if start_waiting:
            waiting += 1
            if waiting >= 50:
                running = False
        if waiting_cooldown:
            cooldown += 1
            if cooldown >= 10:
                cooldown = 0
                waiting_cooldown = False
        pygame.display.flip()
        clock.tick(FPS)

    running_endscreen = True

    if game_over:
        pygame.mixer.music.load("data/sound/game_over.mp3")
        pygame.mixer.music.play()
        image = pygame.image.load("data/images/game_over.png")
    else:
        print("damn good :)")

    while running_endscreen:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    running_endscreen = False
        screen.blit(image, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)


def start_game(screen):
    will_replay = True

    title(screen)

    while will_replay:
        main()

        global map, player, weapon, game
        map = LevelMap(FREE_TILES)
        player = Player((12, 8), "player_front.png")
        weapon = Weapon(player.get_position())
        game = Game(player, map, weapon)


def sound_file(name):
    return f"data/sound/{name}.mp3"


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    all_sprites = pygame.sprite.Group()
    clock = pygame.time.Clock()
    hit_clock = pygame.time.Clock()

    map = LevelMap(FREE_TILES)
    player = Player((12, 8), "player_front.png")
    weapon = Weapon(player.get_position())
    game = Game(player, map, weapon)

    crow_death = pygame.mixer.Sound(sound_file("crow_death"))
    hay_things_death = pygame.mixer.Sound(sound_file("hay_things_death"))
    player_damage = pygame.mixer.Sound(sound_file("player_damage"))
    player_death = pygame.mixer.Sound(sound_file("player_death"))
    treasure_open = pygame.mixer.Sound(sound_file("treasure_open"))
    attack_wave = pygame.mixer.Sound(sound_file("attack"))
    walking = pygame.mixer.Sound(sound_file("walking"))

    start_game(screen)

    pygame.quit()
