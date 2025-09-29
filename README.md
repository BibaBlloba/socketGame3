План:

- [ ] Написать базовый FastAPI сервер без авторизации для вебсоветов
  - [x] FastAPI сервер
  - [x] Хранение состояния игроков
  - [x] Изменение состояний
  - [x] GameProtocol для запаковки и распаковки данных в байтах
  - [x] GameProtocol на клиенте
  - [ ] Передвежение игрока
  - [ ] Минимальное общение клиента и сервера
- [ ] Сделать главное меню для смены ника и выбора сервера/режима игры
- [ ] Сделать авторизацию
  - [x] на сервере
  - [ ] на клиенте
- [ ] Карта мира
- [ ] Чат

Авторизация ->
получение данных об игроке +
jwt токен для проверки подлинности ->
получение координат, ника, инвенторя

```python
def render(self, stdscr, game_state):
    """Отрисовка игрового состояния в curses"""
    try:
        # Очистка экрана
        stdscr.clear()
        height, width = stdscr.getmaxyx()
        
        # Получаем данные для рендеринга
        player = game_state["player"]
        visible_objects = game_state["visible_objects"]
        camera = game_state["camera"]
        ui = game_state["ui"]
        
        # 1. Отрисовка игровой карты (центрированная на игроке)
        self.render_game_map(stdscr, player, visible_objects, camera, width, height)
        
        # 2. Отрисовка UI поверх игры
        self.render_ui(stdscr, player, ui, width, height)
        
        # 3. Отрисовка HUD (здоровье, уровень и т.д.)
        self.render_hud(stdscr, player, width, height)
        
        # Обновление экрана
        stdscr.refresh()
        
    except curses.error as e:
        # Обработка ошибок curses (например, изменение размера терминала)
        pass

def render_game_map(self, stdscr, player, objects, camera, width, height):
    """Отрисовка игровой карты"""
    map_height = height - 6  # Оставляем место для UI
    map_width = width - 20   # Оставляем место для боковой панели
    
    # Вычисляем смещение камеры (центрируем на игроке)
    offset_x = player["x"] - map_width // 2
    offset_y = player["y"] - map_height // 2
    
    # Отрисовка фона (простая сетка или тайлы)
    for y in range(map_height):
        for x in range(map_width):
            world_x = offset_x + x
            world_y = offset_y + y
            
            # Определяем символ для этой позиции
            char = self.get_tile_char(world_x, world_y)
            if 0 <= y < map_height and 0 <= x < map_width:
                try:
                    stdscr.addch(y, x, char)
                except curses.error:
                    pass
    
    # Отрисовка объектов на карте
    for obj in objects:
        screen_x = obj["x"] - offset_x
        screen_y = obj["y"] - offset_y
        
        # Проверяем, виден ли объект в viewport'е
        if (0 <= screen_x < map_width and 0 <= screen_y < map_height):
            char = self.get_object_char(obj)
            color = self.get_object_color(obj)
            
            try:
                stdscr.addch(screen_y, screen_x, char, color)
                
                # Подписываем имена игроков
                if obj["type"] == "player" and "name" in obj:
                    name = obj["name"][:10]  # Обрезаем длинные имена
                    if screen_x + len(name) < map_width:
                        stdscr.addstr(screen_y + 1, screen_x, name)
            except curses.error:
                pass

def render_ui(self, stdscr, player, ui, width, height):
    """Отрисовка интерфейса пользователя"""
    # Боковая панель с информацией
    sidebar_x = width - 20
    sidebar_width = 20
    
    # Заголовок
    self.draw_box(stdscr, 0, sidebar_x, height, sidebar_width)
    stdscr.addstr(1, sidebar_x + 2, f"Игрок: {player['id'][:8]}")
    stdscr.addstr(2, sidebar_x + 2, f"Уровень: {player['level']}")
    
    # Чат
    chat_y = height - 10
    self.draw_box(stdscr, chat_y, 0, 10, width // 2)
    stdscr.addstr(chat_y + 1, 2, "Чат:")
    
    # Последние сообщения чата
    for i, msg in enumerate(ui["chat_messages"][-8:]):
        if chat_y + 3 + i < height - 1:
            color = self.get_message_color(msg["type"])
            text = msg["text"][:width//2 - 4]
            stdscr.addstr(chat_y + 3 + i, 2, text, color)

def render_hud(self, stdscr, player, width, height):
    """Отрисовка HUD (здоровье, статусы и т.д.)"""
    # Полоска здоровья
    health_y = height - 2
    health_width = 30
    health_percent = player["health"] / player["max_health"]
    filled = int(health_width * health_percent)
    
    health_bar = "[" + "█" * filled + " " * (health_width - filled) + "]"
    stdscr.addstr(health_y, 2, f"HP: {health_bar} {player['health']}/{player['max_health']}")

def get_tile_char(self, x, y):
    """Определяет символ тайла на карте"""
    # Простая логика генерации ландшафта
    if (x + y) % 4 == 0:
        return '.'  # Трава
    elif (x * y) % 7 == 0:
        return '#'  # Камень
    else:
        return ' '  # Земля

def get_object_char(self, obj):
    """Определяет символ для объекта"""
    chars = {
        "player": "@",
        "npc": "N", 
        "item": "*",
        "chest": "□"
    }
    return chars.get(obj["type"], "?")

def get_object_color(self, obj):
    """Определяет цвет для объекта"""
    # Используем пары цветов curses
    colors = {
        "player": curses.color_pair(1),  # Яркий цвет для игроков
        "npc": curses.color_pair(2),     # Другой цвет для NPC
        "item": curses.color_pair(3)     # Цвет для предметов
    }
    return colors.get(obj["type"], curses.color_pair(0))

def get_message_color(self, msg_type):
    """Цвет для сообщений чата"""
    colors = {
        "normal": curses.color_pair(1),
        "system": curses.color_pair(2),
        "warning": curses.color_pair(3)
    }
    return colors.get(msg_type, curses.color_pair(0))

def draw_box(self, stdscr, y, x, height, width):
    """Рисует прямоугольную рамку"""
    try:
        # Углы
        stdscr.addch(y, x, curses.ACS_ULCORNER)
        stdscr.addch(y, x + width - 1, curses.ACS_URCORNER)
        stdscr.addch(y + height - 1, x, curses.ACS_LLCORNER)
        stdscr.addch(y + height - 1, x + width - 1, curses.ACS_LRCORNER)
        
        # Горизонтальные линии
        for i in range(1, width - 1):
            stdscr.addch(y, x + i, curses.ACS_HLINE)
            stdscr.addch(y + height - 1, x + i, curses.ACS_HLINE)
        
        # Вертикальные линии
        for i in range(1, height - 1):
            stdscr.addch(y + i, x, curses.ACS_VLINE)
            stdscr.addch(y + i, x + width - 1, curses.ACS_VLINE)
    except curses.error:
        pass
```
