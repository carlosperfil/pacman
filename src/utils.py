from enum import Enum #Enum é uma classe que define um conjunto de constantes com nomes simbólicos
import math

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

class GameState(Enum):
    MENU = 0
    PLAYING = 1
    GAME_OVER = 2
    PAUSED = 3
    VICTORY = 4
    OPTIONS = 5
    HISTORY = 6
    INTERMISSION = 7

class Vector2D: #classe que representa um vetor 2D
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        """Adiciona dois vetores ou um vetor e um tuple"""
        if isinstance(other, Vector2D):
            return Vector2D(self.x + other.x, self.y + other.y)
        elif isinstance(other, tuple) and len(other) == 2:
            return Vector2D(self.x + other[0], self.y + other[1])
        raise TypeError("Operando inválido para adição")

    def __sub__(self, other):
        """Subtrai dois vetores ou um vetor e um tuple"""
        if isinstance(other, Vector2D):
            return Vector2D(self.x - other.x, self.y - other.y)
        elif isinstance(other, tuple) and len(other) == 2:
            return Vector2D(self.x - other[0], self.y - other[1])
        raise TypeError("Operando inválido para subtração")

    def __mul__(self, scalar):
        """Multiplica um vetor por um escalar"""
        return Vector2D(self.x * scalar, self.y * scalar)

    def __eq__(self, other):
        """Verifica se dois vetores são iguais"""
        if isinstance(other, Vector2D):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, tuple) and len(other) == 2:
            return self.x == other[0] and self.y == other[1]
        return False

    def __str__(self):
        """Retorna uma string representando o vetor"""
        return f"({self.x}, {self.y})"

    def magnitude(self):
        """Calcula a magnitude (distância) do vetor"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self):
        """Retorna um vetor unitário na mesma direção"""
        mag = self.magnitude()
        if mag == 0:
            return Vector2D(0, 0)
        return Vector2D(self.x / mag, self.y / mag)

    def distance_to(self, other):
        """Calcula a distância até outro vetor"""
        return (self - other).magnitude()

    def manhattan_distance_to(self, other):
        """
        Calcula a distância Manhattan até outro vetor
        
        A distância Manhattan é a soma das diferenças absolutas
        das coordenadas, simulando movimento apenas ortogonal
        (como caminhar pelas ruas de uma cidade em grade).
        
        É mais adequada para jogos de labirinto onde o movimento
        diagonal não é permitido.
        
        Args:
            other: Vector2D de destino
            
        Returns:
            float: Distância Manhattan entre os pontos
        """
        if isinstance(other, Vector2D):
            return abs(self.x - other.x) + abs(self.y - other.y)
        elif isinstance(other, tuple) and len(other) == 2:
            return abs(self.x - other[0]) + abs(self.y - other[1])
        raise TypeError("Operando deve ser Vector2D ou tupla (x, y)")

    def to_tuple(self):
        """Converte o vetor para um tuple"""
        return (self.x, self.y)

    def copy(self):
        """Retorna uma cópia do vetor"""
        return Vector2D(self.x, self.y)

class AStarNode:
    """
    Nó para o algoritmo A* - representa uma posição no grid
    """
    def __init__(self, position, g_cost=0, h_cost=0, parent=None):
        self.position = position  # Vector2D
        self.g_cost = g_cost     # Custo real do início até este nó
        self.h_cost = h_cost     # Heurística (estimativa até o objetivo)
        self.f_cost = g_cost + h_cost  # Custo total
        self.parent = parent     # Nó pai (para reconstruir o caminho)
    
    def __lt__(self, other):
        """Comparação para heap/priority queue"""
        return self.f_cost < other.f_cost
    
    def __eq__(self, other):
        """Igualdade baseada na posição"""
        return self.position == other.position

class AStar:
    """
    Implementação do algoritmo A* para pathfinding em labirintos
    """
    
    @staticmethod
    def heuristic(pos1, pos2, heuristic_type="manhattan"):
        """
        Calcula a heurística entre duas posições
        
        Args:
            pos1, pos2: Vector2D das posições
            heuristic_type: "manhattan", "euclidean", ou "diagonal"
        """
        if heuristic_type == "manhattan":
            return abs(pos1.x - pos2.x) + abs(pos1.y - pos2.y)
        elif heuristic_type == "euclidean":
            return pos1.distance_to(pos2)
        elif heuristic_type == "diagonal":
            # Distância de Chebyshev (permite movimento diagonal)
            return max(abs(pos1.x - pos2.x), abs(pos1.y - pos2.y))
        else:
            return pos1.manhattan_distance_to(pos2)
    
    @staticmethod
    def get_neighbors(position, cell_size=16):
        """
        Retorna posições vizinhas (UP, DOWN, LEFT, RIGHT)
        
        Args:
            position: Vector2D da posição atual
            cell_size: Tamanho da célula do grid
        """
        neighbors = []
        directions = [(0, -cell_size), (0, cell_size), (-cell_size, 0), (cell_size, 0)]  # UP, DOWN, LEFT, RIGHT
        
        for dx, dy in directions:
            neighbor_pos = Vector2D(position.x + dx, position.y + dy)
            neighbors.append(neighbor_pos)
        
        return neighbors
    
    @staticmethod
    def find_path(start, goal, game_map, heuristic_type="manhattan"):
        """
        Encontra o caminho mais curto usando A*
        
        Args:
            start: Vector2D posição inicial
            goal: Vector2D posição objetivo
            game_map: Instância do mapa para verificar colisões
            heuristic_type: Tipo de heurística a usar
        
        Returns:
            List[Vector2D]: Lista de posições do caminho (vazia se não houver caminho)
        """
        import heapq
        
        # Listas de nós
        open_list = []  # Nós a serem explorados
        closed_list = set()  # Nós já explorados
        
        # Nó inicial
        start_node = AStarNode(
            position=start,
            g_cost=0,
            h_cost=AStar.heuristic(start, goal, heuristic_type)
        )
        
        heapq.heappush(open_list, start_node)
        
        # Dicionário para rastrear melhor custo para cada posição
        best_costs = {(start.x, start.y): 0}
        
        while open_list:
            # Pega o nó com menor f_cost
            current_node = heapq.heappop(open_list)
            current_pos_key = (current_node.position.x, current_node.position.y)
            
            # Se chegou ao objetivo
            if current_node.position.distance_to(goal) < 8:  # Tolerância de 8 pixels
                return AStar.reconstruct_path(current_node)
            
            # Adiciona à lista fechada
            closed_list.add(current_pos_key)
            
            # Examina vizinhos
            for neighbor_pos in AStar.get_neighbors(current_node.position):
                neighbor_key = (neighbor_pos.x, neighbor_pos.y)
                
                # Pula se já foi explorado
                if neighbor_key in closed_list:
                    continue
                
                # Pula se é parede
                if not game_map.is_valid_position(neighbor_pos, 16, "ghost"):
                    continue
                
                # Calcula custos
                g_cost = current_node.g_cost + 16  # Custo de movimento (1 célula)
                h_cost = AStar.heuristic(neighbor_pos, goal, heuristic_type)
                
                # Se encontrou um caminho melhor para este vizinho
                if neighbor_key not in best_costs or g_cost < best_costs[neighbor_key]:
                    best_costs[neighbor_key] = g_cost
                    
                    neighbor_node = AStarNode(
                        position=neighbor_pos,
                        g_cost=g_cost,
                        h_cost=h_cost,
                        parent=current_node
                    )
                    
                    heapq.heappush(open_list, neighbor_node)
        
        # Não encontrou caminho
        return []
    
    @staticmethod
    def reconstruct_path(node):
        """
        Reconstrói o caminho a partir do nó final
        
        Args:
            node: AStarNode final
        
        Returns:
            List[Vector2D]: Caminho do início ao fim
        """
        path = []
        current = node
        
        while current:
            path.append(current.position.copy())
            current = current.parent
        
        path.reverse()  # Inverte para ter o caminho do início ao fim
        return path 