# Diagrama de Classes - Pac-Man OO

Este diagrama mostra a arquitetura completa do projeto Pac-Man orientado a objetos, incluindo todas as classes, interfaces, enumerações e suas relações.

## Arquitetura Geral

O projeto segue uma arquitetura orientada a objetos bem estruturada com:

- **Hierarquia de Herança**: GameObject → MovableObject → (Player, Ghost)
- **Padrões Singleton**: SpriteManager, SoundManager  
- **Composição e Agregação**: Game compõe Player, Ghosts, Pellets, Map
- **Enumerações**: Direction, GameState, SoundType
- **Classes Utilitárias**: Vector2D, AStar, AStarNode

## Diagrama UML

```mermaid
classDiagram
    %% Classe abstrata base
    class GameObject {
        <<abstract>>
        -Vector2D _position
        -tuple _color
        -int _size
        -int _animation_frame
        +position : Vector2D
        +color : tuple
        +size : int
        +get_rect() Rect
        +draw(screen)* void
        +update(delta_time)* void
    }

    %% Classe base para objetos móveis
    class MovableObject {
        -float _speed
        -Direction _direction
        -Direction _next_direction
        +speed : float
        +direction : Direction
        +can_move(direction, game_map, entity_type) bool
        +move(direction) void
    }

    %% Jogador
    class Player {
        -int _lives
        -int _score
        -bool _power_up_active
        -int _power_up_timer
        -int _power_up_duration
        +lives : int
        +score : int
        +power_up_active : bool
        +eat_pellet(pellet_value) void
        +activate_power_up() void
        +lose_life() void
        +draw(screen) void
        +update(delta_time, game_map) void
    }

    %% Fantasma
    class Ghost {
        -str _state
        -Vector2D _initial_position
        -str _ghost_type
        -int _vulnerable_timer
        -Vector2D _target_position
        -str _current_mode
        -list _current_path
        -float _difficulty_multiplier
        -bool _is_in_spawn_delay
        +state : str
        +is_in_spawn_delay : bool
        +spawn_delay_remaining : float
        +set_vulnerable(duration) void
        +set_difficulty(difficulty_level) void
        +reset_position() void
        +get_target_position(player_pos, player_dir, other_ghosts) Vector2D
        +draw(screen) void
        +update(delta_time, player_pos, player_dir, game_map, other_ghosts) void
    }

    %% Pellet
    class Pellet {
        -str _type
        -int _value
        +type : str
        +value : int
        +be_eaten() int
        +draw(screen) void
        +update(delta_time) void
    }

    %% Mapa
    class Map {
        -list _layout
        -int _cell_size
        -int _width
        -int _height
        -dict _metadata
        -dict _spawn_positions
        -str _original_map_path
        +layout : list
        +cell_size : int
        +width : int
        +height : int
        +metadata : dict
        +difficulty : int
        +load_from_json(file_path) bool
        +get_pellets() list
        +get_spawn_position(entity_type) Vector2D
        +is_wall(position) bool
        +is_valid_position(position, object_size, type) bool
        +remove_pellet_at(position) bool
        +count_pellets() int
        +draw(screen) void
        +get_available_maps()$ list
    }

    %% Gerenciador de Sprites
    class SpriteManager {
        <<singleton>>
        -dict _sprites
        -int _sprite_size
        +sprite_size : int
        -_load_sprite(path) Surface
        -_create_default_sprite() Surface
        -_load_all_sprites() void
        +get_pacman_sprite(direction, animation_frame) Surface
        +get_ghost_sprite(ghost_type, direction, animation_frame, state) Surface
        +get_pellet_sprite(pellet_type, animation_frame) Surface
    }

    %% Gerenciador de Sons
    class SoundManager {
        <<singleton>>
        -dict _sounds
        -dict _volumes
        -list _effect_channels
        -Channel _music_channel
        -dict _sound_types
        +play_sound(sound_name, volume) bool
        +stop_sound(sound_name) bool
        +set_volume(sound_type, volume) bool
        +get_volume(sound_type) float
        +stop_all_sounds() void
        +pause_all_sounds() void
        +unpause_all_sounds() void
    }

    %% Jogo principal
    class Game {
        -int _width
        -int _height
        -Surface _screen
        -Clock _clock
        -GameState _state
        -Player _player
        -list _ghosts
        -list _pellets
        -Map _map
        -HighScoreManager _highscore_manager
        -list _available_maps
        -int _current_map_index
        -int _campaign_total_score
        +state : GameState
        +process_events() bool
        +update(delta_time) void
        +render() void
        +run() void
        -_initialize_game() void
        -_reset_game() void
        -_draw_hud() void
    }

    %% Gerenciador de Pontuações
    class HighScoreManager {
        -str filename
        -list highscores
        +load_highscores() list
        +save_highscores() void
        +add_score(name, score) void
    }

    %% Classes utilitárias
    class Vector2D {
        +float x
        +float y
        +__add__(other) Vector2D
        +__sub__(other) Vector2D
        +__mul__(scalar) Vector2D
        +magnitude() float
        +normalize() Vector2D
        +distance_to(other) float
        +manhattan_distance_to(other) float
        +copy() Vector2D
    }

    class AStarNode {
        +Vector2D position
        +float g_cost
        +float h_cost
        +float f_cost
        +AStarNode parent
    }

    class AStar {
        +heuristic(pos1, pos2, heuristic_type)$ float
        +get_neighbors(position, cell_size)$ list
        +find_path(start, goal, game_map, heuristic_type)$ list
        +reconstruct_path(node)$ list
    }

    %% Enumerações
    class Direction {
        <<enumeration>>
        UP
        DOWN
        LEFT
        RIGHT
        NONE
    }

    class GameState {
        <<enumeration>>
        MENU
        PLAYING
        GAME_OVER
        PAUSED
        VICTORY
        OPTIONS
        HISTORY
        INTERMISSION
    }

    class SoundType {
        <<enumeration>>
        EFFECT
        MUSIC
        UI
        GHOST
    }

    %% Relações de Herança
    GameObject <|-- MovableObject
    MovableObject <|-- Player
    MovableObject <|-- Ghost
    GameObject <|-- Pellet

    %% Relações de Composição e Agregação
    Game *-- Player : "1"
    Game *-- "4" Ghost : "ghosts"
    Game *-- "*" Pellet : "pellets"
    Game *-- Map : "1"
    Game *-- HighScoreManager : "1"
    Game ..> SpriteManager : "uses"
    Game ..> SoundManager : "uses"

    %% Dependências das classes de jogo
    Player ..> Vector2D : "uses"
    Ghost ..> Vector2D : "uses"
    Ghost ..> AStar : "uses pathfinding"
    Pellet ..> Vector2D : "uses"
    Map ..> Vector2D : "uses"

    %% Dependências com enums
    Player ..> Direction : "uses"
    Ghost ..> Direction : "uses"
    Game ..> GameState : "uses"
    SoundManager ..> SoundType : "uses"

    %% Relações com classes utilitárias
    AStar ..> AStarNode : "creates"
    AStar ..> Vector2D : "uses"
    AStarNode ..> Vector2D : "uses"

    %% Dependências dos Managers
    SpriteManager ..> Direction : "uses"
    Player ..> SpriteManager : "gets sprites"
    Ghost ..> SpriteManager : "gets sprites"
    Pellet ..> SpriteManager : "gets sprites"
    
    Game ..> SoundType : "uses"
    Player ..> SoundManager : "plays sounds"
    Ghost ..> SoundManager : "plays sounds"
```

## Principais Conceitos OO Demonstrados

### 1. **Herança**
- `GameObject` → `MovableObject` → `Player`, `Ghost`
- `GameObject` → `Pellet`
- Hierarquia clara com especialização progressiva

### 2. **Abstração**
- `GameObject` como classe abstrata com métodos abstratos `draw()` e `update()`
- Interface comum para todos os objetos do jogo

### 3. **Encapsulamento**
- Atributos privados (prefixo `_`) com properties para acesso controlado
- Métodos privados para funcionalidades internas

### 4. **Polimorfismo**
- Implementações específicas de `draw()` e `update()` em cada classe
- Comportamentos únicos mantendo interface comum

### 5. **Composição**
- `Game` compõe `Player`, `Ghost[]`, `Pellet[]`, `Map`
- Relacionamento "tem-um" forte

### 6. **Padrão Singleton**
- `SpriteManager` e `SoundManager` como instâncias únicas globais
- Garantia de um único ponto de acesso aos recursos

### 7. **Dependency Injection**
- Classes recebem dependências através de parâmetros
- Baixo acoplamento entre componentes

## Benefícios da Arquitetura

- **Manutenibilidade**: Código organizado e modular
- **Extensibilidade**: Fácil adição de novos tipos de objetos
- **Reusabilidade**: Classes base reutilizáveis
- **Testabilidade**: Componentes isolados e testáveis
- **Performance**: Singletons evitam recarregamento de recursos 