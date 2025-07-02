from abc import ABC, abstractmethod
import pygame
import math
import random
from .utils import Vector2D, Direction, AStar
from .sprite_manager import sprite_manager

class GameObject(ABC):
    def __init__(self, x, y, color, size):
        self._position = Vector2D(x, y)
        self._color = color
        self._size = size
        self._animation_frame = 0

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, new_position):
        if isinstance(new_position, tuple):
            self._position = Vector2D(new_position[0], new_position[1])
        elif isinstance(new_position, Vector2D):
            self._position = new_position
        else:
            raise TypeError("A posição deve ser uma tupla ou um Vector2D")

    @property
    def color(self):
        return self._color

    @property
    def size(self):
        return self._size

    @abstractmethod
    def draw(self, screen):
        pass

    @abstractmethod
    def update(self, delta_time):
        pass

    def get_rect(self):
        sprite_size = sprite_manager.base_sprite_size
        return pygame.Rect(
            self._position.x - sprite_size // 2,
            self._position.y - sprite_size // 2,
            sprite_size,
            sprite_size
        )

class MovableObject(GameObject):
    def __init__(self, x, y, color, size, speed, direction=Direction.NONE):
        super().__init__(x, y, color, size)
        self._speed = speed
        self._direction = direction
        self._next_direction = direction

    @property
    def speed(self):
        return self._speed

    @speed.setter
    def speed(self, new_speed):
        self._speed = new_speed

    @property
    def direction(self):
        return self._direction

    @direction.setter
    def direction(self, new_direction):
        if isinstance(new_direction, Direction):
            self._next_direction = new_direction
        elif isinstance(new_direction, tuple) and len(new_direction) == 2:
            for d in Direction:
                if d.value == new_direction:
                    self._next_direction = d
                    return
            raise ValueError(f"Tupla de direção inválida: {new_direction}")
        else:
            raise TypeError("A direção deve ser um enum Direction ou uma tupla (x, y)")

    def can_move(self, direction, game_map, entity_type=None):
        if direction == Direction.NONE:
            return False
        
        next_pos = Vector2D(
            self._position.x + direction.value[0] * self._speed,
            self._position.y + direction.value[1] * self._speed
        )
        
        if entity_type is None:
            entity_type = "default"
        
        return game_map.is_valid_position(next_pos, sprite_manager.base_sprite_size, entity_type)

    def move(self, direction=None):
        if direction is None:
            direction = self._direction
        
        if direction != Direction.NONE:
            self._position += Vector2D(
                direction.value[0] * self._speed,
                direction.value[1] * self._speed
            )

class Player(MovableObject):
    def __init__(self, x, y, color, size, speed, lives, score=0):
        super().__init__(x, y, color, size, speed)
        self._lives = lives
        self._score = score
        self._power_up_active = False
        self._power_up_timer = 0
        self._power_up_duration = 5000

    def can_move(self, direction, game_map, entity_type=None):
        return super().can_move(direction, game_map, "player")

    @property
    def lives(self):
        return self._lives

    @property
    def score(self):
        return self._score

    @property
    def power_up_active(self):
        return self._power_up_active

    @power_up_active.setter
    def power_up_active(self, status):
        self._power_up_active = status
        if status:
            self._power_up_timer = self._power_up_duration

    def eat_pellet(self, pellet_value):
        self._score += pellet_value

    def activate_power_up(self):
        self._power_up_active = True
        self._power_up_timer = self._power_up_duration

    def lose_life(self):
        self._lives -= 1
        if self._lives < 0:
            self._lives = 0

    def draw(self, screen, scale_factor=1.0, offset_x=0, offset_y=0):
        sprite = sprite_manager.get_pacman_sprite(self._direction, self._animation_frame)
        
        sprite_size = sprite_manager.sprite_size
        x = int((self._position.x - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_x
        y = int((self._position.y - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_y
        
        if self._power_up_active:
            glow_size = sprite_size + int(4 * scale_factor)
            glow_surface = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
            glow_color = (255, 255, 100, 100) if (self._animation_frame // 5) % 2 else (255, 255, 0, 150)
            glow_radius = sprite_size//2 + int(2 * scale_factor)
            pygame.draw.circle(glow_surface, glow_color, (glow_size//2, glow_size//2), glow_radius)
            screen.blit(glow_surface, (x - int(2 * scale_factor), y - int(2 * scale_factor)))
        
        screen.blit(sprite, (x, y))

    def update(self, delta_time, game_map):
        if self._power_up_active:
            self._power_up_timer -= delta_time * 1000
            if self._power_up_timer <= 0:
                self._power_up_active = False
                self._power_up_timer = 0

        if self._next_direction != self._direction:
            if self.can_move(self._next_direction, game_map):
                self._direction = self._next_direction
            else:
                if not self.can_move(self._direction, game_map):
                    self._direction = Direction.NONE

        if self.can_move(self._direction, game_map):
            self.move()
        else:
            if self._next_direction != self._direction and self.can_move(self._next_direction, game_map):
                self._direction = self._next_direction
                self.move()
            else:
                self._direction = Direction.NONE

        self._animation_frame += 1

class Ghost(MovableObject):
    def __init__(self, x, y, color, size, speed, initial_position, ghost_type="red"):
        super().__init__(x, y, color, size, speed)
        self._state = "normal"
        self._initial_position = Vector2D(initial_position.x if isinstance(initial_position, Vector2D) else initial_position[0],
                                        initial_position.y if isinstance(initial_position, Vector2D) else initial_position[1])
        self._ghost_type = ghost_type
        self._vulnerable_timer = 0
        self._target_position = Vector2D(0, 0)
        self._mode_timer = 0
        self._current_mode = "patrol"
        self._path_finding_timer = 0
        self._original_color = color
        self._last_direction = Direction.NONE
        self._personality_timer = 0
        
        # A* pathfinding
        self._current_path = []
        self._path_index = 0
        self._recalculate_path_timer = 0
        self._use_astar = True
        self._astar_frequency = 2000
        self._last_target = None
        self._smooth_movement = True
        
        # Sistema de patrulhamento
        self._patrol_route = self._get_patrol_route()
        self._patrol_index = 0
        self._patrol_timer = 0
        
        # Sistema de dificuldade progressiva
        self._base_speed = speed
        self._difficulty_multiplier = 1.0
        
        # Sistema de delay após ser comido
        self._is_in_spawn_delay = False
        self._spawn_delay_timer = 0
        self._spawn_delay_duration = 5000

    def can_move(self, direction, game_map, entity_type=None):
        return super().can_move(direction, game_map, "ghost")

    def set_difficulty(self, difficulty_level):
        """Define dificuldade do fantasma baseado no nível do mapa (0-200)"""
        difficulty_factor = min(difficulty_level / 100.0, 2.0)
        self._difficulty_multiplier = 1.0 + difficulty_factor
        self._speed = self._base_speed
        
        # Ajusta frequência A* para ser mais agressivo baseado na dificuldade
        timing_factor = 1.0 - (difficulty_factor * 0.4)
        self._astar_frequency = max(int(2000 * timing_factor), 200)

    def update_difficulty(self, pellets_eaten_percentage):
        """Método legado - mantido para compatibilidade"""
        pass

    def get_difficulty_adjusted_vulnerable_duration(self, base_duration=8000):
        reduction_factor = 1.0 - (self._difficulty_multiplier - 1.0) * 0.85
        adjusted_duration = int(base_duration * reduction_factor)
        return max(adjusted_duration, 1000)

    def get_difficulty_adjusted_mode_timing(self):
        """Retorna timings de modo ajustados pela dificuldade"""
        base_patrol = 10000
        base_chase = 15000
        
        difficulty_factor = self._difficulty_multiplier - 1.0
        
        patrol_duration = int(base_patrol * (1.0 - difficulty_factor * 0.45))
        chase_duration = int(base_chase * (1.0 + difficulty_factor * 0.8))
        
        patrol_duration = max(patrol_duration, 2000)
        chase_duration = min(chase_duration, 40000)
        
        return patrol_duration, chase_duration

    def _get_patrol_route(self):
        """Define rotas de patrulha para cada tipo de fantasma"""
        if self._ghost_type == "red":
            return [
                Vector2D(280, 100),
                Vector2D(420, 130),
                Vector2D(480, 180),
                Vector2D(400, 220),
                Vector2D(280, 200),
                Vector2D(160, 220),
                Vector2D(80, 180),
                Vector2D(140, 130),
            ]
        elif self._ghost_type == "pink":
            return [
                Vector2D(180, 140),
                Vector2D(240, 120),
                Vector2D(320, 140),
                Vector2D(380, 180),
                Vector2D(320, 220),
                Vector2D(240, 240),
                Vector2D(180, 220),
                Vector2D(140, 180),
            ]
        elif self._ghost_type == "cyan":
            return [
                Vector2D(300, 260),
                Vector2D(450, 260),
                Vector2D(480, 300),
                Vector2D(480, 340),
                Vector2D(400, 350),
                Vector2D(280, 330),
                Vector2D(150, 320),
                Vector2D(120, 280),
            ]
        else:  # orange
            return [
                Vector2D(140, 160),
                Vector2D(220, 140),
                Vector2D(300, 180),
                Vector2D(380, 160),
                Vector2D(420, 220),
                Vector2D(340, 260),
                Vector2D(240, 240),
                Vector2D(160, 200),
            ]

    def get_current_patrol_target(self):
        if not self._patrol_route:
            return self._initial_position.copy()
        
        return self._patrol_route[self._patrol_index % len(self._patrol_route)]

    def advance_patrol_waypoint(self):
        """Avança para o próximo waypoint da patrulha"""
        if not self._patrol_route:
            return False
        
        current_target = self.get_current_patrol_target()
        distance = self._position.distance_to(current_target)
        
        tolerance = {
            "red": 28,
            "pink": 35,
            "cyan": 30,
            "orange": 40
        }.get(self._ghost_type, 32)
        
        if distance < tolerance:
            self._patrol_index = (self._patrol_index + 1) % len(self._patrol_route)
            return True
        
        return False

    def configure_astar(self, use_astar=True, frequency=1000):
        self._use_astar = use_astar
        self._astar_frequency = frequency
        if not use_astar:
            self._current_path = []
            self._path_index = 0

    def get_astar_status(self):
        return {
            "enabled": self._use_astar,
            "path_length": len(self._current_path),
            "path_index": self._path_index,
            "frequency": self._astar_frequency,
            "ghost_type": self._ghost_type,
            "has_path": len(self._current_path) > 0,
            "difficulty_multiplier": self._difficulty_multiplier,
            "speed": self._speed
        }

    def get_patrol_status(self):
        return {
            "mode": self._current_mode,
            "route_length": len(self._patrol_route),
            "current_waypoint": self._patrol_index,
            "target_position": self.get_current_patrol_target(),
            "ghost_type": self._ghost_type,
            "distance_to_target": self._position.distance_to(self.get_current_patrol_target()) if self._patrol_route else 0
        }

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state

    @property
    def is_in_spawn_delay(self):
        return self._is_in_spawn_delay

    @property
    def spawn_delay_remaining(self):
        return max(0, self._spawn_delay_timer / 1000.0)

    def set_vulnerable(self, duration=8000):
        self._state = "vulnerable"
        adjusted_duration = self.get_difficulty_adjusted_vulnerable_duration(duration)
        self._vulnerable_timer = adjusted_duration
        self._speed = max(1, self._speed - 1)

    def get_target_position(self, player_position, player_direction=None, other_ghosts=None):
        """Calcula posição alvo baseada no tipo e modo do fantasma"""
        if self._current_mode == "patrol":
            return self.get_current_patrol_target()
        
        elif self._current_mode == "chase":
            if self._ghost_type == "red":
                # Persegue diretamente (Blinky)
                return player_position.copy()
                
            elif self._ghost_type == "pink":
                # Mira 4 células à frente (Pinky)
                if player_direction:
                    cell_size = 16
                    offset_x = player_direction.value[0] * cell_size * 4
                    offset_y = player_direction.value[1] * cell_size * 4
                    target = Vector2D(
                        player_position.x + offset_x,
                        player_position.y + offset_y
                    )
                    return target
                else:
                    return player_position.copy()
                
            elif self._ghost_type == "cyan":
                # Comportamento complexo (Inky)
                if other_ghosts:
                    red_ghost = next((g for g in other_ghosts if g._ghost_type == "red"), None)
                    if red_ghost:
                        if player_direction:
                            cell_size = 16
                            offset_x = player_direction.value[0] * cell_size * 2
                            offset_y = player_direction.value[1] * cell_size * 2
                            player_ahead = Vector2D(
                                player_position.x + offset_x,
                                player_position.y + offset_y
                            )
                        else:
                            player_ahead = player_position.copy()
                        
                        mid_point = Vector2D(
                            (player_ahead.x + red_ghost.position.x) / 2,
                            (player_ahead.y + red_ghost.position.y) / 2
                        )
                        return mid_point
                return player_position.copy()
                
            else:  # orange (Clyde)
                # Alterna entre perseguir e fugir
                distance = self._position.distance_to(player_position)
                if distance > 80:
                    return player_position.copy()
                else:
                    return Vector2D(50, 450)

        return self._initial_position.copy()

    def choose_direction(self, game_map, target_position):
        possible_directions = []
        
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if self.can_move(direction, game_map):
                test_pos = Vector2D(
                    self._position.x + direction.value[0] * self._speed,
                    self._position.y + direction.value[1] * self._speed
                )
                distance = test_pos.distance_to(target_position)
                possible_directions.append((direction, distance))
        
        if not possible_directions:
            return Direction.NONE
        
        if self._state == "vulnerable":
            return max(possible_directions, key=lambda x: x[1])[0]
        else:
            return min(possible_directions, key=lambda x: x[1])[0]

    def choose_direction_advanced(self, game_map, target_position):
        """Escolhe direção com lógica avançada e orgânica"""
        possible_directions = []
        
        for direction in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            if self.can_move(direction, game_map):
                test_pos = Vector2D(
                    self._position.x + direction.value[0] * self._speed,
                    self._position.y + direction.value[1] * self._speed
                )
                distance = test_pos.manhattan_distance_to(target_position)
                possible_directions.append((direction, distance))
        
        if not possible_directions:
            return Direction.NONE
        
        # Preferência por continuar na direção atual (movimento suave)
        if self._smooth_movement and self._direction != Direction.NONE:
            for i, (direction, distance) in enumerate(possible_directions):
                if direction == self._direction:
                    possible_directions[i] = (direction, distance * 0.9)
                    break
        
        if self._state == "vulnerable":
            return max(possible_directions, key=lambda x: x[1])[0]
        
        # Comportamentos específicos por tipo
        if self._ghost_type == "red":
            if random.random() < 0.05:
                return random.choice(possible_directions[:2])[0]
            return min(possible_directions, key=lambda x: x[1])[0]
            
        elif self._ghost_type == "pink":
            if random.random() < 0.2:
                return random.choice(possible_directions)[0]
            elif random.random() < 0.3 and len(possible_directions) > 1:
                sorted_dirs = sorted(possible_directions, key=lambda x: x[1])
                return sorted_dirs[1][0]
            else:
                return min(possible_directions, key=lambda x: x[1])[0]
                
        elif self._ghost_type == "cyan":
            if self._direction != Direction.NONE:
                opposite_direction = Direction((-self._direction.value[0], -self._direction.value[1]))
                filtered_directions = [d for d in possible_directions if d[0] != opposite_direction]
                if filtered_directions and random.random() < 0.8:
                    possible_directions = filtered_directions
            
            if random.random() < 0.15:
                return max(possible_directions[:3], key=lambda x: x[1])[0]
            return min(possible_directions, key=lambda x: x[1])[0]
            
        else:  # orange
            rand = random.random()
            if rand < 0.25:
                return random.choice(possible_directions)[0]
            elif rand < 0.4:
                return max(possible_directions, key=lambda x: x[1])[0]
            elif rand < 0.6 and len(possible_directions) > 2:
                sorted_dirs = sorted(possible_directions, key=lambda x: x[1])
                return sorted_dirs[len(sorted_dirs)//2][0]
            else:
                return min(possible_directions, key=lambda x: x[1])[0]

    def update_mode(self, delta_time):
        """Alterna entre modos patrol/chase com timing ajustado pela dificuldade"""
        self._mode_timer += delta_time * 1000
        
        patrol_duration, chase_duration = self.get_difficulty_adjusted_mode_timing()
        
        if self._current_mode == "patrol":
            if self._mode_timer > patrol_duration:
                self._current_mode = "chase"
                self._mode_timer = 0
        else:  # chase
            if self._mode_timer > chase_duration:
                self._current_mode = "patrol"
                self._mode_timer = 0

    def reset_position(self):
        self._position = self._initial_position.copy()
        self._state = "normal"
        self._speed = self._base_speed
        self._vulnerable_timer = 0
        self._current_mode = "patrol"
        self._mode_timer = 0
        self._current_path = []
        self._path_index = 0
        self._recalculate_path_timer = 0
        self._last_target = None
        self._patrol_index = 0
        self._patrol_timer = 0
        self._is_in_spawn_delay = False
        self._spawn_delay_timer = 0

    def set_eaten_with_delay(self):
        """Coloca fantasma no spawn com delay de 5 segundos"""
        self._position = self._initial_position.copy()
        self._state = "normal"
        self._speed = self._base_speed
        self._vulnerable_timer = 0
        self._current_mode = "patrol"
        self._mode_timer = 0
        self._current_path = []
        self._path_index = 0
        self._recalculate_path_timer = 0
        self._last_target = None
        self._patrol_index = 0
        self._patrol_timer = 0
        self._is_in_spawn_delay = True
        self._spawn_delay_timer = self._spawn_delay_duration
        
        print(f"Fantasma {self._ghost_type} comido! Aguardando 5s no spawn...")

    def reset_difficulty(self):
        self._difficulty_multiplier = 1.0
        self._speed = self._base_speed
        self._astar_frequency = 2000

    def calculate_direction_to_waypoint(self, waypoint):
        diff_x = waypoint.x - self._position.x
        diff_y = waypoint.y - self._position.y
        
        if abs(diff_x) > abs(diff_y):
            if diff_x > 0:
                return Direction.RIGHT
            else:
                return Direction.LEFT
        else:
            if diff_y > 0:
                return Direction.DOWN
            else:
                return Direction.UP

    def should_use_astar(self, target_position):
        """Determina se deve usar A* baseado na personalidade e dificuldade"""
        difficulty_bonus = (self._difficulty_multiplier - 1.0) * 0.6
        
        if self._ghost_type == "red":
            base_chance = 0.9
            return random.random() < min(base_chance + difficulty_bonus, 1.0)
        elif self._ghost_type == "pink":
            base_chance = 0.6
            return random.random() < min(base_chance + difficulty_bonus, 0.95)
        elif self._ghost_type == "cyan":
            base_chance = 0.85
            return random.random() < min(base_chance + difficulty_bonus, 1.0)
        else:  # orange
            distance = self._position.distance_to(target_position)
            if distance > 150:
                base_chance = 0.8
                return random.random() < min(base_chance + difficulty_bonus, 1.0)
            elif distance > 80:
                base_chance = 0.5
                return random.random() < min(base_chance + difficulty_bonus, 0.95)
            else:
                base_chance = 0.2
                return random.random() < min(base_chance + difficulty_bonus, 0.8)

    def astar_pathfinding(self, game_map, target_position):
        """Usa A* para encontrar caminho até o alvo"""
        should_recalculate = (
            len(self._current_path) == 0 or
            self._path_index >= len(self._current_path) - 1 or
            self._recalculate_path_timer > self._astar_frequency or
            (self._last_target and self._last_target.distance_to(target_position) > 32)
        )
        
        if should_recalculate:
            self._current_path = AStar.find_path(
                self._position, 
                target_position, 
                game_map, 
                "manhattan"
            )
            self._path_index = 0
            self._recalculate_path_timer = 0
            self._last_target = target_position.copy()
        
        if self._current_path and self._path_index < len(self._current_path) - 1:
            next_waypoint = self._current_path[self._path_index + 1]
            
            if self._position.distance_to(next_waypoint) < 12:
                self._path_index += 1
                if self._path_index < len(self._current_path) - 1:
                    next_waypoint = self._current_path[self._path_index + 1]
                else:
                    return Direction.NONE
            
            direction = self.calculate_direction_to_waypoint(next_waypoint)
            
            if self.can_move(direction, game_map):
                return direction
        
        return self.choose_direction_advanced(game_map, target_position)

    def draw(self, screen, scale_factor=1.0, offset_x=0, offset_y=0):
        sprite = sprite_manager.get_ghost_sprite(
            self._ghost_type, 
            self._direction, 
            self._animation_frame, 
            self._state
        )
        
        sprite_size = sprite_manager.sprite_size
        x = int((self._position.x - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_x
        y = int((self._position.y - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_y
        
        screen.blit(sprite, (x, y))
        
        if self._is_in_spawn_delay:
            overlay = pygame.Surface((sprite_size, sprite_size), pygame.SRCALPHA)
            alpha = 80 + int(40 * abs(math.sin(pygame.time.get_ticks() * 0.01)))
            overlay.fill((255, 255, 255, alpha))
            screen.blit(overlay, (x, y))

    def update(self, delta_time, player_position=None, player_direction=None, game_map=None, other_ghosts=None):
        # Sistema de delay no spawn
        if self._is_in_spawn_delay:
            self._spawn_delay_timer -= delta_time * 1000
            if self._spawn_delay_timer <= 0:
                self._is_in_spawn_delay = False
                self._spawn_delay_timer = 0
                print(f"Fantasma {self._ghost_type} liberado do spawn!")
            else:
                self._animation_frame += 1
                return

        if self._state == "vulnerable":
            self._vulnerable_timer -= delta_time * 1000
            if self._vulnerable_timer <= 0:
                self._state = "normal"
                self._speed = 1.5

        self.update_mode(delta_time)

        if player_position and game_map:
            if self._current_mode == "patrol":
                self._patrol_timer += delta_time * 1000
                if self._patrol_timer > 200:
                    self.advance_patrol_waypoint()
                    self._patrol_timer = 0
            
            target = self.get_target_position(player_position, player_direction, other_ghosts)
            
            self._path_finding_timer += delta_time * 1000
            self._recalculate_path_timer += delta_time * 1000
            
            use_astar = self._use_astar and self.should_use_astar(target)
            
            new_direction = Direction.NONE
            
            if use_astar:
                astar_interval = {
                    "red": 100,
                    "pink": 100,
                    "cyan": 100,
                    "orange": 100
                }.get(self._ghost_type, 500)
                
                if self._recalculate_path_timer > astar_interval:
                    new_direction = self.astar_pathfinding(game_map, target)
                    if new_direction != Direction.NONE:
                        self._direction = new_direction
                        self._last_direction = new_direction
                    self._recalculate_path_timer = 0
            else:
                legacy_interval = {
                    "red": 250,
                    "pink": 400,
                    "cyan": 350,
                    "orange": 500
                }.get(self._ghost_type, 350)
                
                if self._path_finding_timer > legacy_interval:
                    new_direction = self.choose_direction_advanced(game_map, target)
                    if new_direction != Direction.NONE:
                        self._direction = new_direction
                        self._last_direction = new_direction
                    self._path_finding_timer = 0

            if self.can_move(self._direction, game_map):
                self.move()
            else:
                if use_astar:
                    self._current_path = []
                    self._direction = self.astar_pathfinding(game_map, target)
                else:
                    self._direction = self.choose_direction_advanced(game_map, target)
                
                if self._direction != Direction.NONE:
                    self._last_direction = self._direction

        self._animation_frame += 1

class Pellet(GameObject):
    def __init__(self, x, y, color, size, pellet_type="normal", value=10):
        super().__init__(x, y, color, size)
        self._type = pellet_type
        self._value = value

    @property
    def type(self):
        return self._type

    @property
    def value(self):
        return self._value

    def be_eaten(self):
        return self._value

    def draw(self, screen, scale_factor=1.0, offset_x=0, offset_y=0):
        sprite = sprite_manager.get_pellet_sprite(self._type, self._animation_frame)
        
        sprite_size = sprite_manager.sprite_size
        x = int((self._position.x - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_x
        y = int((self._position.y - sprite_manager.base_sprite_size // 2) * scale_factor) + offset_y
        
        screen.blit(sprite, (x, y))

    def update(self, delta_time):
        self._animation_frame += 1