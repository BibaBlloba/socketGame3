import json
import random

import noise
import numpy as np


class WorldGenerator:
    def __init__(self) -> None:
        # Параметры мира
        self.WORLD_WIDTH = 300
        self.WORLD_HEIGHT = 100
        self.SEED = 69
        self.CHUNK_SIZE = 16

        # Настройки генерации шума
        self.TERRAIN_NOISE = {
            'octaves': 6,
            'persistence': 0.6,
            'lacunarity': 0.5,
            'scale': 10.0,
            'height_multiplier': 50,
            'base_height': 0.3,
        }

        self.CAVE_NOISE = {
            'octaves': 10,
            'persistence': 0.1,
            'lacunarity': 3.0,
            'scale': 10.0,
            'threshold': 0.2,
        }

        # Типы блоков
        self.BLOCKS = {
            'none': {'type': 'none', 'health': 0},
            'grass': {'type': 'grass', 'health': 3},
            'dirt': {'type': 'dirt', 'health': 3},
            'stone': {'type': 'stone', 'health': 4},
            'bedrock': {'type': 'bedrock', 'health': 'inf'},
        }

    def generate_terrain_noise(self, width, height, seed):
        """Генерация карты высот с использованием шума Перлина"""
        terrain = np.zeros(width)

        for x in range(width):
            nx = x / width - 0.5
            value = noise.pnoise1(
                nx * self.TERRAIN_NOISE['scale'],
                octaves=self.TERRAIN_NOISE['octaves'],
                persistence=self.TERRAIN_NOISE['persistence'],
                lacunarity=self.TERRAIN_NOISE['lacunarity'],
                repeat=1024,
                base=seed,
            )
            terrain[x] = int(
                value * self.TERRAIN_NOISE['height_multiplier']
                + height * self.TERRAIN_NOISE['base_height']
            )

        return terrain

    def generate_cave_noise(self, width, height, seed):
        """Генерация карты пещер с использованием 2D шума Перлина"""
        cave_map = np.zeros((height, width))

        for y in range(height):
            for x in range(width):
                nx = x / width - 0.5
                ny = y / height - 0.5
                value = noise.pnoise2(
                    nx * self.CAVE_NOISE['scale'],
                    ny * self.CAVE_NOISE['scale'],
                    octaves=self.CAVE_NOISE['octaves'],
                    persistence=self.CAVE_NOISE['persistence'],
                    lacunarity=self.CAVE_NOISE['lacunarity'],
                    repeatx=1024,
                    repeaty=1024,
                    base=seed,
                )
                cave_map[y, x] = value

        return cave_map

    def generate_world(self, width, height, seed):
        """Генерация всего мира"""
        # Генерируем карту высот
        surface_levels = self.generate_terrain_noise(width, height, seed)

        # Генерируем карту пещер
        cave_map = self.generate_cave_noise(width, height, seed)

        # Создаем массив блоков
        blocks = np.empty((height, width), dtype=object)
        blocks.fill(None)

        for x in range(width):
            surface_y = int(surface_levels[x])

            for y in range(height):
                # Если мы ниже поверхности
                if y > surface_y:
                    depth = y - surface_y

                    # Определяем, находится ли этот блок в пещере
                    is_cave = cave_map[y, x] > self.CAVE_NOISE['threshold']

                    # Если это пещера, оставляем воздух
                    if (
                        is_cave and depth > 5
                    ):  # Не создаем пещеры слишком близко к поверхности
                        continue

                    # Верхний слой - трава
                    if depth == 1:
                        blocks[y, x] = self.BLOCKS['grass']
                    # Несколько слоев земли
                    elif 1 < depth <= 5:
                        # Иногда добавляем камни в землю
                        if random.random() < 0.2:
                            blocks[y, x] = self.BLOCKS['stone']
                        else:
                            blocks[y, x] = self.BLOCKS['dirt']
                    # Каменные слои
                    elif 5 < depth < height - 5:
                        # Добавляем случайные включения земли
                        if random.random() < 0.1:
                            blocks[y, x] = self.BLOCKS['dirt']
                        else:
                            blocks[y, x] = self.BLOCKS['stone']
                    # Коренная порода (нижние 5 слоев)
                    else:
                        blocks[y, x] = self.BLOCKS['bedrock']
                # Если это поверхность
                elif y == surface_y:
                    blocks[y, x] = self.BLOCKS['grass']

        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'w') as f:
            json.dump(blocks.tolist(), f)

    def get_chunks_in_radius(
        self, world: list, chunkX: int, chunkY: int, radius: int = 3
    ) -> list[dict]:
        chunks = []
        world_height = len(world)
        if world_height == 0:
            return chunks

        world_width = len(world[0])
        chunk_size = 16  # Размер чанка 16x16

        # Определяем границы в чанках (не в тайлах)
        min_chunk_x = max(0, chunkX - radius)
        max_chunk_x = min((world_width - 1) // chunk_size, chunkX + radius)

        min_chunk_y = max(0, chunkY - radius)
        max_chunk_y = min((world_height - 1) // chunk_size, chunkY + radius)

        # Проходим по всем чанкам в радиусе
        for current_chunk_y in range(min_chunk_y, max_chunk_y + 1):
            for current_chunk_x in range(min_chunk_x, max_chunk_x + 1):
                # Границы тайлов текущего чанка
                start_x = current_chunk_x * chunk_size
                end_x = min((current_chunk_x + 1) * chunk_size, world_width)

                start_y = current_chunk_y * chunk_size
                end_y = min((current_chunk_y + 1) * chunk_size, world_height)

                # Извлекаем тайлы чанка
                chunk_data = []
                for y in range(start_y, end_y):
                    row = []
                    for x in range(start_x, end_x):
                        row.append(world[y][x])
                    chunk_data.append(row)

                # Добавляем чанк с координатами
                chunks.append(
                    {'x': current_chunk_x, 'y': current_chunk_y, 'data': chunk_data}
                )

        return chunks

    def get_chunk(self, chunkX, chunkY) -> list[dict]:
        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'r') as file:
            content = file.read().strip()
            world = json.loads(content)

            start_x = chunkX * self.CHUNK_SIZE
            start_y = chunkY * self.CHUNK_SIZE

            if (
                start_x >= len(world[0])
                or start_y >= len(world)
                or start_x < 0
                or start_y < 0
            ):
                return None

            chunk = []
            for y in range(start_y, start_y + self.CHUNK_SIZE):
                if y >= len(world):
                    break
                row = []
                for x in range(start_x, start_x + self.CHUNK_SIZE):
                    if x >= len(world[y]):
                        break
                    row.append(world[y][x])
                chunk.append(row)

        return {
            'x': chunkX,
            'y': chunkY,
            'chunk': chunk,
        }


import json

import matplotlib

matplotlib.use('Qt5Agg')  # Устанавливаем бэкенд Agg перед импортом pyplot

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np


def visualize_world_matplotlib(world_generator):
    """Visualize the generated world using matplotlib"""
    try:
        # Load the generated world
        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'r') as file:
            content = file.read().strip()
            world_data = json.loads(content)

        # Convert world data to color matrix
        height = len(world_data)
        width = len(world_data[0]) if height > 0 else 0

        color_map = np.zeros((height, width, 3))  # RGB array

        # Define block colors :cite[2]:cite[7]
        block_colors = {
            'none': [0.2, 0.2, 0.8],  # Dark blue for air/none
            'grass': [0.2, 0.8, 0.2],  # Green for grass
            'dirt': [0.6, 0.4, 0.2],  # Brown for dirt
            'stone': [0.5, 0.5, 0.5],  # Gray for stone
            'bedrock': [0.1, 0.1, 0.1],  # Dark gray for bedrock
        }

        # Fill color matrix
        for y in range(height):
            for x in range(width):
                block = world_data[y][x]
                if block and 'type' in block:
                    block_type = block['type']
                    color_map[y, x] = block_colors.get(block_type, [0, 0, 0])
                else:
                    color_map[y, x] = block_colors['none']

        # Create visualization :cite[5]:cite[7]
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Main world view
        ax1.imshow(color_map, aspect='auto')
        ax1.set_title('Generated World - Color View')
        ax1.set_xlabel('X Coordinate')
        ax1.set_ylabel('Y Coordinate')
        ax1.grid(True, alpha=0.3)

        # Height map view
        surface_levels = []
        for x in range(width):
            for y in range(height):
                block = world_data[y][x]
                if block and block.get('type') == 'grass':
                    surface_levels.append(height - y)
                    break
            else:
                surface_levels.append(0)

        ax2.plot(range(width), surface_levels, 'g-', linewidth=2)
        ax2.fill_between(range(width), surface_levels, alpha=0.3, color='green')
        ax2.set_title('Surface Height Profile')
        ax2.set_xlabel('X Coordinate')
        ax2.set_ylabel('Height from Bottom')
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0, height)

        plt.tight_layout()
        plt.show()

        print(f'World visualized: {width}x{height} blocks')

    except Exception as e:
        print(f'Error in matplotlib visualization: {e}')


def visualize_chunks_matplotlib(
    world_generator, center_chunk_x=5, center_chunk_y=3, radius=2
):
    """Visualize chunks around a specific chunk coordinate"""
    try:
        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'r') as file:
            content = file.read().strip()
            world_data = json.loads(content)

        chunks = world_generator.get_chunks_in_radius(
            world_data, center_chunk_x, center_chunk_y, radius
        )

        if not chunks:
            print('No chunks found in the specified radius')
            return

        # Create figure for chunks
        fig, axes = plt.subplots(len(chunks), 1, figsize=(12, 3 * len(chunks)))
        if len(chunks) == 1:
            axes = [axes]

        block_colors = {
            'none': [0.2, 0.2, 0.8],
            'grass': [0.2, 0.8, 0.2],
            'dirt': [0.6, 0.4, 0.2],
            'stone': [0.5, 0.5, 0.5],
            'bedrock': [0.1, 0.1, 0.1],
        }

        for idx, chunk in enumerate(chunks):
            chunk_data = chunk['data']
            chunk_height = len(chunk_data)
            chunk_width = len(chunk_data[0]) if chunk_height > 0 else 0

            color_chunk = np.zeros((chunk_height, chunk_width, 3))

            for y in range(chunk_height):
                for x in range(chunk_width):
                    block = chunk_data[y][x]
                    if block and 'type' in block:
                        block_type = block['type']
                        color_chunk[y, x] = block_colors.get(block_type, [0, 0, 0])
                    else:
                        color_chunk[y, x] = block_colors['none']

            axes[idx].imshow(color_chunk, aspect='auto')
            axes[idx].set_title(
                f'Chunk ({chunk["x"]}, {chunk["y"]}) - {chunk_width}x{chunk_height}'
            )
            axes[idx].set_xlabel('X in Chunk')
            axes[idx].set_ylabel('Y in Chunk')

        plt.tight_layout()
        plt.show()

    except Exception as e:
        print(f'Error in chunk visualization: {e}')


def visualize_world_terminal(
    world_generator, start_x=0, start_y=0, width=80, height=20
):
    """Visualize a section of the world in terminal using ASCII art"""
    try:
        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'r') as file:
            content = file.read().strip()
            world_data = json.loads(content)

        world_height = len(world_data)
        world_width = len(world_data[0]) if world_height > 0 else 0

        # Adjust viewport to fit within world bounds
        end_x = min(start_x + width, world_width)
        end_y = min(start_y + height, world_height)
        actual_width = end_x - start_x
        actual_height = end_y - start_y

        # Define ASCII characters for blocks :cite[9]
        block_chars = {
            'none': ' ',  # Air
            'grass': '█',  # Grass (full block)
            'dirt': '▒',  # Dirt (medium shade)
            'stone': '░',  # Stone (light shade)
            'bedrock': '▓',  # Bedrock (dark shade)
        }

        print(f'World View: ({start_x}, {start_y}) to ({end_x}, {end_y})')
        print(f'Dimensions: {actual_width}x{actual_height}')
        print('Legend: █=Grass ▒=Dirt ░=Stone ▓=Bedrock')
        print('-' * (actual_width + 2))

        # Print world section
        for y in range(start_y, end_y):
            line = '|'
            for x in range(start_x, end_x):
                block = world_data[y][x]
                if block and 'type' in block:
                    block_type = block['type']
                    line += block_chars.get(block_type, '?')
                else:
                    line += block_chars['none']
            line += '|'
            print(line)

        print('-' * (actual_width + 2))

    except Exception as e:
        print(f'Error in terminal visualization: {e}')


def visualize_world_stats(world_generator):
    """Display statistics about the generated world"""
    try:
        with open('/home/akeka/proj/terrariaWeb/back/world.json', 'r') as file:
            content = file.read().strip()
            world_data = json.loads(content)

        world_height = len(world_data)
        world_width = len(world_data[0]) if world_height > 0 else 0

        # Count block types
        block_counts = {'none': 0, 'grass': 0, 'dirt': 0, 'stone': 0, 'bedrock': 0}

        for y in range(world_height):
            for x in range(world_width):
                block = world_data[y][x]
                if block and 'type' in block:
                    block_type = block['type']
                    block_counts[block_type] = block_counts.get(block_type, 0) + 1
                else:
                    block_counts['none'] += 1

        total_blocks = world_width * world_height

        print('\n' + '=' * 50)
        print('WORLD STATISTICS')
        print('=' * 50)
        print(f'World Size: {world_width} x {world_height} = {total_blocks} blocks')
        print(f'Chunk Size: {world_generator.CHUNK_SIZE}')
        print(
            f'Total Chunks: {(world_width // world_generator.CHUNK_SIZE)} x {(world_height // world_generator.CHUNK_SIZE)}'
        )
        print('\nBlock Distribution:')
        for block_type, count in block_counts.items():
            percentage = (count / total_blocks) * 100
            print(f'  {block_type:8}: {count:6} blocks ({percentage:5.1f}%)')

        # Calculate surface information
        surface_blocks = 0
        for x in range(world_width):
            for y in range(world_height):
                block = world_data[y][x]
                if block and block.get('type') == 'grass':
                    surface_blocks += 1
                    break

        print(f'\nSurface Length: {surface_blocks} blocks')
        print('=' * 50)

    except Exception as e:
        print(f'Error generating world stats: {e}')


# Test the world generation and visualization
if __name__ == '__main__':
    # Create world generator instance
    generator = WorldGenerator()

    # Generate the world (uncomment if you want to regenerate)
    # generator.generate_world(generator.WORLD_WIDTH, generator.WORLD_HEIGHT, generator.SEED)

    print('=== TERMINAL VISUALIZATION ===')
    # Show different sections of the world in terminal
    visualize_world_terminal(generator, 0, 0, 80, 20)  # Top-left section
    visualize_world_terminal(generator, 100, 20, 80, 20)  # Middle section
    visualize_world_terminal(generator, 200, 40, 80, 20)  # Right section

    print('\n=== WORLD STATISTICS ===')
    visualize_world_stats(generator)

    print('\n=== CHUNK INFORMATION ===')
    # Test chunk retrieval
    test_chunk = generator.get_chunk(2, 1)
    if test_chunk:
        print(f'Retrieved chunk at ({test_chunk["x"]}, {test_chunk["y"]})')
        print(f'Chunk size: {len(test_chunk["chunk"])}x{len(test_chunk["chunk"][0])}')

    print('\n=== MATPLOTLIB VISUALIZATION ===')
    print('Opening matplotlib visualizations...')

    # Show full world visualization
    visualize_world_matplotlib(generator)

    # Show chunk-based visualization
    visualize_chunks_matplotlib(generator, center_chunk_x=3, center_chunk_y=2, radius=2)

    print('All visualizations completed!')
