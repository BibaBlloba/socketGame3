import curses
from time import sleep
from typing import Any, Dict, List, Tuple


class CameraWindow:
    def __init__(self, parent_win, x: int, y: int, width: int, height: int):
        """Окно камеры для отрисовки игрового мира.

        Args:
            parent_win: Родительское окно curses
            x (int): Позиция X на родительском окне
            y (int): Позиция Y на родительском окне
            width (int): Ширина окна камеры
            height (int): Высота окна камеры
        """
        self.parent_win = parent_win
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Создаем подокно для камеры
        self.win = parent_win.subwin(height, width, y, x)
        self.win.keypad(True)

        # Позиция камеры в мировых координатах
        self.world_x = 0
        self.world_y = 0

        # Размер видимой области в мировых координатах
        self.viewport_width = 20
        self.viewport_height = 15

    def clear(self):
        """Очищает окно камеры."""
        self.win.clear()

    def refresh(self):
        """Обновляет окно камеры."""
        self.win.refresh()

    def world_to_screen(self, world_x: int, world_y: int) -> Tuple[int, int]:
        """Преобразует мировые координаты в экранные координаты камеры."""
        screen_x = world_x - self.world_x + self.width // 2
        screen_y = world_y - self.world_y + self.height // 2
        return screen_x, screen_y

    def is_visible(self, world_x: int, world_y: int) -> bool:
        """Проверяет, виден ли объект в окне камеры."""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return 0 <= screen_x < self.width and 0 <= screen_y < self.height

    def draw_char(
        self, char: str, world_x: int, world_y: int, attr: int = curses.A_NORMAL
    ):
        """Рисует символ в мировых координатах."""
        if self.is_visible(world_x, world_y):
            screen_x, screen_y = self.world_to_screen(world_x, world_y)
            try:
                self.win.addch(screen_y, screen_x, char, attr)
            except curses.error:
                pass  # Игнорируем ошибки отрисовки на границах

    def draw_border(self):
        """Рисует границу вокруг окна камеры."""
        self.win.border()

    def center_on(self, world_x: int, world_y: int):
        """Центрирует камеру на указанных мировых координатах."""
        self.world_x = world_x
        self.world_y = world_y
