"""
Módulo auxiliar para renderizar texto simples
Quando pygame.font não está disponível
"""
import pygame

class TextoSimples:
    """Renderiza texto simples usando pygame.draw"""
    
    def __init__(self, tamanho=24):
        self.tamanho = tamanho
        self.char_width = max(6, tamanho // 2)
        self.char_height = tamanho
        
    def render(self, texto, aa, cor):
        """
        Renderiza texto de forma simples
        Retorna uma Surface com o texto
        """
        largura = len(texto) * self.char_width
        altura = self.char_height
        
        surf = pygame.Surface((largura, altura), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        
        # Desenhar cada caractere como um símbolo simples
        x = 0
        for char in texto:
            self._desenhar_char(surf, char, x, 0, cor)
            x += self.char_width
        
        return surf
    
    def _desenhar_char(self, surf, char, x, y, cor):
        """Desenha um caractere simples"""
        tamanho = self.tamanho
        
        # Desenhar números e símbolos como blocos simples
        if char.isdigit():
            # Desenhar números como retângulo com diagonal
            pygame.draw.rect(surf, cor, (x + 1, y + 1, tamanho - 2, tamanho - 2), 1)
            pygame.draw.line(surf, cor, (x + 1, y + 1), (x + tamanho - 1, y + tamanho - 1), 1)
        elif char == ':':
            # Dois pontos
            pygame.draw.circle(surf, cor, (x + tamanho // 2, y + 4), 1)
            pygame.draw.circle(surf, cor, (x + tamanho // 2, y + tamanho - 4), 1)
        elif char == ' ':
            # Espaço em branco
            pass
        elif char == '!':
            pygame.draw.line(surf, cor, (x + tamanho // 2, y + 2), (x + tamanho // 2, y + tamanho - 4), 1)
            pygame.draw.circle(surf, cor, (x + tamanho // 2, y + tamanho - 2), 1)
        elif char == 'V':
            pygame.draw.line(surf, cor, (x + 1, y + 1), (x + tamanho // 2, y + tamanho - 1), 1)
            pygame.draw.line(surf, cor, (x + tamanho - 1, y + 1), (x + tamanho // 2, y + tamanho - 1), 1)
        else:
            # Caractere genérico: desenhar retângulo
            pygame.draw.rect(surf, cor, (x + 1, y + 1, tamanho - 2, tamanho - 2), 1)


def get_fonte(tamanho=24):
    """
    Retorna uma fonte ou um objeto TextoSimples como fallback
    """
    try:
        return pygame.font.Font(None, tamanho)
    except:
        return TextoSimples(tamanho)
