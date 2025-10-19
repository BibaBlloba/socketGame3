from Utilities.Enums.Rotation import Rotation


class Player:
    def __init__(
        self,
        player_id: int,
        name: str,
        x: int = 0,
        y: int = 0,
        skin: str = '@',
        rotation: Rotation = Rotation.UP,
        is_current_player: bool = False,
        health: int = 100,
        level: int = 1,
    ) -> None:
        self.id = player_id
        self.name = name
        self.x = x
        self.y = y
        self.skin = skin
        self.rotation = rotation
        self.is_current_player = is_current_player
        self.health = health
        self.level = level

    def move(self, dx: int, dy: int) -> None:
        """Перемещает игрока на указанное смещение.

        Args:
            dx (int): Смещение по X
            dy (int): Смещение по Y
        """
        self.x += dx
        self.y += dy

    def set_position(self, x: int, y: int) -> None:
        """Устанавливает позицию игрока.

        Args:
            x (int): Новая позиция X
            y (int): Новая позиция Y
        """
        self.x = x
        self.y = y

    def get_position(self) -> tuple:
        """Возвращает текущую позицию игрока.

        Returns:
            tuple: Кортеж (x, y)
        """
        return (self.x, self.y)

    def take_damage(self, damage: int) -> int:
        """Наносит урон игроку.

        Args:
            damage (int): Количество урона

        Returns:
            int: Оставшееся здоровье
        """
        self.health = max(0, self.health - damage)
        return self.health

    def heal(self, amount: int) -> int:
        """Восстанавливает здоровье игроку.

        Args:
            amount (int): Количество здоровья

        Returns:
            int: Текущее здоровье
        """
        self.health = min(self.max_health, self.health + amount)
        return self.health

    def update_from_dict(self, data: dict) -> None:
        """Обновляет состояние игрока из словаря.

        Args:
            data (dict): Данные для обновления
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def distance_to(self, other_x: int, other_y: int) -> float:
        """Вычисляет расстояние до другой точки.

        Args:
            other_x (int): X координата цели
            other_y (int): Y координата цели

        Returns:
            float: Расстояние до цели
        """
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5

    def __str__(self) -> str:
        """Строковое представление игрока.

        Returns:
            str: Строковое представление
        """
        return f"Player({self.id}, '{self.name}', pos=({self.x},{self.y}), HP={self.health})"
