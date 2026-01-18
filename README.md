# 🎮 Pac-Man OO - Projeto Orientado a Objetos

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen.svg)

**🎯 Um jogo Pac-Man completo implementado em Python com arquitetura orientada a objetos avançada**

</div>

---

## 🌟 Destaques do Projeto

- **🎨 Interface Moderna** - Design responsivo que se adapta a qualquer resolução
- **🧠 IA Inteligente** - Fantasmas com pathfinding A* e comportamentos únicos
- **🎵 Sistema de Áudio Completo** - 18 efeitos sonoros e trilhas musicais
- **🗺️ 10 Mapas Únicos** - Campanha progressiva com dificuldade escalável
- **🏆 Sistema de High Scores** - Persistência de recordes
- **⚡ Performance Otimizada** - 60 FPS com renderização eficiente

---

## 🚀 Demonstração Rápida

```bash
# Clone o repositório
git clone https://github.com/carlosperfil/Projeto-OO-pacman.git
cd Projeto-OO-pacman

# Instale as dependências
pip install -r requirements.txt

# Execute o jogo
python main.py
```

---

## 🎮 Como Jogar

| Controle | Ação |
|----------|------|
| **↑↓←→** | Mover Pac-Man |
| **ESC** | Pausar / Voltar |
| **ENTER** | Confirmar / Selecionar |
| **WASD** | Movimento alternativo |

---

## 🏗️ Arquitetura do Projeto

### 📁 Estrutura de Classes

```
📦 Projeto-OO-pacman
├── 🎯 GameObject (Classe Base Abstrata)
│   ├── 🚶 MovableObject
│   │   ├── 👤 Player (Pac-Man)
│   │   └── 👻 Ghost (IA dos Fantasmas)
│   └── ⚪ Pellet (Pontos)
├── 🗺️ Map (Sistema de Mapas)
├── 🎨 SpriteManager (Gerenciamento Visual)
├── 🎵 SoundManager (Sistema de Áudio)
└── 🛠️ Utils (Vector2D, Direction, A*)
```

### 🧠 Sistema de IA dos Fantasmas

Cada fantasma tem personalidade única:

| Fantasma | Comportamento | IA Strategy |
|----------|---------------|-------------|
| **🔴 Blinky** | Perseguidor Direto | A* Agressivo |
| **🩷 Pinky** | Interceptador | Predição de Movimento |
| **🔵 Inky** | Estratégico | Coordenação com Blinky |
| **🟡 Clyde** | Imprevisível | Alternância Perseguição/Fuga |

---

## 🎨 Recursos Visuais

- **Sprites Animados** - 9 frames do Pac-Man + 4 tipos de fantasmas
- **Efeitos Visuais** - Glow durante power-up, animações suaves
- **Interface Responsiva** - Escala automática para qualquer tela
- **HUD Informativo** - Score, vidas, mapa atual

---

## 🎵 Sistema de Áudio

| Categoria | Sons | Descrição |
|-----------|------|-----------|
| **🎼 Música** | 3 tracks | Menu, gameplay, créditos |
| **🍽️ Efeitos** | 8 sons | Comer pellets, frutas, fantasmas |
| **👻 Fantasmas** | 5 sons | Movimento, vulnerabilidade |
| **🎮 Interface** | 2 sons | Menu, game over |

---

## 🗺️ Sistema de Mapas

### Campanha Progressiva (10 Mapas)

| Mapa | Dificuldade | Características |
|------|-------------|-----------------|
| **Narrow Corridors** | 20/200 | Corredores estreitos |
| **Twisted Paths** | 30/200 | Caminhos sinuosos |
| **Complex Chambers** | 40/200 | Câmaras complexas |
| **Spiral Trap** | 50/200 | Armadilha espiral |
| **Narrow Escape** | 60/200 | Fuga estreita |
| **Death Maze** | 70/200 | Labirinto mortal |
| **Nightmare Zone** | 80/200 | Zona pesadelo |
| **Inferno Challenge** | 90/200 | Desafio infernal |
| **Classic Pac-Man** | 100/200 | Clássico original |
| **Ultimate Nightmare** | 100/200 | Pesadelo final |

---

## 🛠️ Tecnologias Utilizadas

- **🐍 Python 3.8+** - Linguagem principal
- **🎮 Pygame 2.5+** - Framework de jogos
- **🧮 A* Algorithm** - Pathfinding inteligente
- **🎨 JSON** - Sistema de mapas dinâmico
- **🎵 SDL2** - Sistema de áudio avançado

---

## 📊 Métricas do Projeto

- **📁 793 linhas** de código Python
- **🎨 18 arquivos** de áudio
- **🖼️ 40+ sprites** animados
- **🗺️ 10 mapas** únicos
- **🧠 4 personalidades** de IA
- **⚡ 60 FPS** garantidos

---

## 🎯 Funcionalidades Avançadas

### 🧠 Sistema de Dificuldade Dinâmica
- Ajuste automático baseado no mapa
- IA mais agressiva em níveis altos
- Velocidade escalável dos fantasmas

### 🎮 Sistema de Modos
- **Campanha** - Progressão por 10 mapas
- **Arcade** - Mapa único com vidas infinitas
- **Time Trial** - Modo contra o tempo

### 🏆 Sistema de Recordes
- Persistência em JSON
- Top 10 scores
- Nomes personalizados

---

## 🚀 Como Contribuir

1. **Fork** o projeto
2. **Clone** seu fork
3. **Crie** uma branch para sua feature
4. **Commit** suas mudanças
5. **Push** para a branch
6. **Abra** um Pull Request

---

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

<div align="center">

### ⭐ Se este projeto te ajudou, considere dar uma estrela!

**🎮 Divirta-se jogando!**

</div> 
