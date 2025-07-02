import pygame
import sys
import json
import os
from src.game_objects import Player, Ghost, Pellet
from src.map import Map
from src.utils import Vector2D, Direction, GameState
from src.sprite_manager import sprite_manager
from src.sound_manager import sound_manager, SoundType

class HighScoreManager:
    def __init__(self, filename="highscores.json"):
        self.filename = filename
        self.highscores = self.load_highscores()

    def load_highscores(self):
        if os.path.exists(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except Exception:
                    return []
        return []

    def save_highscores(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.highscores, f, ensure_ascii=False, indent=2)

    def add_score(self, name, score):
        self.highscores.append({"name": name, "score": score})
        self.highscores = sorted(self.highscores, key=lambda x: x["score"], reverse=True)[:10]
        self.save_highscores()

class Game:
    def __init__(self, width=560, height=400):
        pygame.init()
        
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("Mixer do Pygame inicializado no Game")
        except Exception as e:
            print(f"Erro ao inicializar mixer no Game: {e}")
        
        # Dimensões originais e atuais
        self._original_width = width
        self._original_height = height
        self._width = width
        self._height = height
        
        # Dimensões escalonadas
        self._base_map_height = 336
        self._map_height = 336
        self._hud_y_start = self._map_height + 5
        
        # Fator de escala global
        self._scale_factor = 1.0
        
        # Configuração da janela
        self._screen = pygame.display.set_mode((self._width, self._height), pygame.RESIZABLE)
        pygame.display.set_caption("Pac-Man OO - Projeto Orientado a Objetos")
        self._clock = pygame.time.Clock()
        self._state = GameState.MENU
        
        # Fonts com escala
        self._update_fonts()
        
        self._initialize_sound_system()
        
        self._menu_options = ["Jogar", "Opções", "Sair"]
        self._selected_option = 0
        self._menu_animation_frame = 0
        
        self._options_menu = ["Ver Histórico", "Volume Música", "Volume Efeitos", "Volume Interface", "Volume Fantasmas", "Voltar"]
        self._selected_option_options = 0
        self._volume_step = 0.1
        
        self._history_page = 0
        self._history_per_page = 8
        
        self._highscore_manager = HighScoreManager()
        self._input_active = False
        self._player_name = ""
        self._show_save_confirmation = False
        self._save_confirmation_timer = 0
        
        self._available_maps = []
        self._current_map_index = 0
        self._campaign_total_score = 0
        self._intermission_timer = 0
        self._intermission_duration = 3000
        self._next_map_info = None
        
        self._initialize_campaign()
        self._initialize_game()

    def _update_fonts(self):
        """Atualiza os tamanhos das fontes baseado na escala"""
        base_large = 48
        base_medium = 32
        base_small = 24
        base_tiny = 22
        
        self._font_large = pygame.font.Font(None, max(12, int(base_large * self._scale_factor)))
        self._font_medium = pygame.font.Font(None, max(10, int(base_medium * self._scale_factor)))
        self._font_small = pygame.font.Font(None, max(8, int(base_small * self._scale_factor)))
        self._font_tiny = pygame.font.Font(None, max(6, int(base_tiny * self._scale_factor)))

    def _calculate_scale_factor(self, new_width, new_height):
        """Calcula o fator de escala baseado nas novas dimensões"""
        # Calcula escala baseada na menor dimensão para manter proporções
        scale_x = new_width / self._original_width
        scale_y = new_height / self._original_height
        return min(scale_x, scale_y)

    def _update_scale(self, new_width, new_height):
        """Atualiza a escala do jogo baseado nas novas dimensões"""
        self._width = new_width
        self._height = new_height
        
        # Calcula nova escala
        new_scale = self._calculate_scale_factor(new_width, new_height)
        
        if abs(new_scale - self._scale_factor) > 0.01:  # Evita updates muito pequenos
            self._scale_factor = new_scale
            
            # Atualiza dimensões escaladas
            self._map_height = int(self._base_map_height * self._scale_factor)
            self._hud_y_start = self._map_height + int(5 * self._scale_factor)
            
            # Atualiza escala dos sprites
            sprite_manager.set_scale_factor(self._scale_factor)
            
            # Atualiza fontes
            self._update_fonts()
            
            print(f"Janela redimensionada: {new_width}x{new_height}, escala: {self._scale_factor:.2f}x")

    def _get_scaled_pos(self, x, y):
        """Converte posições do espaço do jogo para o espaço da tela escalada"""
        # Centraliza o jogo na tela quando há espaço extra
        scaled_width = int(self._original_width * self._scale_factor)
        scaled_height = int(self._original_height * self._scale_factor)
        
        offset_x = (self._width - scaled_width) // 2
        offset_y = (self._height - scaled_height) // 2
        
        return (
            int(x * self._scale_factor) + offset_x,
            int(y * self._scale_factor) + offset_y
        )

    def _get_scaled_rect(self, x, y, width, height):
        """Converte um retângulo para o espaço escalado"""
        scaled_x, scaled_y = self._get_scaled_pos(x, y)
        return pygame.Rect(
            scaled_x, scaled_y,
            int(width * self._scale_factor),
            int(height * self._scale_factor)
        )

    def _initialize_sound_system(self):
        sound_manager.set_volume(SoundType.MUSIC, 0.3)
        sound_manager.set_volume(SoundType.EFFECT, 0.7)
        sound_manager.set_volume(SoundType.UI, 0.8)
        sound_manager.set_volume(SoundType.GHOST, 0.6)
        sound_manager.play_sound("music_menu")

    def _initialize_campaign(self):
        from src.map import Map
        self._available_maps = Map.get_available_maps()
        self._current_map_index = 0
        self._campaign_total_score = 0
        
        print(f"Campanha inicializada com {len(self._available_maps)} mapas:")
        for i, map_info in enumerate(self._available_maps):
            difficulty_label = self._get_difficulty_label(map_info['difficulty'])
            print(f"  {i+1}. {map_info['name']} - {map_info['difficulty']}/200 ({difficulty_label})")

    def _get_difficulty_label(self, difficulty):
        if difficulty >= 175:
            return "EXTREMO"
        elif difficulty >= 150:
            return "MUITO DIFÍCIL"
        elif difficulty >= 125:
            return "DIFÍCIL+"
        elif difficulty >= 100:
            return "DIFÍCIL"
        elif difficulty >= 75:
            return "MÉDIO+"
        elif difficulty >= 50:
            return "MÉDIO"
        elif difficulty >= 25:
            return "FÁCIL+"
        else:
            return "MUITO FÁCIL"

    def _get_difficulty_color(self, difficulty):
        if difficulty >= 175:
            return (150, 0, 0)
        elif difficulty >= 150:
            return (200, 0, 0)
        elif difficulty >= 125:
            return (255, 50, 50)
        elif difficulty >= 100:
            return (255, 100, 0)
        elif difficulty >= 75:
            return (255, 150, 50)
        elif difficulty >= 50:
            return (255, 255, 50)
        elif difficulty >= 25:
            return (150, 255, 150)
        else:
            return (100, 255, 100)

    def _initialize_game(self):
        current_map_path = None
        if self._available_maps and self._current_map_index < len(self._available_maps):
            current_map_path = self._available_maps[self._current_map_index]['file_path']
        
        if hasattr(self, '_map') and self._map is not None and current_map_path:
            self._map = Map(map_file_path=current_map_path)
        elif current_map_path:
            self._map = Map(map_file_path=current_map_path)
        else:
            self._map = Map()
        
        player_pos = self._map.get_spawn_position("player")
        self._player = Player(
            x=player_pos.x, 
            y=player_pos.y, 
            color=(255, 255, 0), 
            size=sprite_manager.base_sprite_size,
            speed=2,  
            lives=20
        )
        
        self._ghosts = []
        ghost_configs = [
            {"type": "red", "color": (255, 0, 0)},
            {"type": "pink", "color": (255, 182, 193)},
            {"type": "cyan", "color": (0, 255, 255)},
            {"type": "orange", "color": (255, 165, 0)}
        ]
        
        for config in ghost_configs:
            ghost_pos = self._map.get_spawn_position(f"ghost_{config['type']}")
            ghost = Ghost(
                x=ghost_pos.x,
                y=ghost_pos.y,
                color=config["color"],
                size=sprite_manager.base_sprite_size,
                speed=1.5,  
                initial_position=ghost_pos,
                ghost_type=config["type"]
            )
            self._ghosts.append(ghost)
        
        self._pellets = []
        pellet_data = self._map.get_pellets()
        for pellet_info in pellet_data:
            pellet = Pellet(
                x=pellet_info["position"].x,
                y=pellet_info["position"].y,
                color=(255, 255, 255),
                size=sprite_manager.base_sprite_size,
                pellet_type=pellet_info["type"],
                value=pellet_info["value"]
            )
            self._pellets.append(pellet)
        
        self._total_pellets = len(self._pellets)
        self._game_start_time = pygame.time.get_ticks()
        
        map_difficulty = self._map.difficulty
        if isinstance(map_difficulty, str):
            try:
                map_difficulty = int(map_difficulty)
            except (ValueError, TypeError):
                map_difficulty = 0
        elif not isinstance(map_difficulty, int):
            map_difficulty = 0
            
        for ghost in self._ghosts:
            ghost.set_difficulty(map_difficulty)
        
        print(f"Mapa carregado: {self._map.metadata.get('name', 'Sem nome')}")
        print(f"Dificuldade do mapa: {map_difficulty}/200 ({map_difficulty//2}%)")
        print(f"Pellets no mapa: {len(self._pellets)}")

    def _reset_game(self):
        sound_manager.stop_all_sounds()
        
        self._input_active = False
        self._player_name = ""
        self._show_save_confirmation = False
        self._save_confirmation_timer = 0
        
        self._current_map_index = 0
        self._campaign_total_score = 0
        
        self._initialize_game()
        self._state = GameState.PLAYING
        sound_manager.play_sound("music_menu")

    def _reset_positions(self):
        player_pos = self._map.get_spawn_position("player")
        self._player.position = player_pos
        
        for ghost in self._ghosts:
            ghost.reset_position()

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        self._state = new_state

    def _set_game_over(self):
        self._state = GameState.GAME_OVER
        self._input_active = True
        self._player_name = ""
        self._show_save_confirmation = False

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            elif event.type == pygame.VIDEORESIZE:
                # Trata o redimensionamento da janela
                self._update_scale(event.w, event.h)
                self._screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                
            elif event.type == pygame.KEYDOWN:
                if self._state == GameState.MENU:
                    if event.key == pygame.K_UP:
                        self._selected_option = (self._selected_option - 1) % len(self._menu_options)
                    elif event.key == pygame.K_DOWN:
                        self._selected_option = (self._selected_option + 1) % len(self._menu_options)
                    elif event.key == pygame.K_RETURN:
                        if self._selected_option == 0:
                            self._reset_game()
                        elif self._selected_option == 1:
                            self._state = GameState.OPTIONS
                        elif self._selected_option == 2:
                            return False
                    elif event.key == pygame.K_ESCAPE:
                        return False
                
                elif self._state == GameState.OPTIONS:
                    if event.key == pygame.K_UP:
                        self._selected_option_options = (self._selected_option_options - 1) % len(self._options_menu)
                    elif event.key == pygame.K_DOWN:
                        self._selected_option_options = (self._selected_option_options + 1) % len(self._options_menu)
                    elif event.key == pygame.K_RETURN:
                        if self._selected_option_options == 0:
                            self._state = GameState.HISTORY
                            self._history_page = 0
                        elif self._selected_option_options == 5:
                            self._state = GameState.MENU
                    elif event.key == pygame.K_LEFT:
                        if self._selected_option_options == 1:
                            current = sound_manager.get_volume(SoundType.MUSIC)
                            new_volume = max(0.0, current - self._volume_step)
                            sound_manager.set_volume(SoundType.MUSIC, new_volume)
                        elif self._selected_option_options == 2:
                            current = sound_manager.get_volume(SoundType.EFFECT)
                            new_volume = max(0.0, current - self._volume_step)
                            sound_manager.set_volume(SoundType.EFFECT, new_volume)
                        elif self._selected_option_options == 3:
                            current = sound_manager.get_volume(SoundType.UI)
                            new_volume = max(0.0, current - self._volume_step)
                            sound_manager.set_volume(SoundType.UI, new_volume)
                        elif self._selected_option_options == 4:
                            current = sound_manager.get_volume(SoundType.GHOST)
                            new_volume = max(0.0, current - self._volume_step)
                            sound_manager.set_volume(SoundType.GHOST, new_volume)
                        else:
                            self._state = GameState.MENU
                    elif event.key == pygame.K_RIGHT:
                        if self._selected_option_options == 1:
                            current = sound_manager.get_volume(SoundType.MUSIC)
                            new_volume = min(1.0, current + self._volume_step)
                            sound_manager.set_volume(SoundType.MUSIC, new_volume)
                        elif self._selected_option_options == 2:
                            current = sound_manager.get_volume(SoundType.EFFECT)
                            new_volume = min(1.0, current + self._volume_step)
                            sound_manager.set_volume(SoundType.EFFECT, new_volume)
                        elif self._selected_option_options == 3:
                            current = sound_manager.get_volume(SoundType.UI)
                            new_volume = min(1.0, current + self._volume_step)
                            sound_manager.set_volume(SoundType.UI, new_volume)
                        elif self._selected_option_options == 4:
                            current = sound_manager.get_volume(SoundType.GHOST)
                            new_volume = min(1.0, current + self._volume_step)
                            sound_manager.set_volume(SoundType.GHOST, new_volume)
                    elif event.key == pygame.K_ESCAPE:
                        self._state = GameState.MENU
                
                elif self._state == GameState.HISTORY:
                    if event.key == pygame.K_UP:
                        self._history_page = max(0, self._history_page - 1)
                    elif event.key == pygame.K_DOWN:
                        max_pages = max(0, (len(self._highscore_manager.highscores) - 1) // self._history_per_page)
                        self._history_page = min(max_pages, self._history_page + 1)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_ESCAPE:
                        self._state = GameState.OPTIONS
                elif self._state == GameState.PLAYING:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        self._player.direction = Direction.UP
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        self._player.direction = Direction.DOWN
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self._player.direction = Direction.LEFT
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self._player.direction = Direction.RIGHT
                    elif event.key == pygame.K_ESCAPE:
                        self._state = GameState.PAUSED
                        sound_manager.pause_all_sounds()
                        
                elif self._state == GameState.PAUSED:
                    if event.key == pygame.K_ESCAPE:
                        self._state = GameState.PLAYING
                        sound_manager.unpause_all_sounds()
                    elif event.key == pygame.K_RETURN:
                        self._initialize_game()
                        self._state = GameState.MENU
                        sound_manager.stop_all_sounds()
                        sound_manager.play_sound("music_menu")
                    return True
                elif self._state == GameState.GAME_OVER:
                    if self._input_active:
                        if event.key == pygame.K_RETURN:
                            if self._player_name.strip():
                                self._highscore_manager.add_score(self._player_name.strip(), self._player.score)
                                self._input_active = False
                                self._show_save_confirmation = True
                                self._save_confirmation_timer = pygame.time.get_ticks()
                        elif event.key == pygame.K_BACKSPACE:
                            self._player_name = self._player_name[:-1]
                        else:
                            if len(self._player_name) < 12 and event.unicode.isprintable():
                                self._player_name += event.unicode
                        return True
                    elif not self._input_active and not self._show_save_confirmation:
                        if event.key == pygame.K_RETURN:
                            self._reset_game()
                        elif event.key == pygame.K_ESCAPE:
                            self._state = GameState.MENU
                            sound_manager.stop_all_sounds()
                            sound_manager.play_sound("music_menu")
                        return True
                elif self._state == GameState.VICTORY:
                    if self._input_active:
                        if event.key == pygame.K_RETURN:
                            if self._player_name.strip():
                                self._highscore_manager.add_score(self._player_name.strip(), self._campaign_total_score)
                                self._input_active = False
                                self._show_save_confirmation = True
                                self._save_confirmation_timer = pygame.time.get_ticks()
                        elif event.key == pygame.K_BACKSPACE:
                            self._player_name = self._player_name[:-1]
                        else:
                            if len(self._player_name) < 12 and event.unicode.isprintable():
                                self._player_name += event.unicode
                        return True
                    elif not self._input_active and not self._show_save_confirmation:
                        if event.key == pygame.K_RETURN:
                            self._reset_game()
                        elif event.key == pygame.K_ESCAPE:
                            self._state = GameState.MENU
                            sound_manager.stop_all_sounds()
                            sound_manager.play_sound("music_menu")
                        return True
                elif self._state == GameState.INTERMISSION:
                    if event.key == pygame.K_RETURN:
                        self._initialize_game()
                        self._state = GameState.PLAYING
                        sound_manager.stop_all_sounds()
                        sound_manager.play_sound("music_menu")
                    elif event.key == pygame.K_ESCAPE:
                        self._state = GameState.MENU
                        sound_manager.stop_all_sounds()
                        sound_manager.play_sound("music_menu")
        
        return True

    def update(self, delta_time):
        if self._show_save_confirmation:
            if pygame.time.get_ticks() - self._save_confirmation_timer > 1000:
                self._show_save_confirmation = False
                self._state = GameState.MENU
                sound_manager.stop_all_sounds()
                sound_manager.play_sound("music_menu")
            return

        if self._state == GameState.INTERMISSION:
            current_time = pygame.time.get_ticks()
            if current_time - self._intermission_timer >= self._intermission_duration:
                self._initialize_game()
                self._state = GameState.PLAYING
                sound_manager.play_sound("music_menu")
                return

        if (self._state == GameState.VICTORY or self._state == GameState.GAME_OVER) and not self._input_active and not self._show_save_confirmation:
            self._input_active = True
            self._player_name = ""

        if self._state not in [GameState.PLAYING, GameState.INTERMISSION]:
            return
        
        if self._state == GameState.PLAYING:
            self._player.update(delta_time, self._map)
            
            for ghost in self._ghosts:
                ghost.update(delta_time, self._player.position, self._player.direction, self._map, self._ghosts)
            
            pellets_to_remove = []
            for pellet in self._pellets:
                distance = self._player.position.distance_to(pellet.position)
                collision_radius = sprite_manager.base_sprite_size // 2
                if distance < collision_radius:
                    points = pellet.be_eaten()
                    self._player.eat_pellet(points)
                    self._map.remove_pellet_at(pellet.position)
                    
                    if pellet.type == "power_up":
                        self._player.activate_power_up()
                        for ghost in self._ghosts:
                            ghost.set_vulnerable(8000)
                        sound_manager.play_sound("ghost-turn-to-blue")
                    else:
                        sound_manager.play_sound("eating")
                    
                    pellets_to_remove.append(pellet)
            
            for pellet in pellets_to_remove:
                self._pellets.remove(pellet)
            
            if len(self._pellets) == 0:
                self._campaign_total_score += self._player.score
                
                if self._current_map_index + 1 < len(self._available_maps):
                    self._current_map_index += 1
                    self._next_map_info = self._available_maps[self._current_map_index]
                    self._state = GameState.INTERMISSION
                    self._intermission_timer = pygame.time.get_ticks()
                    
                    sound_manager.stop_all_sounds()
                    sound_manager.play_sound("extend")
                    
                    print(f"✅ Mapa completado! Avançando para: {self._next_map_info['name']}")
                else:
                    self._state = GameState.VICTORY
                    sound_manager.stop_all_sounds()
                    sound_manager.play_sound("credit")
                    
                    print(f"CAMPANHA COMPLETA! Pontuação total: {self._campaign_total_score}")
                return
            
            for ghost in self._ghosts:
                distance = self._player.position.distance_to(ghost.position)
                collision_radius = sprite_manager.base_sprite_size // 2
                if distance < collision_radius:
                    if ghost.state == "vulnerable":
                        self._player.eat_pellet(200)
                        ghost.set_eaten_with_delay()
                        sound_manager.play_sound("eating-ghost")
                    elif ghost.state == "normal":
                        self._player.lose_life()
                        sound_manager.play_sound("miss")
                        
                        if self._player.lives <= 0:
                            self._set_game_over()
                            sound_manager.stop_all_sounds()
                            sound_manager.play_sound("miss")
                        else:
                            self._reset_positions()
                            pygame.time.wait(1000)

    def _draw_text_centered(self, text, font, color, y_offset=0):
        text_surface = font.render(text, True, color)
        scaled_width = int(self._original_width * self._scale_factor)
        scaled_height = int(self._original_height * self._scale_factor)
        
    
        offset_x = (self._width - scaled_width) // 2
        offset_y = (self._height - scaled_height) // 2
        
        center_x = offset_x + scaled_width // 2
        center_y = offset_y + scaled_height // 2 + int(y_offset * self._scale_factor)
        
        text_rect = text_surface.get_rect(center=(center_x, center_y))
        self._screen.blit(text_surface, text_rect)

    def _draw_hud(self):
       
        scaled_width = int(self._original_width * self._scale_factor)
        scaled_height = int(self._original_height * self._scale_factor)
        offset_x = (self._width - scaled_width) // 2
        offset_y = (self._height - scaled_height) // 2
        
       
        hud_start_x = offset_x + int(10 * self._scale_factor)
        hud_start_y = offset_y + self._hud_y_start
        hud_width = scaled_width - int(20 * self._scale_factor)
        
        score_text = self._font_small.render(f"Pontuação: {self._player.score}", True, (255, 255, 255))
        self._screen.blit(score_text, (hud_start_x, hud_start_y))
        
        lives_text = self._font_small.render(f"Vidas: {self._player.lives}", True, (255, 255, 255))
        lives_rect = lives_text.get_rect(topright=(hud_start_x + hud_width, hud_start_y))
        self._screen.blit(lives_text, lives_rect)
        
        pellets_remaining = len(self._pellets)
        pellets_text = self._font_small.render(f"Pellets: {pellets_remaining}", True, (255, 255, 255))
        center_x = offset_x + scaled_width // 2
        pellets_rect = pellets_text.get_rect(center=(center_x, hud_start_y + int(25 * self._scale_factor)))
        self._screen.blit(pellets_text, pellets_rect)
        
        pellets_start_x = pellets_rect.left
        
        if hasattr(self, '_map') and self._map is not None:
            map_difficulty = self._map.difficulty
            if isinstance(map_difficulty, str):
                try:
                    map_difficulty = int(map_difficulty)
                except (ValueError, TypeError):
                    map_difficulty = 0
            elif not isinstance(map_difficulty, int):
                map_difficulty = 0
                
            difficulty_color = (255, 255, 255)
            difficulty_label = "FÁCIL"
            
            if map_difficulty >= 175:
                difficulty_color = (150, 0, 0)
                difficulty_label = "EXTREMO"
            elif map_difficulty >= 150:
                difficulty_color = (200, 0, 0)
                difficulty_label = "MUITO DIFÍCIL" 
            elif map_difficulty >= 125:
                difficulty_color = (255, 50, 50)
                difficulty_label = "DIFÍCIL+"
            elif map_difficulty >= 100:
                difficulty_color = (255, 100, 0)
                difficulty_label = "DIFÍCIL"
            elif map_difficulty >= 75:
                difficulty_color = (255, 150, 50)
                difficulty_label = "MÉDIO+"
            elif map_difficulty >= 50:
                difficulty_color = (255, 255, 50)
                difficulty_label = "MÉDIO"
            elif map_difficulty >= 25:
                difficulty_color = (150, 255, 150)
                difficulty_label = "FÁCIL+"
            else:
                difficulty_color = (100, 255, 100)
                difficulty_label = "MUITO FÁCIL"
            
            difficulty_text = self._font_small.render(f"Dificuldade:{difficulty_label}", True, difficulty_color)
            self._screen.blit(difficulty_text, (hud_start_x, hud_start_y + int(25 * self._scale_factor)))
        
        if hasattr(self, '_available_maps') and self._available_maps:
            current_map = self._current_map_index + 1
            total_maps = len(self._available_maps)
            campaign_text = self._font_small.render(f"Mapa: {current_map}/{total_maps}", True, (200, 200, 255))
            campaign_rect = campaign_text.get_rect(topright=(hud_start_x + hud_width, hud_start_y + int(25 * self._scale_factor)))
            self._screen.blit(campaign_text, campaign_rect)
            
            if self._current_map_index < len(self._available_maps):
                map_name = self._available_maps[self._current_map_index]['name']
                if len(map_name) > 20:
                    map_name = map_name[:17] + "..."
                map_name_text = self._font_small.render(map_name, True, (150, 150, 255))
                map_name_rect = map_name_text.get_rect(center=(center_x, hud_start_y - int(40 * self._scale_factor)))
                self._screen.blit(map_name_text, map_name_rect)
        
        if self._player.power_up_active:
            power_text = self._font_small.render("POWER-UP ATIVO!", True, (255, 255, 0))
            power_rect = power_text.get_rect(center=(center_x, hud_start_y - int(20 * self._scale_factor)))
            self._screen.blit(power_text, power_rect)
        
        ghosts_in_delay = [ghost for ghost in self._ghosts if ghost.is_in_spawn_delay]
        if ghosts_in_delay:
            delay_info = []
            for ghost in ghosts_in_delay:
                remaining = ghost.spawn_delay_remaining
                delay_info.append(f"{ghost._ghost_type.capitalize()}:{remaining:.1f}s")
            
            delay_text = "Fantasmas em delay: " + ", ".join(delay_info)
            delay_surface = self._font_small.render(delay_text, True, (220, 0, 0))
            self._screen.blit(delay_surface, (pellets_start_x, hud_start_y + int(45 * self._scale_factor)))

    def render(self):
        self._screen.fill((0, 0, 0))
        
        # Calcula offset para centralizar o jogo
        scaled_width = int(self._original_width * self._scale_factor)
        scaled_height = int(self._original_height * self._scale_factor)
        offset_x = (self._width - scaled_width) // 2
        offset_y = (self._height - scaled_height) // 2
        
        if self._state == GameState.MENU:
            self._menu_animation_frame += 1
            self._draw_text_centered("PAC-MAN", self._font_large, (255, 255, 0), -120)
            for i, option in enumerate(self._menu_options):
                color = (255, 255, 0) if i == self._selected_option else (255, 255, 255)
                text_surface = self._font_medium.render(option, True, color)
                
                center_x = offset_x + scaled_width // 2
                center_y = offset_y + scaled_height // 2 - int(20 * self._scale_factor) + int(i * 45 * self._scale_factor)
                text_rect = text_surface.get_rect(center=(center_x, center_y))
                self._screen.blit(text_surface, text_rect)
                
                if i == self._selected_option:
                    pacman_sprite = sprite_manager.get_pacman_sprite(Direction.RIGHT, self._menu_animation_frame)
                    sprite_x = center_x - int(120 * self._scale_factor)
                    sprite_rect = pacman_sprite.get_rect(center=(sprite_x, center_y))
                    self._screen.blit(pacman_sprite, sprite_rect)
            self._draw_text_centered("Use as setas para navegar e ENTER para selecionar", self._font_small, (200, 200, 200), 120)

        elif self._state == GameState.OPTIONS:
            self._menu_animation_frame += 1
            self._draw_text_centered("OPÇÕES", self._font_large, (255, 255, 0), -140)
            for i, option in enumerate(self._options_menu):
                color = (255, 255, 0) if i == self._selected_option_options else (255, 255, 255)
                
                if 1 <= i <= 4:
                    volume_types = [None, SoundType.MUSIC, SoundType.EFFECT, SoundType.UI, SoundType.GHOST]
                    current_volume = sound_manager.get_volume(volume_types[i])
                    volume_text = f"{option}: {int(current_volume * 100)}%"
                    text_surface = self._font_small.render(volume_text, True, color)
                else:
                    text_surface = self._font_small.render(option, True, color)
                
                center_x = offset_x + scaled_width // 2
                center_y = offset_y + scaled_height // 2 - int(90 * self._scale_factor) + int(i * 25 * self._scale_factor)
                text_rect = text_surface.get_rect(center=(center_x, center_y))
                self._screen.blit(text_surface, text_rect)
                
                if i == self._selected_option_options:
                    pacman_sprite = sprite_manager.get_pacman_sprite(Direction.RIGHT, self._menu_animation_frame)
                    sprite_x = center_x - int(140 * self._scale_factor)
                    sprite_rect = pacman_sprite.get_rect(center=(sprite_x, center_y))
                    self._screen.blit(pacman_sprite, sprite_rect)
            
            self._draw_text_centered("Setas para navegar | ENTER para selecionar", self._font_small, (200, 200, 200), 110)
            self._draw_text_centered("ESQ ou ESC para voltar", self._font_small, (200, 200, 200), 130)
            if 1 <= self._selected_option_options <= 4:
                self._draw_text_centered("ESQ/DIR para ajustar volume", self._font_small, (255, 255, 0), 150)

        elif self._state == GameState.HISTORY:
            self._menu_animation_frame += 1
            self._draw_text_centered("HISTÓRICO DE PONTUAÇÕES", self._font_medium, (255, 255, 0), -140)
            
            scores = self._highscore_manager.highscores
            if not scores:
                self._draw_text_centered("Nenhuma pontuação registrada", self._font_medium, (255, 255, 255), 0)
            else:
                start_idx = self._history_page * self._history_per_page
                end_idx = min(start_idx + self._history_per_page, len(scores))
                
                for i in range(start_idx, end_idx):
                    score_data = scores[i]
                    position = i + 1
                    text = f"{position:2d}. {score_data['name']:12s} - {score_data['score']:6d}"
                    color = (255, 255, 0) if position <= 3 else (255, 255, 255)
                    
                    y_pos = -100 + (i - start_idx) * 20
                    self._draw_text_centered(text, self._font_small, color, y_pos)
                
                if len(scores) > self._history_per_page:
                    current_page = self._history_page + 1
                    total_pages = (len(scores) - 1) // self._history_per_page + 1
                    page_text = f"Página {current_page}/{total_pages}"
                    self._draw_text_centered(page_text, self._font_small, (200, 200, 200), 80)
            
            self._draw_text_centered("setas para navegar páginas", self._font_small, (200, 200, 200), 110)
            self._draw_text_centered("ESQ ou ESC para voltar", self._font_small, (200, 200, 200), 130)

        elif self._state == GameState.PLAYING:
            self._map.draw(self._screen, self._scale_factor, offset_x, offset_y)
            
            for pellet in self._pellets:
                pellet.draw(self._screen, self._scale_factor, offset_x, offset_y)
            
            self._player.draw(self._screen, self._scale_factor, offset_x, offset_y)
            for ghost in self._ghosts:
                ghost.draw(self._screen, self._scale_factor, offset_x, offset_y)
            
            self._draw_hud()
            
        elif self._state == GameState.PAUSED:
            self._map.draw(self._screen, self._scale_factor, offset_x, offset_y)
            for pellet in self._pellets:
                pellet.draw(self._screen, self._scale_factor, offset_x, offset_y)
            self._player.draw(self._screen, self._scale_factor, offset_x, offset_y)
            for ghost in self._ghosts:
                ghost.draw(self._screen, self._scale_factor, offset_x, offset_y)
            
            pause_surface = pygame.Surface((self._width, self._height))
            pause_surface.set_alpha(128)
            pause_surface.fill((0, 0, 0))
            self._screen.blit(pause_surface, (0, 0))
            
            self._draw_text_centered("PAUSADO", self._font_large, (255, 255, 255), -40)
            self._draw_text_centered("ESC - Continuar", self._font_small, (255, 255, 255), 0)
            self._draw_text_centered("ENTER - Menu", self._font_small, (255, 255, 255), 25)
            
        elif self._state == GameState.GAME_OVER:
            self._draw_text_centered("GAME OVER", self._font_large, (255, 0, 0), -80)
            self._draw_text_centered(f"Pontuação Final: {self._player.score}", self._font_medium, (255, 255, 255), -40)
            self._draw_text_centered(f"Pellets: {self._total_pellets - len(self._pellets)}/{self._total_pellets}", 
                                   self._font_small, (255, 255, 255), -10)
            if self._input_active:
                self._draw_text_centered("Digite seu nome e pressione ENTER:", self._font_small, (255, 255, 0), 45)
                name_surface = self._font_medium.render(self._player_name + "|", True, (255, 255, 255))
               
                center_x = offset_x + scaled_width // 2
                center_y = offset_y + scaled_height // 2 + int(85 * self._scale_factor)
                name_rect = name_surface.get_rect(center=(center_x, center_y))
                self._screen.blit(name_surface, name_rect)
            elif self._show_save_confirmation:
                self._draw_text_centered("Pontuação salva!", self._font_small, (0, 255, 0), 45)
            else:
                self._draw_text_centered("ENTER - Jogar Novamente", self._font_small, (255, 255, 255), 45)
                self._draw_text_centered("ESC - Menu", self._font_small, (255, 255, 255), 70)
            
        elif self._state == GameState.VICTORY:
            self._draw_text_centered("CAMPANHA COMPLETA!", self._font_large, (255, 215, 0), -100)
            
            total_maps = len(self._available_maps)
            self._draw_text_centered(f"Mapas Completados: {total_maps}/{total_maps}", 
                                   self._font_medium, (0, 255, 0), -60)
            self._draw_text_centered(f"Pontuação Total: {self._campaign_total_score}", 
                                   self._font_medium, (255, 255, 0), -30)
            
            if total_maps > 0:
                average_score = self._campaign_total_score // total_maps
                self._draw_text_centered(f"Média por Mapa: {average_score}", 
                                       self._font_small, (200, 200, 200), 0)
            
            self._draw_text_centered("Parabéns! Você dominou todos os mapas!", 
                                   self._font_small, (255, 255, 255), 30)
            
            if self._input_active:
                self._draw_text_centered("Digite seu nome e pressione ENTER:", self._font_small, (255, 255, 0), 75)
                name_surface = self._font_medium.render(self._player_name + "|", True, (255, 255, 255))
               
                center_x = offset_x + scaled_width // 2
                center_y = offset_y + scaled_height // 2 + int(115 * self._scale_factor)
                name_rect = name_surface.get_rect(center=(center_x, center_y))
                self._screen.blit(name_surface, name_rect)
            elif self._show_save_confirmation:
                self._draw_text_centered("Pontuação salva!", self._font_small, (0, 255, 0), 75)
            else:
                self._draw_text_centered("ENTER - Nova Campanha", self._font_small, (255, 255, 255), 75)
                self._draw_text_centered("ESC - Menu", self._font_small, (255, 255, 255), 100)
        
        elif self._state == GameState.INTERMISSION:
            self._draw_text_centered("MAPA COMPLETADO!", self._font_large, (0, 255, 0), -120)
            
            current_map = self._current_map_index 
            total_maps = len(self._available_maps)
            self._draw_text_centered(f"Progresso da Campanha: {current_map}/{total_maps}", 
                                   self._font_medium, (255, 255, 255), -80)
            
            self._draw_text_centered(f"Pontuação Total: {self._campaign_total_score}", 
                                   self._font_small, (255, 255, 0), -50)
            
            if self._next_map_info:
                self._draw_text_centered("PRÓXIMO MAPA:", self._font_medium, (255, 255, 255), -10)
                self._draw_text_centered(f"{self._next_map_info['name']}", 
                                       self._font_medium, (255, 255, 0), 15)
                
                difficulty_label = self._get_difficulty_label(self._next_map_info['difficulty'])
                difficulty_color = self._get_difficulty_color(self._next_map_info['difficulty'])
                self._draw_text_centered(f"Dificuldade: {difficulty_label}", 
                                       self._font_small, difficulty_color, 40)
                
                self._draw_text_centered(f"Tamanho: {self._next_map_info['width']}x{self._next_map_info['height']}", 
                                       self._font_small, (200, 200, 200), 60)
                
                if self._next_map_info.get('description'):
                    self._draw_text_centered(f"'{self._next_map_info['description']}'", 
                                           self._font_small, (150, 150, 150), 80)
            
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self._intermission_timer
            progress = min(elapsed / self._intermission_duration, 1.0)
            remaining_time = max(0, (self._intermission_duration - elapsed) / 1000.0)
            
            self._draw_text_centered(f"Carregando em {remaining_time:.1f}s", 
                                   self._font_small, (255, 255, 255), 110)
            
            bar_width = 300
            bar_height = 10
            bar_x = (self._width - bar_width) // 2
            bar_y = self._height // 2 + 140
            
            pygame.draw.rect(self._screen, (50, 50, 50), 
                           (bar_x, bar_y, bar_width, bar_height))
            
            progress_width = int(bar_width * progress)
            if progress_width > 0:
                pygame.draw.rect(self._screen, (0, 255, 0), 
                               (bar_x, bar_y, progress_width, bar_height))
            
            pygame.draw.rect(self._screen, (255, 255, 255), 
                           (bar_x, bar_y, bar_width, bar_height), 2)
            
            self._draw_text_centered("ENTER - Pular | ESC - Menu", 
                                   self._font_small, (150, 150, 150), 170)
        
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            delta_time = self._clock.tick(60) / 1000.0
            
            running = self.process_events()
            self.update(delta_time)
            self.render()
        
        pygame.quit()
        sys.exit()

def main():
    try:
        game = Game(width=560, height=400)
        game.run()
    except Exception as e:
        print(f"Erro ao executar o jogo: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main() 