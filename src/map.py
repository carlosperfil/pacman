import pygame
import json
import os
import glob
from .utils import Vector2D
from .sprite_manager import sprite_manager

class Map:
    def __init__(self, layout_data=None, cell_size=None, map_file_path=None):
        """
        Inicializa o mapa. Por padrão, carrega de arquivo JSON.
        
        Args:
            layout_data: Dados de layout manuais (opcional, para compatibilidade)
            cell_size: Tamanho das células (opcional)
            map_file_path: Caminho para arquivo JSON do mapa (opcional)
        """
        self._layout = []
        self._cell_size = cell_size if cell_size else sprite_manager.base_sprite_size
        self._width = 0
        self._height = 0
        self._metadata = {}
        self._spawn_positions = {}
        self._original_map_path = None
        
        # Se dados manuais fornecidos, usa eles (compatibilidade)
        if layout_data:
            self._layout = layout_data
            self._update_dimensions()
            self._set_default_spawn_positions()
        else:
            # Sempre tenta carregar de JSON primeiro
            map_path = map_file_path or "assets/maps/default_map.json"
            if not self.load_from_json(map_path):
                print(f"Aviso: Falha ao carregar mapa JSON. Usando mapa padrão.")
                self.load_default_map()

    def load_from_json(self, file_path):
        """
        Carrega mapa de um arquivo JSON.
        
        Args:
            file_path: Caminho para o arquivo JSON
            
        Returns:
            bool: True se carregou com sucesso, False caso contrário
        """
        try:
            # Verifica se arquivo existe
            if not os.path.exists(file_path):
                print(f"Erro: Arquivo de mapa não encontrado: {file_path}")
                return False
            
            # Carrega e valida JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                map_data = json.load(f)
            
            # Valida estrutura básica do JSON
            if not self._validate_map_json(map_data):
                print(f"Erro: Estrutura inválida no arquivo de mapa: {file_path}")
                return False
            
            # Extrai dados do JSON
            self._metadata = map_data.get('metadata', {})
            self._layout = map_data['layout']
            
            # Atualiza cell_size se especificado no JSON
            if 'cell_size' in self._metadata:
                self._cell_size = self._metadata['cell_size']
            
            # Carrega posições de spawn
            spawn_data = map_data.get('spawn_positions', {})
            self._load_spawn_positions(spawn_data)
            
            # Atualiza dimensões
            self._update_dimensions()
            
            # Valida dimensões
            if not self._validate_dimensions():
                print(f"Erro: Dimensões inválidas no mapa")
                return False
            
            # Salva o caminho original para reset
            self._original_map_path = file_path
            
            print(f"Mapa carregado com sucesso: {self._metadata.get('name', 'Sem nome')}")
            print(f"Dimensões: {self._width}x{self._height}, Cell Size: {self._cell_size}")
            return True
            
        except json.JSONDecodeError as e:
            print(f"Erro ao decodificar JSON: {e}")
            return False
        except Exception as e:
            print(f"Erro inesperado ao carregar mapa: {e}")
            return False

    def _validate_map_json(self, map_data):
        """
        Valida se o JSON do mapa tem a estrutura correta.
        
        Args:
            map_data: Dados do mapa carregados do JSON
            
        Returns:
            bool: True se válido, False caso contrário
        """
        # Verifica campos obrigatórios
        required_fields = ['layout']
        for field in required_fields:
            if field not in map_data:
                print(f"Campo obrigatório ausente: {field}")
                return False
        
        # Valida layout
        layout = map_data['layout']
        if not isinstance(layout, list) or len(layout) == 0:
            print("Layout deve ser uma lista não-vazia")
            return False
        
        # Verifica se todas as linhas têm o mesmo tamanho
        row_length = len(layout[0])
        for i, row in enumerate(layout):
            if not isinstance(row, list):
                print(f"Linha {i} deve ser uma lista")
                return False
            if len(row) != row_length:
                print(f"Linha {i} tem tamanho inconsistente")
                return False
            
            # Valida valores das células
            for j, cell in enumerate(row):
                if not isinstance(cell, int) or cell < 0 or cell > 3:
                    print(f"Valor inválido na posição ({i}, {j}): {cell}")
                    return False
        
        return True

    def _load_spawn_positions(self, spawn_data):
        """
        Carrega posições de spawn do JSON.
        
        Args:
            spawn_data: Dados de spawn do JSON
        """
        self._spawn_positions = {}
        
        for entity_type, pos_data in spawn_data.items():
            if isinstance(pos_data, dict) and 'x' in pos_data and 'y' in pos_data:
                # Converte coordenadas de grid para coordenadas do mundo
                x = pos_data['x'] * self._cell_size + self._cell_size // 2
                y = pos_data['y'] * self._cell_size + self._cell_size // 2
                self._spawn_positions[entity_type] = Vector2D(x, y)
        
        # Se não há posições de spawn definidas, usa padrões
        if not self._spawn_positions:
            self._set_default_spawn_positions()

    def _set_default_spawn_positions(self):
        """Define posições de spawn padrão."""
        self._spawn_positions = {
            "player": Vector2D(1 * self._cell_size + self._cell_size // 2, 1 * self._cell_size + self._cell_size // 2),
            "ghost_red": Vector2D(17 * self._cell_size + self._cell_size // 2, 9 * self._cell_size + self._cell_size // 2),
            "ghost_pink": Vector2D(18 * self._cell_size + self._cell_size // 2, 9 * self._cell_size + self._cell_size // 2),
            "ghost_cyan": Vector2D(17 * self._cell_size + self._cell_size // 2, 10 * self._cell_size + self._cell_size // 2),
            "ghost_orange": Vector2D(18 * self._cell_size + self._cell_size // 2, 10 * self._cell_size + self._cell_size // 2)
        }

    def _update_dimensions(self):
        """Atualiza as dimensões do mapa baseado no layout."""
        self._height = len(self._layout)
        self._width = len(self._layout[0]) if self._layout else 0

    def _validate_dimensions(self):
        """Valida se as dimensões do mapa são válidas."""
        return self._width > 0 and self._height > 0

    @property
    def layout(self):
        return self._layout

    @property
    def cell_size(self):
        return self._cell_size

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def metadata(self):
        """Retorna metadados do mapa."""
        return self._metadata

    @property
    def difficulty(self):
        """
        Retorna o nível de dificuldade do mapa (0-200).
        
        Returns:
            int: Nível de dificuldade (0=fácil, 100=médio, 200=extremo)
        """
        return self._metadata.get('difficulty', 50)  # Padrão médio se não especificado

    @staticmethod
    def get_available_maps():
        """
        Retorna lista de todos os mapas disponíveis ordenados por dificuldade.
        
        Returns:
            List[dict]: Lista de mapas com informações básicas
        """
        maps_dir = "assets/maps"
        if not os.path.exists(maps_dir):
            return []
        
        maps = []
        for file_path in glob.glob(os.path.join(maps_dir, "*.json")):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                maps.append({
                    'file_path': file_path,
                    'name': metadata.get('name', 'Mapa Sem Nome'),
                    'difficulty': metadata.get('difficulty', 50),
                    'description': metadata.get('description', ''),
                    'width': metadata.get('width', '?'),
                    'height': metadata.get('height', '?')
                })
            except Exception as e:
                print(f"Erro ao carregar mapa {file_path}: {e}")
        
        # Ordena por dificuldade (fácil para difícil)
        maps.sort(key=lambda m: m['difficulty'])
        return maps

    def load_default_map(self):
        """Carrega um mapa padrão para o jogo (fallback)"""
        print("Carregando mapa padrão como fallback...")
        
        # Layout do labirinto (1=parede, 0=caminho, 2=pellet, 3=power_up)
        self._layout = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 3, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 3, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 2, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 2, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 2, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 2, 1, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 1, 2, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 2, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 2, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 1, 1, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1],
            [1, 3, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 3, 1],
            [1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1],
            [1, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 1],
            [1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1],
            [1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        ]
        
        self._update_dimensions()
        self._set_default_spawn_positions()
        self._metadata = {
            "name": "Mapa Padrão (Fallback)",
            "version": "1.0",
            "description": "Mapa carregado como fallback"
        }

    def load_map(self, map_file_path):
        """
        Carrega mapa de um arquivo JSON.
        
        Args:
            map_file_path: Caminho para o arquivo JSON
            
        Returns:
            bool: True se carregou com sucesso
        """
        return self.load_from_json(map_file_path)

    def get_pellets(self):
        """Retorna lista de pellets baseada no layout do mapa"""
        pellets = []
        for row_idx, row in enumerate(self._layout):
            for col_idx, cell in enumerate(row):
                if cell == 2:  # Pellet normal
                    x = col_idx * self._cell_size + self._cell_size // 2
                    y = row_idx * self._cell_size + self._cell_size // 2
                    pellets.append({"position": Vector2D(x, y), "type": "normal", "value": 10})
                elif cell == 3:  # Power-up
                    x = col_idx * self._cell_size + self._cell_size // 2
                    y = row_idx * self._cell_size + self._cell_size // 2
                    pellets.append({"position": Vector2D(x, y), "type": "power_up", "value": 50})
        return pellets

    def get_spawn_position(self, entity_type="player"):
        """
        Retorna posição de spawn para diferentes entidades.
        
        Args:
            entity_type: Tipo da entidade
            
        Returns:
            Vector2D: Posição de spawn
        """
        return self._spawn_positions.get(
            entity_type, 
            Vector2D(self._cell_size, self._cell_size)  # Fallback
        )

    def draw(self, screen, scale_factor=1.0, offset_x=0, offset_y=0):
        """Desenha o mapa na tela com escala"""
        scaled_cell_size = int(self._cell_size * scale_factor)
        
        for row_idx, row in enumerate(self._layout):
            for col_idx, cell in enumerate(row):
                x = int(col_idx * self._cell_size * scale_factor) + offset_x
                y = int(row_idx * self._cell_size * scale_factor) + offset_y
                rect = pygame.Rect(x, y, scaled_cell_size, scaled_cell_size)
                
                if cell == 1:  # Parede
                    # Desenho procedural das paredes (sem sprites disponíveis)
                    pygame.draw.rect(screen, (0, 0, 255), rect)  # Azul para paredes
                    
                    border_width = max(1, int(1 * scale_factor))
                    pygame.draw.rect(screen, (0, 0, 200), rect, border_width)
                elif cell == 0:  # Caminho vazio
                    pygame.draw.rect(screen, (0, 0, 0), rect)  # Preto para caminhos

    def is_wall(self, position: Vector2D):
        """Verifica se uma posição é uma parede"""
        # Converte posição do mundo para coordenadas da grade
        col = int(position.x // self._cell_size)
        row = int(position.y // self._cell_size)
        
        # Verifica limites
        if row < 0 or row >= self._height or col < 0 or col >= self._width:
            return True
        
        # Retorna True se for parede (1)
        return self._layout[row][col] == 1

    def is_valid_position(self, position: Vector2D, object_size=16, type="player"):
        """
        Verifica se uma posição é válida considerando o tamanho do objeto
        
        Args:
            position: Posição a ser verificada
            object_size: Tamanho do sprite (geralmente 16px)
            type: Tipo da entidade ("player", "ghost" ou "default")
        
        Returns:
            bool: True se a posição for válida (sem colisão com paredes)
        """
        # Define diferentes margens para diferentes tipos de entidades
        # Margens menores = controle mais preciso, mas mais difícil passar por espaços apertados
        # Margens maiores = controle mais fluido, mas pode causar colisões aparentemente incorretas
        if type == "player":
            # Player tem margem mais apertada para movimento mais preciso e controle responsivo
            # Permite ao jogador navegar por corredores estreitos com mais facilidade
            half_size = object_size // 2.125
        elif type == "ghost":
            # Fantasmas têm margem ligeiramente mais generosa para movimento mais fluido
            # Evita que os fantasmas fiquem "presos" em situações de pathfinding
            half_size = object_size // 3  
        else:
            # Default para outros objetos (pellets, itens especiais, etc.)
            half_size = object_size //3 
        
        corners = [
            Vector2D(position.x - half_size, position.y - half_size),
            Vector2D(position.x + half_size, position.y - half_size),
            Vector2D(position.x - half_size, position.y + half_size),
            Vector2D(position.x + half_size, position.y + half_size)
        ]
        
        for corner in corners:
            if self.is_wall(corner):
                return False
        return True

    def remove_pellet_at(self, position: Vector2D):
        """Remove um pellet na posição especificada"""
        col = int(position.x // self._cell_size)
        row = int(position.y // self._cell_size)
        
        if 0 <= row < self._height and 0 <= col < self._width:
            if self._layout[row][col] in [2, 3]:  # Se é pellet ou power-up
                self._layout[row][col] = 0  # Torna caminho vazio
                return True
        return False

    def count_pellets(self):
        """Conta quantos pellets restam no mapa"""
        count = 0
        for row in self._layout:
            for cell in row:
                if cell in [2, 3]:  # Pellet normal ou power-up
                    count += 1
        return count 
    
    def reset_map(self):
        """Reseta o mapa para o estado inicial, restaurando todos os pellets"""
        # Tenta recarregar o mapa do JSON original
        if hasattr(self, '_original_map_path'):
            if self.load_from_json(self._original_map_path):
                return
        
        # Fallback: carrega mapa padrão
        self.load_default_map()