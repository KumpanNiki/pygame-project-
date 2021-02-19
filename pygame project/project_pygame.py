import pygame
import os
import sys
import random


class Background(pygame.sprite.Sprite):  # создание заднего фона
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location


def load_image(name, color_key=None):  # загрузка изображения
    fullname = os.path.join('data', name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as message:
        print('Не удаётся загрузить:', name)
        raise SystemExit(message)
    image = image.convert_alpha()
    if color_key is not None:
        if color_key is None:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    return image


os.environ['SDL_VIDEO_WINDOW_POS'] = '200, 30' # настраиваем координаты окна
pygame.init()
SCREEN_SIZE = (880, 640) # размеры окна
screen = pygame.display.set_mode(SCREEN_SIZE)
FPS = 60 # фпс
# изображения
TILE_IMAGES = {
    'wall': load_image('препятствие.png'),
    'empty': load_image('квадратик.png'),
    'enemy': load_image('враг.gif')
}
player_image = load_image('герой.png')
tile_width = tile_height = 72


class Button:  # создание кнопки
    def __init__(self, position, size, clr=(100, 100, 100), cngclr=None, func=None, text='', font="Segoe Print",
                 font_size=10, font_clr=(0, 0, 0)):
        self.clr = clr
        self.size = size
        self.func = func
        self.surf = pygame.Surface(size)
        self.rect = self.surf.get_rect(center=position)
        if cngclr:
            self.cngclr = cngclr
        else:
            self.cngclr = clr
        if len(clr) == 4:
            self.surf.set_alpha(clr[3])
        self.font = pygame.font.SysFont(font, font_size)
        self.txt = text
        self.font_clr = font_clr
        self.txt_surf = self.font.render(self.txt, 1, self.font_clr)
        self.txt_rect = self.txt_surf.get_rect(center=[wh // 2 for wh in self.size])

    def draw(self, screen):
        self.mouseover()
        self.surf.fill(self.curclr)
        self.surf.blit(self.txt_surf, self.txt_rect)
        screen.blit(self.surf, self.rect)

    def mouseover(self):
        self.curclr = self.clr
        pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(pos):
            self.curclr = self.cngclr

    def call_back(self, *args):
        if self.func:
            return self.func(*args)


class Text:  # создание текста
    def __init__(self, msg, position, clr=(100, 100, 100), font="Segoe Print", font_size=15, mid=False):
        self.position = position
        self.font = pygame.font.SysFont(font, font_size)
        self.txt_surf = self.font.render(msg, 1, clr)
        if len(clr) == 4:
            self.txt_surf.set_alpha(clr[3])
        if mid:
            self.position = self.txt_surf.get_rect(center=position)

    def draw(self, screen):
        screen.blit(self.txt_surf, self.position)


damage = 200  # урон героя
radius = 146  # радиус урона героя
k = 2  # количество энергии
h = 100  # здоровье героя
h_e = 1000  # здоровье первого врага
h_e_1 = 900  # здоровье второго врага
damage_enemy = 30  # урон первого врвга
damage_enemy_1 = 10  # урон второго врвга
radius_enemy_1 = 73  # радиус урона второго врага
radius_enemy = 146  # радиус урона первого врвга
sound = pygame.mixer.Sound('автомат.wav')  # звук выстрела
step = pygame.mixer.Sound('шаг.wav')  # звук шагов


def weapon1():  # взятие первого оружия
    global f1, damage, radius, sound, weapon_now
    weapon_now = load_image('оружие1.png')
    radius = 146
    damage = 200
    sound = pygame.mixer.Sound('автомат.wav')
    sound1 = pygame.mixer.Sound('кнопка.wav')
    sound1.play()


def weapon2():  # взятие второго оружие
    global damage, radius, sound, weapon_now
    weapon_now = load_image('оружие2.png')
    radius = 219
    damage = 300
    sound = pygame.mixer.Sound('снайперская.wav')
    sound1 = pygame.mixer.Sound('кнопка.wav')
    sound1.play()


def weapon3():  # взятие третьего оружия
    global damage, radius, sound, weapon_now
    weapon_now = load_image('оружие3.png')
    radius = 73
    damage = 400
    sound = pygame.mixer.Sound('дробовик.wav')
    sound1 = pygame.mixer.Sound('кнопка.wav')
    sound1.play()


def end():  # конец хода
    global k, shoot
    if h_e > 0:
        move(enemy, random.choice(['up', 'down', 'left', 'right']))
    if h_e_1 > 0:
        move(enemy_1, random.choice(['up', 'down', 'left', 'right']))
    k += 2
    shoot = True


def game():  # начало самой игры
    global flag
    flag = True


def regen():  # регенерация
    global k, h
    if k > 1:
        h += 10
        k -= 2
        sound1 = pygame.mixer.Sound('лечение.wav')
        sound1.play()


class SpriteGroup(pygame.sprite.Group):  # группа спрайтов
    def __init__(self):
        super().__init__()

    def get_event(self, event):
        for sprite in self:
            sprite.get_event(event)


class Sprite(pygame.sprite.Sprite):  # спрайт
    def __init__(self, group):
        super().__init__(group)
        self.rect = None

    def get_event(self, event):
        pass


class Tile(Sprite):  # создание окружения
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(sprite_group)
        self.image = TILE_IMAGES[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 180, tile_height * pos_y)


class Player(Sprite):  # создание игрока
    def __init__(self, pos_x, pos_y):
        super().__init__(hero_group)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 180, tile_height * pos_y)
        self.pos = (pos_x, pos_y)

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0] + 180, tile_height * self.pos[1])

    def coords(self):
        return tile_width * self.pos[0] + 180, tile_height * self.pos[1]

    def change_image(self):
        self.image = load_image('герой ранен.png')

    def change(self):
        self.image = player_image

    def shoot(self):
        self.image = load_image('герой стреляет.png')


class Enemy(Sprite):  # создание врага
    def __init__(self, pos_x, pos_y):
        super().__init__(hero_group)
        self.image = TILE_IMAGES['enemy']
        self.rect = self.image.get_rect().move(
            tile_width * pos_x + 180, tile_height * pos_y)
        self.pos = (pos_x, pos_y)

    def coords(self):
        return tile_width * self.pos[0] + 180, tile_height * self.pos[1]

    def move(self, x, y):
        self.pos = (x, y)
        self.rect = self.image.get_rect().move(
            tile_width * self.pos[0] + 180, tile_height * self.pos[1])

    def im(self):
        self.image = load_image('враг ранен.png')

    def return_im(self):
        self.image = TILE_IMAGES['enemy']

    def sh(self):
        self.image = load_image('враг стреляет.gif')

    def dead(self):
        self.image = TILE_IMAGES['empty']


player = None
running = True
clock = pygame.time.Clock()
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
sprite_group = SpriteGroup()
hero_group = SpriteGroup()


def terminate():  # завершение игры
    pygame.quit()
    sys.exit()


def start_screen_1():  # зарузка первого стартового окна
    global FPS
    pygame.display.set_caption('ПРИВЕТСТВИЕ')
    fon = pygame.transform.scale(load_image('fon1.jpg'), SCREEN_SIZE)
    screen.blit(fon, (0, 0))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
        pygame.display.flip()
        clock.tick(0.6)
        return


def start_screen():  # зарузка второго стартового окна
    global flag
    pygame.display.set_caption('ГОТОВЫ?')
    intro_text = 'Готов, боец?'
    fon = pygame.transform.scale(load_image('fon.jpg'), SCREEN_SIZE)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 60)
    text_coord = 200
    but = Button((540, 300), (160, 30), (255, 255, 255), (255, 0, 0), game, 'Начать сражение', font_size=15)
    string_rendered = font.render(intro_text, 1, pygame.Color('black'))
    intro_rect = string_rendered.get_rect()
    intro_rect.top = text_coord
    intro_rect.x = 400
    screen.blit(string_rendered, intro_rect)
    while True:
        but.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if but.rect.collidepoint(pos):
                        but.call_back()
                    if flag:
                        flag = False
                        return
        pygame.display.flip()
        clock.tick(FPS)


def hint():  # подсказка
    sound1 = pygame.mixer.Sound('кнопка.wav')
    sound1.play()
    global flag
    pygame.display.set_caption('ПОДСКАЗКА')
    intro_text = ["Чтобы выбрать оружие, нужно нажать на кнопку.",
                  "Каждое оружие имеет свои радиус атаки и урон.",
                  "За каждое действие игрока используется энергия.",
                  "После нажатия кнопки <конец хода> прибавляется энергия.",
                  "Чтобы нанести урон врагу, наведите на него курсор мышки и кликните на него.",
                  "Цель игры : остаться в живых и победить всех врагов.",
                  "УДАЧИ       :)"]
    fon = pygame.transform.scale(load_image('подсказка.jpg'), SCREEN_SIZE)
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 25)
    text_coord = 90
    but = Button((560, 500), (300, 50), (220, 220, 0), (255, 0, 0), game, 'Закрыть подсказку', font="Insiced",
                 font_size=23)
    for line in intro_text:
        string_rendered = font.render(line, 1, pygame.Color('black'))
        intro_rect = string_rendered.get_rect()
        text_coord += 30
        intro_rect.top = text_coord
        intro_rect.x = 30
        text_coord += intro_rect.height
        screen.blit(string_rendered, intro_rect)
    while True:
        but.draw(screen)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    if but.rect.collidepoint(pos):
                        but.call_back()
                    if flag:
                        flag = False
                        pygame.display.set_caption('СРАЖЕНИЕ')
                        sound1 = pygame.mixer.Sound('кнопка.wav')
                        sound1.play()
                        return
                    else:
                        pass
        pygame.display.flip()
        clock.tick(FPS)


def load_level(filename):  # загрузка уровня
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))


def generate_level(level):  # создание уровня
    new_player, new_enemy, new_enemy_1, x, y = None, None, None, None, None
    k = 0
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Tile('empty', x, y)
                if k == 0:
                    new_enemy = Enemy(x, y)
                    k += 1
                else:
                    new_enemy_1 = Enemy(x, y)
                level[y][x] = '#'
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
                level[y][x] = '#'
            elif level[y][x] == '&':
                Tile('empty', x, y)
                Tile('wall', x, y)
                level[y][x] = '#'
    return new_player, new_enemy, new_enemy_1, x, y


def i(heroo, movement):  # вспомогательная функция движения героев
    x, y = heroo.pos
    level_map[y][x] = '.'
    if movement == "up":
        if y > 0 and level_map[y - 1][x] == ".":
            heroo.move(x, y - 1)
            level_map[y - 1][x] = "#"
        else:
            level_map[y][x] = '#'
    elif movement == "down":
        if y < max_y and level_map[y + 1][x] == ".":
            heroo.move(x, y + 1)
            level_map[y + 1][x] = "#"
        else:
            level_map[y][x] = '#'
    elif movement == "left":
        if x > 0 and level_map[y][x - 1] == ".":
            heroo.move(x - 1, y)
            level_map[y][x - 1] = "#"
        else:
            level_map[y][x] = '#'
    elif movement == "right":
        if x < max_x and level_map[y][x + 1] == ".":
            heroo.move(x + 1, y)
            level_map[y][x + 1] = "#"
        else:
            level_map[y][x] = '#'


def move(heroo, movement):  # движение героев
    global k, h, damage_enemy, radius_enemy, h_e, h_e_1, f, sh, sh_1
    x, y = heroo.pos
    a, b = enemy.pos
    c, d = enemy_1.pos
    level_map[y][x] = '.'
    if h_e == 0:
        level_map[b][a] = '.'
    if h_e_1 == 0:
        level_map[d][c] = '.'
    i(heroo, movement)
    while level_map[y][x] == '#' and heroo == enemy:
        i(enemy, random.choice(['up', 'down', 'left', 'right']))
    while level_map[y][x] == '#' and heroo == enemy_1:
        i(enemy_1, random.choice(['up', 'down', 'left', 'right']))
    step.play()
    clock.tick(20)
    pos = hero.coords()
    sound = pygame.mixer.Sound('автомат.wav')
    if heroo == enemy:
        if pos[0] in range(enemy.coords()[0] - radius_enemy, enemy.coords()[0] + radius_enemy) and pos[1] in range(
                enemy.coords()[1] - radius_enemy, enemy.coords()[1] + radius_enemy):
            if h - damage_enemy <= 0:
                h = 0
            else:
                h -= damage_enemy
            sh = True
            enemy.sh()
            sound.play()
            hero.change_image()
            f = True
    if heroo == enemy_1:
        if pos[0] in range(enemy_1.coords()[0] - radius_enemy_1, enemy_1.coords()[0] + radius_enemy_1) and pos[1] \
                in range(enemy_1.coords()[1] - radius_enemy_1, enemy_1.coords()[1] + radius_enemy_1):
            if h - damage_enemy_1 <= 0:
                h = 0
            else:
                h -= damage_enemy_1
            sh_1 = True
            enemy_1.sh()
            sound.play()
            hero.change_image()
            f = True
    if level_map[y][x] != '#' and heroo == hero:
        k -= 1


sh = False  # первый враг стреляет
flag = False  # начало игры
shoot = True  # один выстрел за ход
f = False  # в героя выстрелели
ch = False  # первый враг ранен
ch_1 = False  # второй враг ранен
sh_1 = False  # второй враг стреляет
start_screen_1()
start_screen()
level_map = load_level("level.txt")
hero, enemy, enemy_1, max_x, max_y = generate_level(level_map)
font_size = 110
font = pygame.font.Font(None, font_size)
# далее кнопки и текст
button1 = Button(position=(90, 160), size=(160, 15), clr=[0, 220, 220], cngclr=(250, 200, 200), func=weapon1,
                 text='Использовать автомат', font="Summer camp", font_size=18)
button2 = Button((90, 260), (160, 15), (0, 220, 220), (250, 200, 200), weapon2, 'Ипользовать снайперскую',
                 font="Summer camp",
                 font_size=18)
button3 = Button((90, 360), (160, 15), (0, 220, 220), (250, 200, 200), weapon3, 'Использовать дробовик',
                 font="Summer camp",
                 font_size=18)
button4 = Button((775, 600), (160, 44), (0, 220, 220), (0, 255, 0), end, 'Конец хода', font="impact", font_size=18)
button6 = Button((775, 550), (160, 45), (0, 220, 220), (100, 100, 200), hint, 'ПОДСКАЗКА', font='Insiced',
                 font_size=23)
regeneration = Button((90, 450), (160, 50), (0, 220, 220), (255, 0, 200), regen, 'Регенерация', font="Summer camp",
                      font_size=23)
regeneration_text_1 = Text('- 2 единицы энергии', (5, 397), clr=[0, 0, 0], font="Segoe Print", font_size=11)
regeneration_text_2 = Text('+ 10 единиц здоровья', (5, 409), clr=[0, 0, 0], font="Segoe Print", font_size=11)
button_list = [button1, button2, button3, button4, button6, regeneration]
choose_weapon = Text('Выберете оружие', (10, 10), clr=[0, 0, 0], font="juniorstar", font_size=26)
damage_range1 = Text('Урон: 300    Радиус: 2 клетки', (5, 120), clr=[0, 0, 0], font="Segoe Print", font_size=11)
damage_range2 = Text('Урон: 200    Радиус: 3 клетки', (5, 220), clr=[0, 0, 0], font="Segoe Print", font_size=11)
damage_range3 = Text('Урон: 400    Радиус: 1 клетка', (5, 320), clr=[0, 0, 0], font="Segoe Print", font_size=11)
weapon_is_used = Text('Текущее оружее', (10, 500), clr=[0, 20, 0], font="juniorstar", font_size=26)
energy = Text('Энергия', (300, 540), clr=[0, 0, 0], font="juniorstar", font_size=30)
health_hero = Text('Здоровье', (500, 540), clr=[0, 0, 0], font="juniorstar", font_size=30)
health_enemy = Text('Здоровье 1- го врага', (690, 100), clr=[0, 0, 0], font="juniorstar", font_size=26)
health_enemy_1 = Text('Здоровье 2- го врага', (690, 200), clr=[0, 0, 0], font="juniorstar", font_size=26)
en = load_image('враг.png')
en1 = load_image('враг.png')
weapon_1 = load_image('оружие1.png')
weapon_2 = load_image('оружие2.png')
weapon_3 = load_image('оружие3.png')
weapon_now = load_image('оружие1.png')
enemy_weapon = Text('Оружие 1-го врага', (690, 270), clr=[0, 0, 0], font="juniorstar", font_size=26)
enemy_weapon_characteristic = Text('Урон: {}, радиус: 2 клетки'.format(damage_enemy), (690, 310), clr=[0, 0, 0],
                                   font="juniorstar", font_size=20)
enemy_weapon_characteristic_1 = Text('Урон: {}, радиус: 1 клетка'.format(damage_enemy_1), (690, 430), clr=[0, 0, 0],
                                     font="juniorstar", font_size=20)
enemy_weapon_1 = Text('Оружие 2-го врага', (690, 400), clr=[0, 0, 0], font="juniorstar", font_size=26)
first = Text('Первый', (700, 10), clr=[0, 0, 0], font="juniorstar", font_size=26)
second = Text('Второй', (780, 10), clr=[0, 0, 0], font="juniorstar", font_size=26)
weapon_enemy = load_image('оружие1.png')
weapon_enemy_1 = load_image('оружие1.png')
BackGround = Background('фон.jpg', [0, 0])
pygame.display.set_caption('СРАЖЕНИЕ')
while running:
    FPS = 60
    if h <= 0 or (h_e <= 0 and h_e_1 <= 0):
        running = False
        clock.tick(1)
    if f:
        FPS = 1
        hero.change()
        f = False
    else:
        FPS = 60
    if h_e <= 0:
        enemy.dead()
    elif h_e_1 <= 0:
        enemy_1.dead()
    if ch:
        FPS = 1
        enemy.return_im()
        ch = False
    if sh:
        FPS = 1
        enemy.return_im()
        sh = False
    if sh_1:
        FPS = 1
        enemy_1.return_im()
        sh_1 = False
    if ch_1:
        FPS = 1
        enemy_1.return_im()
        ch_1 = False
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                pos = pygame.mouse.get_pos()
                if pos[0] in range(enemy.coords()[0], enemy.coords()[0] + 72) and pos[1] in range(enemy.coords()[1],
                                                                                                  enemy.coords()[
                                                                                                      1] + 72) and pos[
                    0] in range(hero.coords()[0] - radius, hero.coords()[0] + radius + 72) and pos[1] in range(
                    hero.coords()[1] - radius, hero.coords()[1] + radius + 72) and shoot and k > 0:
                    if h_e - damage <= 0:
                        h_e = 0
                    else:
                        h_e -= damage
                    ch = True
                    k -= 1
                    shoot = False
                    f = True
                    sound.play()
                    hero.shoot()
                    enemy.im()
                elif pos[0] in range(enemy_1.coords()[0], enemy_1.coords()[0] + 72) and pos[1] in range(
                        enemy_1.coords()[1],
                        enemy_1.coords()[
                            1] + 72) and pos[
                    0] in range(hero.coords()[0] - radius, hero.coords()[0] + radius + 72) and pos[1] in range(
                    hero.coords()[1] - radius, hero.coords()[1] + radius + 72) and shoot and k > 0:
                    if h_e_1 - damage <= 0:
                        h_e_1 = 0
                    else:
                        h_e_1 -= damage
                    ch_1 = True
                    k -= 1
                    shoot = False
                    f = True
                    sound.play()
                    hero.shoot()
                    enemy_1.im()
                for b in button_list:
                    if b.rect.collidepoint(pos):
                        b.call_back()
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if k > 0:
                if event.key == pygame.K_UP:
                    move(hero, "up")
                elif event.key == pygame.K_DOWN:
                    move(hero, "down")
                elif event.key == pygame.K_LEFT:
                    move(hero, "left")
                elif event.key == pygame.K_RIGHT:
                    move(hero, "right")
    for b in button_list:
        b.draw(screen)
    choose_weapon.draw(screen)
    weapon_is_used.draw(screen)
    energy_count = Text('{}'.format(k), (330, 550), clr=[225, 255, 0], font="Segoe Print", font_size=40)
    health_enemy_count = Text('{}'.format(h_e), (730, 130), clr=[225, 0, 0], font="Segoe Print", font_size=20)
    health_enemy_1_count = Text('{}'.format(h_e_1), (730, 230), clr=[225, 0, 0], font="Segoe Print", font_size=20)
    health_count = Text('{}'.format(h), (500, 550), clr=[225, 0, 0], font="Segoe Print", font_size=40)
    energy_count.draw(screen)
    health_count.draw(screen)
    health_enemy_count.draw(screen)
    enemy_weapon_characteristic.draw(screen)
    enemy_weapon_characteristic_1.draw(screen)
    health_enemy_1_count.draw(screen)
    energy.draw(screen)
    enemy_weapon.draw(screen)
    enemy_weapon_1.draw(screen)
    damage_range1.draw(screen)
    damage_range2.draw(screen)
    damage_range3.draw(screen)
    health_hero.draw(screen)
    health_enemy_1.draw(screen)
    health_enemy.draw(screen)
    regeneration_text_1.draw(screen)
    regeneration_text_2.draw(screen)
    pygame.display.flip()
    screen.fill([255, 255, 255])
    screen.blit(BackGround.image, BackGround.rect)
    screen.blit(weapon_1, (10, 70))
    screen.blit(weapon_2, (10, 170))
    screen.blit(weapon_3, (10, 270))
    screen.blit(weapon_now, (10, 550))
    if h_e != 0:
        screen.blit(en, (700, 30))
        first.draw(screen)
    if h_e_1 != 0:
        screen.blit(en1, (780, 30))
        second.draw(screen)
    screen.blit(weapon_enemy, (700, 350))
    screen.blit(weapon_enemy_1, (700, 460))
    sprite_group.draw(screen)
    hero_group.draw(screen)
    clock.tick(FPS)
pygame.quit()
pygame.init()
screen = pygame.display.set_mode((880, 640))
if h == 0:
    game_over = load_image('download.gif')
elif h_e == 0 and h_e_1 == 0:
    game_over = load_image('download1.gif')
else:
    game_over = load_image('download2.gif')
clock = pygame.time.Clock()
pygame.display.set_caption('Game over')
x = - 600
y = 0
running = True
screen.fill((0, 0, 255))
# загрузка концовки игры
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or event.type == pygame.KEYDOWN or \
                event.type == pygame.MOUSEBUTTONDOWN:
            running = False
    if x < 0:
        x += 20
        screen.blit(game_over, (x, y))
        pygame.display.flip()
    clock.tick(60)
