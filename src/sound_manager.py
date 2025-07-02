import pygame
import os
import time
from enum import Enum
from typing import Dict, Optional, List

class SoundType(Enum):
    """Enum para categorizar diferentes tipos de som"""
    EFFECT = "effect"      # Efeitos sonoros (comer pellet, power-up, etc.)
    MUSIC = "music"        # Música de fundo
    UI = "ui"             # Sons de interface (menu, game over, etc.)
    GHOST = "ghost"       # Sons específicos dos fantasmas

class SoundManager:
    """
    Gerenciador de sons para o jogo Pac-Man.
    
    Controla e manipula volumes individualmente para diferentes tipos de som,
    previne sobreposição indesejada e segue boas práticas de OO.
    """
    
    def __init__(self):
        """Inicializa o gerenciador de sons"""
        # Inicializa o mixer do Pygame
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            print("Mixer do Pygame inicializado com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar mixer do Pygame: {e}")
            return
        
        self._sounds: Dict[str, pygame.mixer.Sound] = {}
        self._music_channel: Optional[pygame.mixer.Channel] = None
        self._effect_channels: List[pygame.mixer.Channel] = []
        self._ui_channel: Optional[pygame.mixer.Channel] = None
        self._ghost_channel: Optional[pygame.mixer.Channel] = None
        
        # Volumes individuais para cada tipo de som
        self._volumes = {
            SoundType.EFFECT: 0.7,
            SoundType.MUSIC: 0.5,
            SoundType.UI: 0.8,
            SoundType.GHOST: 0.6
        }
        
        # Controle de sobreposição - armazena último tempo de reprodução
        self._last_play_times: Dict[str, float] = {}
        self._min_interval = 0.5 # Intervalo mínimo entre reproduções (segundos)
        
        # Mapeamento de sons para seus tipos
        self._sound_types = {
            # Efeitos sonoros
            "eating": SoundType.EFFECT,
            "eating-ghost": SoundType.EFFECT,
            "eating-fruit": SoundType.EFFECT,
            "extend": SoundType.EFFECT,
            
            # Música
            "music_menu": SoundType.MUSIC,
            "coffee-break-music": SoundType.MUSIC,
            "credit": SoundType.MUSIC,
            
            # Interface
            "miss": SoundType.UI,
            
            # Fantasmas
            "ghost-normal-move": SoundType.GHOST,
            "ghost-spurt-move-1": SoundType.GHOST,
            "ghost-spurt-move-2": SoundType.GHOST,
            "ghost-spurt-move-3": SoundType.GHOST,
            "ghost-spurt-move-4": SoundType.GHOST,
            "ghost-return-to-home": SoundType.GHOST,
            "ghost-turn-to-blue": SoundType.GHOST
        }
        
        self._initialize_channels()
        self._load_all_sounds()
    
    def _initialize_channels(self):
        """Inicializa os canais de áudio do Pygame"""
        try:
            # Reserva canais específicos para cada tipo de som
            pygame.mixer.set_reserved(4)  # Reserva 4 canais
            
            # Canais específicos
            self._music_channel = pygame.mixer.Channel(0)
            self._ui_channel = pygame.mixer.Channel(1)
            self._ghost_channel = pygame.mixer.Channel(2)
            
            # Canais para efeitos (múltiplos para sobreposição controlada)
            self._effect_channels = [
                pygame.mixer.Channel(3),
                pygame.mixer.Channel(4),
                pygame.mixer.Channel(5)
            ]
            
            print("Canais de áudio inicializados com sucesso")
        except Exception as e:
            print(f"Erro ao inicializar canais de áudio: {e}")
    
    def _load_all_sounds(self):
        """Carrega todos os sons disponíveis na pasta assets/sounds"""
        sounds_path = "assets/sounds"
        
        if not os.path.exists(sounds_path):
            print(f"Aviso: Pasta de sons não encontrada em {sounds_path}")
            return
        
        try:
            for filename in os.listdir(sounds_path):
                if filename.endswith(('.wav', '.mp3', '.ogg')):
                    sound_name = os.path.splitext(filename)[0]
                    file_path = os.path.join(sounds_path, filename)
                    
                    try:
                        sound = pygame.mixer.Sound(file_path)
                        self._sounds[sound_name] = sound
                        print(f"Som carregado: {sound_name}")
                    except Exception as e:
                        print(f"Erro ao carregar som {filename}: {e}")
            
            print(f"Total de sons carregados: {len(self._sounds)}")
        except Exception as e:
            print(f"Erro ao carregar sons: {e}")
    
    def _get_channel_for_sound(self, sound_name: str) -> Optional[pygame.mixer.Channel]:
        """Retorna o canal apropriado para um som específico"""
        sound_type = self._sound_types.get(sound_name, SoundType.EFFECT)
        
        if sound_type == SoundType.MUSIC:
            return self._music_channel
        elif sound_type == SoundType.UI:
            return self._ui_channel
        elif sound_type == SoundType.GHOST:
            return self._ghost_channel
        else:  # SoundType.EFFECT
            # Escolhe um canal de efeito disponível
            for channel in self._effect_channels:
                if not channel.get_busy():
                    return channel
            # Se todos estiverem ocupados, usa o primeiro
            return self._effect_channels[0] if self._effect_channels else None
    
    def _can_play_sound(self, sound_name: str) -> bool:
        """
        Verifica se um som pode ser reproduzido (evita sobreposição indesejada)
        """
        current_time = time.time()
        last_play_time = self._last_play_times.get(sound_name, 0)
        
        # Permite reprodução se passou tempo suficiente desde a última
        if current_time - last_play_time >= self._min_interval:
            self._last_play_times[sound_name] = current_time
            return True
        return False
    
    def play_sound(self, sound_name: str, volume: Optional[float] = None) -> bool:
        """
        Reproduz um som específico.
        
        Args:
            sound_name: Nome do som a ser reproduzido
            volume: Volume específico (opcional, usa volume padrão se não fornecido)
            
        Returns:
            bool: True se o som foi reproduzido com sucesso, False caso contrário
        """
        if sound_name not in self._sounds:
            print(f"Aviso: Som '{sound_name}' não encontrado")
            return False
        
        # Verifica se pode reproduzir (evita sobreposição)
        if not self._can_play_sound(sound_name):
            return False
        
        try:
            sound = self._sounds[sound_name]
            channel = self._get_channel_for_sound(sound_name)
            
            if channel is None:
                print(f"Erro: Nenhum canal disponível para {sound_name}")
                return False
            
            # Define o volume
            if volume is not None:
                sound.set_volume(volume)
            else:
                sound_type = self._sound_types.get(sound_name, SoundType.EFFECT)
                sound.set_volume(self._volumes[sound_type])
            
            # Reproduz o som
            channel.play(sound)
            return True
            
        except Exception as e:
            print(f"Erro ao reproduzir som {sound_name}: {e}")
            return False
    
    def stop_sound(self, sound_name: str) -> bool:
        """
        Para a reprodução de um som específico.
        
        Args:
            sound_name: Nome do som a ser parado
            
        Returns:
            bool: True se o som foi parado, False caso contrário
        """
        try:
            channel = self._get_channel_for_sound(sound_name)
            if channel and channel.get_busy():
                channel.stop()
                return True
            return False
        except Exception as e:
            print(f"Erro ao parar som {sound_name}: {e}")
            return False
    
    def pause_sound(self, sound_name: str) -> bool:
        """
        Pausa a reprodução de um som específico.
        
        Args:
            sound_name: Nome do som a ser pausado
            
        Returns:
            bool: True se o som foi pausado, False caso contrário
        """
        try:
            channel = self._get_channel_for_sound(sound_name)
            if channel and channel.get_busy():
                channel.pause()
                return True
            return False
        except Exception as e:
            print(f"Erro ao pausar som {sound_name}: {e}")
            return False
    
    def unpause_sound(self, sound_name: str) -> bool:
        """
        Despausa a reprodução de um som específico.
        
        Args:
            sound_name: Nome do som a ser despausado
            
        Returns:
            bool: True se o som foi despausado, False caso contrário
        """
        try:
            channel = self._get_channel_for_sound(sound_name)
            if channel:
                channel.unpause()
                return True
            return False
        except Exception as e:
            print(f"Erro ao despausar som {sound_name}: {e}")
            return False
    
    def set_volume(self, sound_type: SoundType, volume: float) -> bool:
        """
        Define o volume para um tipo específico de som.
        
        Args:
            sound_type: Tipo de som (EFFECT, MUSIC, UI, GHOST)
            volume: Volume entre 0.0 e 1.0
            
        Returns:
            bool: True se o volume foi definido, False caso contrário
        """
        if not 0.0 <= volume <= 1.0:
            print(f"Erro: Volume deve estar entre 0.0 e 1.0, recebido: {volume}")
            return False
        
        self._volumes[sound_type] = volume
        
        # Atualiza volume de todos os sons do tipo especificado
        for sound_name, sound in self._sounds.items():
            if self._sound_types.get(sound_name) == sound_type:
                sound.set_volume(volume)
        
        return True
    
    def set_sound_volume(self, sound_name: str, volume: float) -> bool:
        """
        Define o volume para um som específico.
        
        Args:
            sound_name: Nome do som
            volume: Volume entre 0.0 e 1.0
            
        Returns:
            bool: True se o volume foi definido, False caso contrário
        """
        if sound_name not in self._sounds:
            print(f"Erro: Som '{sound_name}' não encontrado")
            return False
        
        if not 0.0 <= volume <= 1.0:
            print(f"Erro: Volume deve estar entre 0.0 e 1.0, recebido: {volume}")
            return False
        
        try:
            self._sounds[sound_name].set_volume(volume)
            return True
        except Exception as e:
            print(f"Erro ao definir volume para {sound_name}: {e}")
            return False
    
    def get_volume(self, sound_type: SoundType) -> float:
        """
        Retorna o volume atual de um tipo de som.
        
        Args:
            sound_type: Tipo de som
            
        Returns:
            float: Volume atual (entre 0.0 e 1.0)
        """
        return self._volumes.get(sound_type, 0.5)
    
    def stop_all_sounds(self):
        """Para todos os sons em reprodução"""
        try:
            pygame.mixer.stop()
        except Exception as e:
            print(f"Erro ao parar todos os sons: {e}")
    
    def pause_all_sounds(self):
        """Pausa todos os sons em reprodução"""
        try:
            pygame.mixer.pause()
        except Exception as e:
            print(f"Erro ao pausar todos os sons: {e}")
    
    def unpause_all_sounds(self):
        """Despausa todos os sons"""
        try:
            pygame.mixer.unpause()
        except Exception as e:
            print(f"Erro ao despausar todos os sons: {e}")
    
    def is_sound_playing(self, sound_name: str) -> bool:
        """
        Verifica se um som específico está sendo reproduzido.
        
        Args:
            sound_name: Nome do som
            
        Returns:
            bool: True se o som está sendo reproduzido, False caso contrário
        """
        try:
            channel = self._get_channel_for_sound(sound_name)
            return channel is not None and channel.get_busy()
        except Exception as e:
            print(f"Erro ao verificar se {sound_name} está tocando: {e}")
            return False
    
    def get_available_sounds(self) -> List[str]:
        """
        Retorna lista de todos os sons disponíveis.
        
        Returns:
            List[str]: Lista com nomes dos sons carregados
        """
        return list(self._sounds.keys())
    
    def get_sound_type(self, sound_name: str) -> Optional[SoundType]:
        """
        Retorna o tipo de um som específico.
        
        Args:
            sound_name: Nome do som
            
        Returns:
            Optional[SoundType]: Tipo do som ou None se não encontrado
        """
        return self._sound_types.get(sound_name)
    
    def set_min_interval(self, interval: float):
        """
        Define o intervalo mínimo entre reproduções do mesmo som.
        
        Args:
            interval: Intervalo em segundos
        """
        if interval >= 0:
            self._min_interval = interval
        else:
            print("Erro: Intervalo deve ser maior ou igual a 0")
    
    def get_min_interval(self) -> float:
        """
        Retorna o intervalo mínimo atual entre reproduções.
        
        Returns:
            float: Intervalo em segundos
        """
        return self._min_interval

# Instância global do gerenciador de sons
sound_manager = SoundManager() 