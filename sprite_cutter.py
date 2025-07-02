import pygame
import sys
import os

class SpriteCutter:
    def __init__(self, sprite_sheet_path):
        pygame.init()
        
        # Carrega a sprite sheet
        self.sprite_sheet = pygame.image.load(sprite_sheet_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.get_size()
        
        # Configurações da janela
        self.window_width = 800
        self.window_height = 600
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Sprite Cutter - 16x16")
        
        # Configurações do quadrado de seleção
        self.sprite_size = 16
        self.selection_x = 0
        self.selection_y = 0
        
        # Controle de movimento - para evitar movimento rápido
        self.key_delay = 150  # Delay em milissegundos
        self.key_repeat_delay = 50  # Delay para repetição
        self.last_key_time = 0
        self.keys_pressed = set()
        
        # Cores
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.GREEN = (0, 255, 0)
        self.BLUE = (0, 0, 255)
        self.YELLOW = (255, 255, 0)
        
        # Fonte
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # Estado
        self.running = True
        self.clock = pygame.time.Clock()
        
        # Lista de sprites recortados
        self.cut_sprites = []
        
    def handle_events(self):
        """Processa eventos do teclado e mouse"""
        current_time = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                    
                # Adiciona tecla ao conjunto de teclas pressionadas
                self.keys_pressed.add(event.key)
                
                # Recortar sprite atual
                if event.key == pygame.K_SPACE:
                    self.cut_current_sprite()
                    
                # Salvar todos os sprites recortados
                elif event.key == pygame.K_s:
                    self.save_all_sprites()
                    
                # Limpar lista de sprites recortados
                elif event.key == pygame.K_c:
                    self.cut_sprites.clear()
                    
            elif event.type == pygame.KEYUP:
                # Remove tecla do conjunto quando solta
                self.keys_pressed.discard(event.key)
        
        # Processa movimento das setas com controle de tempo
        if current_time - self.last_key_time > self.key_delay:
            moved = False
            
            # Verifica se alguma seta está pressionada
            if pygame.K_LEFT in self.keys_pressed:
                if self.selection_x > 0:
                    self.selection_x -= 1
                    moved = True
            elif pygame.K_RIGHT in self.keys_pressed:
                if self.selection_x < self.sheet_width - self.sprite_size:
                    self.selection_x += 1
                    moved = True
            elif pygame.K_UP in self.keys_pressed:
                if self.selection_y > 0:
                    self.selection_y -= 1
                    moved = True
            elif pygame.K_DOWN in self.keys_pressed:
                if self.selection_y < self.sheet_height - self.sprite_size:
                    self.selection_y += 1
                    moved = True
            
            # Se moveu, atualiza o tempo e ajusta o delay
            if moved:
                self.last_key_time = current_time
                # Reduz o delay para repetição mais rápida após o primeiro movimento
                self.key_delay = self.key_repeat_delay
            else:
                # Reseta o delay quando nenhuma tecla está pressionada
                self.key_delay = 150
                    
    def cut_current_sprite(self):
        """Recorta o sprite na posição atual do quadrado de seleção"""
        # Cria uma superfície para o sprite recortado
        sprite_surface = pygame.Surface((self.sprite_size, self.sprite_size), pygame.SRCALPHA)
        
        # Copia a região selecionada da sprite sheet
        sprite_surface.blit(self.sprite_sheet, (0, 0), 
                           (self.selection_x, self.selection_y, self.sprite_size, self.sprite_size))
        
        # Adiciona à lista de sprites recortados
        sprite_info = {
            'surface': sprite_surface,
            'x': self.selection_x,
            'y': self.selection_y
        }
        self.cut_sprites.append(sprite_info)
        
        print(f"Sprite recortado na posição ({self.selection_x}, {self.selection_y})")
        
    def save_all_sprites(self):
        """Salva todos os sprites recortados como arquivos PNG"""
        if not self.cut_sprites:
            print("Nenhum sprite para salvar!")
            return
            
        # Cria pasta para salvar os sprites
        output_dir = "sprites_cortados"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for i, sprite_info in enumerate(self.cut_sprites):
            filename = f"{output_dir}/sprite_{i+1:03d}_x{sprite_info['x']}_y{sprite_info['y']}.png"
            pygame.image.save(sprite_info['surface'], filename)
            
        print(f"{len(self.cut_sprites)} sprites salvos na pasta '{output_dir}'")
        
    def draw(self):
        """Desenha a interface"""
        self.screen.fill(self.BLACK)
        
        # Desenha a sprite sheet
        self.screen.blit(self.sprite_sheet, (10, 10))
        
        # Desenha o quadrado de seleção
        selection_rect = pygame.Rect(
            10 + self.selection_x, 
            10 + self.selection_y, 
            self.sprite_size, 
            self.sprite_size
        )
        pygame.draw.rect(self.screen, self.RED, selection_rect, 2)
        
        # Desenha uma borda mais grossa para destacar
        pygame.draw.rect(self.screen, self.YELLOW, selection_rect, 1)
        
        # Desenha informações
        info_x = self.sheet_width + 30
        
        # Informações da posição
        pos_text = self.font.render(f"Posição: ({self.selection_x}, {self.selection_y})", True, self.WHITE)
        self.screen.blit(pos_text, (info_x, 20))
        
        # Informações da sprite sheet
        sheet_text = self.font.render(f"Sprite Sheet: {self.sheet_width}x{self.sheet_height}", True, self.WHITE)
        self.screen.blit(sheet_text, (info_x, 50))
        
        # Controles
        controls_y = 100
        controls = [
            "Controles:",
            "Setas - Mover seleção",
            "Espaço - Recortar sprite",
            "S - Salvar todos",
            "C - Limpar lista",
            "ESC - Sair"
        ]
        
        for i, control in enumerate(controls):
            color = self.YELLOW if i == 0 else self.WHITE
            control_text = self.font.render(control, True, color)
            self.screen.blit(control_text, (info_x, controls_y + i * 25))
        
        # Lista de sprites recortados
        sprites_y = 250
        sprites_text = self.font.render(f"Sprites recortados: {len(self.cut_sprites)}", True, self.GREEN)
        self.screen.blit(sprites_text, (info_x, sprites_y))
        
        # Mostra os últimos sprites recortados
        sprites_y += 30
        for i, sprite_info in enumerate(self.cut_sprites[-5:]):  # Mostra apenas os últimos 5
            sprite_text = self.small_font.render(
                f"{i+1}: ({sprite_info['x']}, {sprite_info['y']})", True, self.WHITE
            )
            self.screen.blit(sprite_text, (info_x, sprites_y + i * 20))
            
            # Desenha uma miniatura do sprite
            mini_sprite = pygame.transform.scale(sprite_info['surface'], (8, 8))
            self.screen.blit(mini_sprite, (info_x + 120, sprites_y + i * 20))
        
        # Preview do sprite atual
        preview_y = 400
        preview_text = self.font.render("Preview:", True, self.WHITE)
        self.screen.blit(preview_text, (info_x, preview_y))
        
        # Cria preview do sprite atual
        preview_surface = pygame.Surface((self.sprite_size, self.sprite_size), pygame.SRCALPHA)
        preview_surface.blit(self.sprite_sheet, (0, 0), 
                            (self.selection_x, self.selection_y, self.sprite_size, self.sprite_size))
        
        # Desenha o preview ampliado
        preview_rect = pygame.Rect(info_x, preview_y + 30, self.sprite_size * 4, self.sprite_size * 4)
        pygame.draw.rect(self.screen, self.BLACK, preview_rect)
        pygame.draw.rect(self.screen, self.WHITE, preview_rect, 1)
        
        # Amplia o sprite para o preview
        enlarged_sprite = pygame.transform.scale(preview_surface, (self.sprite_size * 4, self.sprite_size * 4))
        self.screen.blit(enlarged_sprite, (info_x, preview_y + 30))
        
    def run(self):
        """Loop principal"""
        while self.running:
            self.handle_events()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
            
        pygame.quit()
        sys.exit()

def main():
    """Função principal"""
    if len(sys.argv) != 2:
        print("Uso: python sprite_cutter.py <caminho_para_sprite_sheet>")
        print("Exemplo: python sprite_cutter.py assets/sprites/spritesheet.png")
        return
        
    sprite_sheet_path = sys.argv[1]
    
    if not os.path.exists(sprite_sheet_path):
        print(f"Erro: Arquivo '{sprite_sheet_path}' não encontrado!")
        return
        
    try:
        cutter = SpriteCutter(sprite_sheet_path)
        cutter.run()
    except Exception as e:
        print(f"Erro ao executar o programa: {e}")
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main() 