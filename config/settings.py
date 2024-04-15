import os
import random
import pygame
import math
import openpyxl
import colorsys

pygame.init()

# region - GAME Settings
# Window GAME Settings
WINDOW_WIDTH: int = 1200
WINDOW_HEIGHT: int = 750
WG_SIZE = (WINDOW_WIDTH, WINDOW_HEIGHT)
WG_CENTER = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
HUD: int = 102
HUD2: int = WINDOW_HEIGHT - HUD    # total game screen (to move)
MAX_HEIGHT: int = 600              # max height to start animation
FPS = 60

# PLAYER Settings
PLAYER_SIZE = 50  # = image width: 52x57
PLAYER_VELOCITY = 5
PLAYER_BOOST_SCALE = 1.65
PLAYER_MAX_HP = 100
PLAYER_MAX_POISON = 100
PLAYER_MAX_BOOST = 2000
PLAYER_MAX_WRAPS = 5
PLAYER_SLOW_TIME = 1250
PLAYER_AI_TIME = 2  # sek.
ROUND_TIME = 50

# CHEESE settings
CHEESE_SPEED = 4                # initial cheese speed
CHEESE_SPEED_scale = 0.0125     # speed increment  (speed + scale) every cooldown sek.
CHEESE_SPEED_cooldown = 2       # speed increment cooldown
CHEESE_distance_reduction = 5   # reduce distance (time) between respawns (max_y_distance - distance_y_scale)
CHEESE_distance_respawn = 100   # minimum distance(x) between two different cheeses
CHEESE_offset = 45              # offset from the left and right edges of the image when respawning
CHEESE_min_distance = 100       # min distance (time) between disappearance and reappearance (restart)
CHEESE_max_distance = 400       # max distance (time) between disappearance and reappearance (restart) dac 250-750?
CHEESE_bonus_chance = 15        # Percentage chance to drop bonus cheese (0-100)
CHESSE_fake_chance = 11         # Percentage chance to drop fake cheese (0-100)

# TRAP settings
TRAP_draw_time = 3750   # 4500 = 4.5 sek. - how long trap exist after explosion
TRAP_pause_min = 7200   # min and max time between respawn
TRAP_pause_max = 9850
MEDICINE_draw_time = 2250
MEDICINE_pause_min = 16000
MEDICINE_pause_max = 19500

# ITEM Settings
"""
- image cooldown: animation speed - time between images changes 
- extra_time: the image disappears after the end of the extra animation automatically,
              you can extend it (the last graphic in the list) by extra_time 1000=1sec
- rect_first_resize
  rect_second_resize: collision check is performed for self.rect.col (not self rect), self.rect.col is transformed by
                       rect_first_resize for normal animation and by rect_second_resize for animation lasting extra_time
                       (e.g. cracked egg has smaller area than exploding one)reduce the distance (time) between respawns
- min_x / max_y: additional distance (time) - random(min,  max) between restarts (reappearances)
- crush_distance: crush animation starts at Y random (EndOfScreen - crush_distance, EndOfScreen) 
                  Leave crush_distance=0 without animation !
- sounds: path to the sound file
"""
ITEM_dict = {
    'typ': 'image cooldown, extra_time, first_resize, second_resize, offset_x, offset_y, min_x, max_x, min_y, max_y, '
           'crush distance, sound_col ,sound_drop, increase_speed',
    'cat': (75, 0, (0, 0, 0, 0), (0, 0, 0, 0), 0, 70, 500, 1500, 0, 0, 0, None, 'explosion', 0.10),
    'cat_fly': (75, 0, (10, 15, 0, 0), (-10, -10, 5, -10), 0, 70, 6500, 8500, 0, 0, 0, None, 'explosion', 0.10),
    'bird': (75, 0, (15, 20, 0, 0), (-10, -10, 5, -10), 0, 70, 750, 1500, 0, 0, 0, None, 'explosion', 0.10),
    'bird_big': (75, 0, (55, 75, 0, 0), (-10, -10, 5, -10), 0, 70, 500, 1500, 0, 0, 0, None, 'explosion', 0.10),
    'egg': (75, 2500, (0, 0, 0, 0), (10, 40, 0, 20), 30, 0, 0, 0, 2250, 3500, 150, 'egg_crush', 'egg_crush', 0.10),
    'water': (75, 1250, (0, 0, 0, 0), (10, 75, 0, 30), 30, 0, 0, 0, 1500, 2500, 200, 'water_drop', 'water_splash',
              0.05),
    'poison': (75, 1250, (0, 0, 0, 0), (10, 75, 0, 30), 30, 0, 0, 0, 3500, 5500, 50, 'toxic_drop', 'toxic_splash', 0.1),
    'time': (75, 1250, (0, 0, 0, 0), (0, 0, 0, 0), 30, 0, 0, 0, 12500, 15000, 0, 'time', None, 0.025),
    'cola': (55, 1250, (0, 0, 0, 0), (0, 0, 0, 0), 30, 0, 0, 0, 3000, 4000, 0, 'cola', None, 0.025),
}
# endregion


# region - COLORS
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
YELLOW = (255, 212, 37)
YELLOW_2 = (255, 240, 0)
ORANGE = (250, 170, 50)
GRAY = (60, 60, 60)
DARK_WHITE = (180, 180, 180)
GREEN = (45, 255, 45)
RED = (255, 40, 40)
BLUE = (0, 210, 255)
PINK = (251, 81, 131)
PINK_2 = (240, 55, 115)
PINK_MUSIC = (209, 90, 107)
PINK_MENU = (252, 189, 172)

MENU_COLORS = [WHITE, YELLOW, ORANGE, PINK, RED, GREEN, YELLOW_2, PINK_2, DARK_WHITE]


def random_color():
    """ return random color """
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def adjust_contrast(color: tuple[int, int, int], background: tuple[int, int, int] = BLACK, threshold: int = 90):
    """ Function changes color if it has too little contrast to the Background """
    brightness = sum(color) / 3
    background_brightness = sum(background) / 3

    # The difference in brightness between color and background
    brightness_difference = abs(brightness - background_brightness)

    # Use contrast
    if brightness_difference < threshold:
        contrast_color = tuple(max(value, 150) for value in color)
    else:
        contrast_color = color

    return contrast_color


def is_gray(color: tuple[int, int, int], threshold=30):
    """ Function checks if the color is gray """
    r, g, b = color
    h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    return s * 100 < threshold


def create_colors_list(size: int = 3, only_contrast=True, remove_gray=True, only_one_color=False, color=WHITE):
    """
    Function create colors list with random colors
        - only contrast colors or only one color
        - without gray colors
     """
    new_colors = []

    for _ in range(size):
        if only_one_color:
            new_colors.append(color)
        else:
            new_color = random_color()

            if only_contrast:
                new_color = adjust_contrast(new_color)

            if remove_gray and is_gray(new_color):
                while is_gray(new_color):
                    new_color = random_color()

            new_colors.append(new_color)

    return new_colors


# endregion


# region - FONTS
FONT_15 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 15)
FONT_21 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 21)
FONT_25 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 25)
FONT_28 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 28)
FONT_32 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 32)
FONT_36 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 36)
FONT_50 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 50)
FONT_60 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 60)
FONT_65 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 65)
FONT_75 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 75)

FONT_110 = pygame.font.Font('./config/fonts/SpongeboyMeBob.ttf', 110)
FONT_120 = pygame.font.Font('./config/fonts/SpongeboyMeBob.ttf', 175)

FONT_150 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 150)
FONT_160 = pygame.font.Font('./config/fonts/CartoonMadness.ttf', 70)
FONT_170 = pygame.font.Font('./config/fonts/WashYourHand.ttf', 160)

FONT2_165 = pygame.font.Font('./config/fonts/ChillBlood.ttf', 165)
FONT2_175 = pygame.font.Font('./config/fonts/ChillBlood.ttf', 175)

FONT3_165 = pygame.font.Font('./config/fonts/SpongeboyMeBob.ttf', 165)
FONT3_175 = pygame.font.Font('./config/fonts/SpongeboyMeBob.ttf', 175)
# endregion


# region - Functions
def text_width(text, font: pygame.font.Font):
    text_p = font.render(text, True, (255, 255, 255))
    return text_p.get_width()


def draw_text(surface: pygame.Surface, text: str, x: int, y: int, font: pygame.font.Font = None,
              color: tuple[int, int, int] = (255, 255, 255), angle: int = 0, center: bool = True) -> None:
    """ draw text in center x,y or top left corner = (x,y)"""
    font = FONT_36 if font is None else font
    text = font.render(text, True, color)
    rotated_text = pygame.transform.rotate(text, angle)
    if center:
        surface.blit(rotated_text, (x - rotated_text.get_width() // 2, y - rotated_text.get_height() // 2))
    else:
        surface.blit(rotated_text, (x, y))


def draw_text_double(surface: pygame.Surface, text: str, x: int, y: int, size: int,
                     x_offset: int, y_offset: int, font1: pygame.font.Font, color1: tuple[int, int, int],
                     font2: pygame.font.Font, color2: tuple[int, int, int],
                     extra_x_offset: list[int] = None) -> None:
    """
    Draws text twice on the given surface (graffiti style),
    fon1 - main text (smaller size), font2 - shadow text

    Parameters:
    - surface: pygame.Surface - the surface on which the text will be drawn.
    - text: str - the text to be drawn.
    - x, y: int - starting coordinates for drawing the text (for first letter).
    - size: int - the size of the gap between characters, match the size of the font.
    - x_offset, y_offset: int - offset shadow by x and y.
    - font1, font2: pygame.font.Font - font objects for the first and second sets of text.
    - color1, color2: tuple[int, int, int] - text colors for the first and second sets.
    - extra_x_offset: list[int] - additional x offset for each character individually.
    """

    extra_x_offset = [0, 0, 0] if extra_x_offset is None else extra_x_offset
    x -= size

    for t in range(len(text)):
        # debug: if the length of the list is less than the text, add 0
        extra_x_offset.append(0)

        # total offset
        x += extra_x_offset[t] + size

        # Draws text from the second set (shadow)
        image_text2 = font2.render(text[t], True, color2)
        surface.blit(image_text2, (x, y))

        # Draws text from the first set (main)
        image_text1 = font1.render(text[t], True, color1)
        surface.blit(image_text1, (x + x_offset, y + y_offset))


# IMAGES settings
class ImageList:
    """ creates a list of images of the same name """
    def __init__(self, img_path, scale=1):
        self.img_path = img_path
        self.img_category_keys = set()
        self.scale = scale

    def create_dict(self, separator: str = '_', print_list=False):
        for file in os.listdir(self.img_path):
            image_name = os.path.splitext(file)[0].rsplit(separator, 1)[0]
            self.img_category_keys.add(image_name)
        img_category = {title: [] for title in self.img_category_keys}

        # Sort the list of files
        files = sorted(os.listdir(self.img_path))

        # Print list for debug
        if print_list:
            print('-' * 60)
            print('\n'.join(file for file in files))
            print('-' * 60)

        # Create image list in dict
        for img_category_key in self.img_category_keys:
            for file in files:
                image = pygame.image.load(os.path.join(self.img_path, file)).convert_alpha()
                image = scale_image(image, self.scale)
                image_category = os.path.splitext(file)[0].rsplit(separator, 1)[0]
                if image_category == img_category_key:
                    img_category[image_category].append(image)

        return img_category

    def get_list(self, category_key: str, separator: str = '_', print_list=False):
        img_category = self.create_dict(separator, print_list)
        return img_category.get(category_key, [])


def scale_image(c_image, scale):
    """ returns a scaled image """
    x = c_image.get_width()
    y = c_image.get_height()
    return pygame.transform.scale(c_image, (x*scale, y*scale))


def scale_size_image(img, x_size, y_size):
    """ returns an image with the given dimensions """
    return pygame.transform.scale(img, (x_size, y_size))


def draw_image(surface, image, x, y, scale=1, center=False):
    """ draws image in the top-left corner or center """
    s_image = scale_image(image, scale)
    if center:
        surface.blit(s_image, (x - s_image.get_width()//2, y-s_image.get_height()//2))
    else:
        surface.blit(s_image, (x, y))


def draw_image_by_path(surface, image_path, x, y, scale=1, center=False):
    """ draws image in the top-left corner or center from the given path """
    c_image = pygame.image.load(image_path)
    s_image = scale_image(c_image, scale)
    if center:
        surface.blit(s_image, (x - s_image.get_width()//2, y-s_image.get_height()//2))
    else:
        surface.blit(s_image, (x, y))


def diagonal_distance(point_1, point_2):
    """ distance between two points """
    dx = (point_1[0] - point_2[0])**2
    dy = (point_1[1] - point_2[1])**2
    return math.sqrt(dx + dy)


def diagonal_distance2(x1, y1, x2, y2):
    """ distance between two points """
    dx = (x2 - x1)**2
    dy = (y2 - y1)**2
    return math.sqrt(dx + dy)


def signum(x):
    """ returns the sign of the expression  """
    if x < 0:
        return -1
    elif x > 0:
        return 1
    else:
        return 0


def diagonal_move_factor(x, y, go_x=True):
    """ returns coefficients for diagonal movement, for x when go_x = True, otherwise for y """
    a = math.sqrt(x ** 2 + y ** 2)
    try:
        b = x / a if go_x is True else y / a
    except ZeroDivisionError:
        return 1
    return b


def calculate_volume(x, x_min=606, x_max=785, volume_min=0, volume_max=100):
    """ Linear interpolation for volume """
    volume = ((x - x_min) / (x_max - x_min)) * (volume_max - volume_min) + volume_min
    volume = round(volume)
    volume = max(min(volume, volume_max), volume_min)
    return volume


def resize_and_offset_rect(old_rect: pygame.rect, params: tuple):
    """ function reduces the old_rect by dx, dy, offsets it and returns a new rect object
        params = (dx, dy, offset_x, offset_y) """
    if len(params) != 4:
        raise ValueError("Tuple params must have exactly 4 elements.")

    dx, dy, offset_x, offset_y = params
    new_rect = pygame.Rect(old_rect.x, old_rect.y, old_rect.width - dx, old_rect.height - dy)
    new_rect.center = (old_rect.centerx + offset_x, old_rect.centery + offset_y)
    return new_rect


def center_coordinates(rect_01: pygame.rect, rect_02: pygame.rect):
    """ returns coordinates (x,y) between two pygame.rect """
    x = (rect_01.centerx + rect_02.centerx) // 2
    y = (rect_01.centery + rect_02.centery) // 2
    return x, y


def random_num(a: int, b: int = WINDOW_WIDTH, to_difference=True):
    """ return random number from A to B-A (or form A to B when to_difference=False) """
    if to_difference:
        number = random.randint(a, b-a) if a < b else a
    else:
        number = random.randint(a, b) if a < b else a
    return number


def format_ratio(a: int, b: int, revers=False):
    """ shows the ratio in percentage form """
    ratio = ((a / b) * 100 if not revers else ((b - a) / b) * 100) if b != 0 else 0
    formatted_ratio = f'{int(ratio)}%' if ratio % 1 == 0 else f'{ratio:.1f}%'
    return formatted_ratio


def format_time(seconds: int):
    """ converts time [sec] to mm:ss format """
    minutes = seconds // 60
    seconds %= 60
    formatted_time = f"{minutes:02d}:{seconds:02d}"
    return formatted_time


def load_sound(name: str, format='mp3'):
    return None if name is None else pygame.mixer.Sound(f'./config/music/{name}.{format}')


def create_font(font: str = './config/fonts/WashYourHand.ttf', size: int = 20, standard: bool = False):
    return pygame.font.SysFont(font, size) if standard else pygame.font.Font(font, size)


def create_text(surface: pygame.surface, text: str, x: int, y: int, size: int, font: str = 'Chiller',
                random_col: bool = False, color: tuple = (255, 255, 255), standard: bool = True):
    if random_col:
        text_color = (random.randint(15, 255), random.randint(25, 255), random.randint(15, 255))
    else:
        text_color = color
    text_font = pygame.font.SysFont(font, size) if standard else pygame.font.Font(font, size)
    text_image = text_font.render(text, True, text_color)
    return surface.blit(text_image, (x, y))


def rename_file(old_name, new_name, file_typ='xlsx', file_path='./config/data/'):
    number = 1
    old_file = f'{file_path}{old_name}.{file_typ}'
    if os.path.exists(old_file):
        while os.path.exists(f'{file_path}{new_name}_{number:02d}.{file_typ}'):
            number += 1
        new_file = f'{file_path}{new_name}_{number:02d}.{file_typ}'
        try:
            os.rename(old_file, new_file)
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.append(["Score", "Date", "Cheese"])
            wb.save(f'{file_path}score.xlsx')
        except FileNotFoundError:
            print(f'File "{old_file}" not exist')


# endregion
