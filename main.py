import pygame
import pytmx
import random
import json


window_size = width, height = 1080, 700
FPS = 30
MAPS_DIR = "data/maps"
TILE_SIZE = 32
free_tiles = [1, 2, 3, 4, 5, 24, 14, 25, 15, 44, 34, 45, 35,
              71, 72, 73, 81, 82, 83, 91, 92, 93, 54, 64]
rr_am = 13
ENEMY_EVENT_TYPE = 30

ENEMY_HIT_DELAY = 300
ENEMY_HIT = pygame.USEREVENT + 1


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
        if roomID in ["start_room.tmx", "boss_room.tmx"]:
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

    def find_path(self, start, target):
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
            self.enemies_am = len(self.enemies)


class LevelMap:
    def __init__(self, free_tiles):
        self.free_tiles = free_tiles
        self.id_map = [[f"room_{random.randint(1, rr_am)}", f"room_{random.randint(1, rr_am)}",
                     f"room_{random.randint(1, rr_am)}", f"treasure_room_{random.randint(1, 2)}"],
                    ["start_room", f"room_{random.randint(1, rr_am)}",
                     f"room_{random.randint(1, rr_am)}", "boss_room"],
                    [f"room_{random.randint(1, rr_am)}", f"room_{random.randint(1, rr_am)}",
                     f"room_{random.randint(1, rr_am)}"]]
        print(self.id_map)
        self.map = [[Room(r + ".tmx", self.free_tiles) for r in row] for row in self.id_map]
        self.curr_room = self.map[1][0]
        self.cr_yx = (1, 0)
        self.map_tile_size = 48
        self.trsr_taken = False

    def render(self, screen):
        self.curr_room.render(screen)
        self.block_edges()
        self.treasure_taken()
        clearCheck = {False: (76, 173, 105),
                      True: (103, 239, 146),}
        for y in range(3):
            for x in range(4):
                rect = pygame.Rect(x * self.map_tile_size + 852,
                                   y * self.map_tile_size + 80,
                                   self.map_tile_size, self.map_tile_size)
                try:
                    screen.fill(clearCheck[self.map[y][x].clear], rect)
                    pygame.draw.rect(screen, (42, 99, 16), rect, 3)
                except IndexError:
                    continue
        icon = pygame.image.load("data/images/player/player_front.png")
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
        if self.cr_yx[1] + 1 not in range(3) and self.cr_yx not in [(1, 2), (0, 2)]:
            self.curr_room.tiles_map[8][24] = 23
            image = self.curr_room.map.get_tile_image(24, 6, 0)
            screen.blit(image, (24 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))

    def treasure_taken(self):
        if self.trsr_taken and "treasure" in self.curr_room.roomID:
            self.curr_room.tiles_map[8][12] = 1
            self.curr_room.clear = True
            image = self.curr_room.map.get_tile_image(4, 8, 0)
            screen.blit(image, (12 * TILE_SIZE + 20, 8 * TILE_SIZE + 20))


class Enemy:
    def __init__(self, position):
        self.hp = 5
        self.x, self.y = position
        self.image = pygame.image.load(f"data/images/player/player_front.png")
        self.delay = 250
        pygame.time.set_timer(ENEMY_EVENT_TYPE, self.delay)

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def change_pic(self, newpic):
        self.image = pygame.image.load(f"data/images/enemy/{newpic}")

    def render(self, screen):
        delta = (self.image.get_width() - TILE_SIZE) // 2
        screen.blit(self.image, (self.x * TILE_SIZE - delta + 20,
                                 self.y * TILE_SIZE - delta + 20))


class Crow(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.change_pic("crow/crow_front.png")


class HayRoll(Enemy):
    def __init__(self, position):
        super().__init__(position)
        self.change_pic("hay_roll/hay_roll_1.png")
        self.picID = "1"
        self.direction = [-1, -1]

    def set_direction(self, direction):
        self.direction = direction


class Boss(Enemy):
    def __init__(self, position):
        super().__init__(position)


class Player:
    def __init__(self, position, pic):
        self.x, self.y = position
        self.image = pygame.image.load(f"data/images/player/{pic}")
        self.hp_image = pygame.image.load(f"data/images/hp.png")
        self.hp = 5
        self.direction = "down"

    def get_position(self):
        return self.x, self.y

    def set_position(self, position):
        self.x, self.y = position

    def change_pic(self, newpic):
        self.image = pygame.image.load(f"data/images/player/{newpic}")

    def render(self, screen):
        delta = (self.image.get_width() - TILE_SIZE) // 2
        screen.blit(self.image, (self.x * TILE_SIZE - delta + 20,
                                 self.y * TILE_SIZE - delta + 20))
        for i in range(self.hp):
            screen.blit(self.hp_image, (40 + i * 84, 590))


class Weapon:
    def __init__(self, position):
        with open("data/weapon/weapons_data.json") as f:
            self.types = json.load(f)
        self.set_curr_weapon("sword")
        self.attack_area = []
        self.x = position[0]
        self.y = position[1]

    def set_curr_weapon(self, type):
        self.type = type
        self.damage = self.types[type]["atk"]
        self.x_area = self.types[type]["x_area"]
        self.y_area = self.types[type]["y_area"]
        self.attack_im = pygame.image.load(f"data/weapon/{self.type}_attack.png")
        self.info_im = pygame.image.load(f"data/weapon/{self.type}_info.png")
        self.info_im = pygame.transform.scale(self.info_im, (230, 230))

    def set_position(self, position):
        self.x = position[0]
        self.y = position[1]

    def attack(self, direction, screen):
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

        """for a in attack_area:
            x, y = a[0], a[1]
            rect = pygame.Rect(x * TILE_SIZE + 20,
                                   y * TILE_SIZE + 20,
                                   TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, pygame.Color("white"), rect, 1)"""

        screen.blit(shown_im, (attack_area[0][0] * TILE_SIZE + 20,
                               attack_area[0][1] * TILE_SIZE + 20))
        return [tuple(i) for i in attack_area]

    def render(self, screen):
        screen.blit(self.info_im, (833, 300))

class Game:
    def __init__(self, player, map, weapon):
        self.player = player
        self.map = map
        self.weapon = weapon

    def render(self, screen):
        self.map.render(screen)
        self.player.render(screen)
        self.weapon.render(screen)

    def update_player(self):
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
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            area = self.weapon.attack(self.player.direction, screen)
            for enemy in self.map.curr_room.enemies:
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
        for enemy in self.map.curr_room.enemies:
            if enemy.__class__.__name__ == "Crow":
                next_position = self.map.curr_room.find_path(enemy.get_position(),
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

    def check_room(self):
        if not self.map.curr_room.clear:
            if len(self.map.curr_room.enemies) == 0 and "treasure" not in self.map.curr_room.roomID:
                self.map.curr_room.clear = True
            for enemy in self.map.curr_room.enemies:
                if enemy.hp <= 0:
                    self.map.curr_room.enemies.remove(enemy)

    def check_treasure_room(self):
        if "treasure" in self.map.curr_room.roomID:
            if self.map.curr_room.get_tile(self.player.get_position()) == 5:
                self.map.trsr_taken = True
                new_weapon = list(self.weapon.types.keys())[random.randint(1, 4)]
                self.weapon.set_curr_weapon(new_weapon)

    def check_player_damage(self):
        return self.player.get_position() in [enemy.get_position() for enemy in self.map.curr_room.enemies]


if __name__ == '__main__':
    pygame.init()
    screen = pygame.display.set_mode(window_size)
    pygame.time.set_timer(ENEMY_HIT, ENEMY_HIT_DELAY)

    map = LevelMap(free_tiles)
    player = Player((12, 8), "player_front.png")
    weapon = Weapon(player.get_position())
    game = Game(player, map, weapon)

    clock = pygame.time.Clock()
    hit_clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == ENEMY_EVENT_TYPE:
                game.move_enemy()
            if event.type == ENEMY_HIT and game.check_player_damage():
                game.player.hp -= 1
        game.update_player()
        game.check_room()
        game.check_treasure_room()
        screen.fill((76, 173, 105))
        game.render(screen)
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            game.check_attack(screen)
            clock.tick(FPS - 10)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()