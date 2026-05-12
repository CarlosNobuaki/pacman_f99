# GUIA DE SPRITES

Este arquivo explica como adicionar sprites personalizados ao jogo Pac-Man.

## 🎨 Opção 1: Usar Sprites do Spriters Resource

**Website**: https://www.spriters-resource.com/browser_games/

### Passo a passo:

1. **Acesse o site** e procure por:
   - "Pac-Man" → Complete sheets
   - "Arcade Pac-Man" 
   - Você vai encontrar spritesheet completo com Pac-Man, fantasmas e tiles

2. **Extraia a imagem do Pac-Man**:
   - Tamanho recomendado: 32x32 pixels
   - Se a imagem for maior, redimensione usando:
     - Photoshop, GIMP, Paint.NET
     - Python: `from PIL import Image; Image.open('original.png').resize((32,32)).save("jogador.png")`

3. **Renomeie e salve**:
   ```
   pacman/
   ├── pacman.py
   └── jogador.png  ← Cole aqui
   ```

## 🎨 Opção 2: Gerar Sprites com Python

Se preferir gerar sprites simples em código:

```python
import pygame

# Criar um sprite Pac-Man amarelo com 'boca'
def criar_pacman():
    img = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(img, (255, 255, 0), (16, 16), 14)
    # Desenha a "boca" (triângulo)
    pygame.draw.polygon(img, (0, 0, 0), [(16, 16), (20, 10), (20, 22)])
    return img

# Criar um fantasma simples
def criar_fantasma():
    img = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.rect(img, (255, 0, 0), (8, 8, 16, 16))  # Corpo
    pygame.draw.circle(img, (255, 0, 0), (12, 8), 4)     # Cabeça esquerda
    pygame.draw.circle(img, (255, 0, 0), (20, 8), 4)     # Cabeça direita
    pygame.draw.circle(img, (255, 255, 255), (10, 12), 2) # Olho
    pygame.draw.circle(img, (255, 255, 255), (18, 12), 2)
    return img
```

## 🎨 Opção 3: Formatos Aceitos

O jogo aceita qualquer imagem que Pygame suporte:
- ✅ PNG (recomendado - suporta transparência)
- ✅ JPG
- ✅ BMP
- ✅ GIF (primeira frame)

## 📏 Requisitos Técnicos

- **Tamanho ideal**: 32x32 pixels
- **Transparência**: Recomendado usar PNG com transparência
- **Cores**: RGB ou RGBA
- **Caso o arquivo não tenha 32x32**: Será automaticamente redimensionado

## 🚀 Como Adicionar ao Jogo

### Método 1: Colocando os arquivos

```bash
# Coloque os 3 arquivos de sprite na mesma pasta de pacman.py
cp jogador.png /Users/carlosnobuaki/pacman/
cp fantasma.png /Users/carlosnobuaki/pacman/
cp parede.png /Users/carlosnobuaki/pacman/

# Execute o jogo - detectará automaticamente!
python3 pacman.py
```

### Método 2: Customizar os caminhos no código

Edite `pacman.py` e mude estas linhas:

```python
# Linha ~30
try:
    img_pacman = pygame.image.load("jogador.png").convert_alpha()
    img_fantasma = pygame.image.load("fantasma.png").convert_alpha()
    img_parede = pygame.image.load("parede.png").convert_alpha()
```

Para outros caminhos:

```python
img_pacman = pygame.image.load("/path/para/seu/pacman.png").convert_alpha()
```

## 🎨 Dicas de Sprite Design

### Para Pac-Man:
- Círculo amarelo com 'boca' triangular aberta
- Diferentes frames para animação (boca aberta/fechada)
- Nível de detalhe: simples e legível

### Para Fantasmas:
- Forma de manto/fantasma (quadrado com ponta em cima)
- Olhos brancos e pupilas pretas
- 4 cores diferentes:
  - Vermelho (Blinky)
  - Rosa (Pinky)
  - Ciano (Inky)
  - Laranja (Clyde)

### Para Paredes:
- Quadrados ou tijolos azuis/cinzas
- Padrão repetível 32x32
- Bom contraste com o fundo preto

## 📂 Estrutura Recomendada

```
pacman/
├── pacman.py
├── audio.py
├── setup.py
├── README.md
├── requirements.txt
├── sprites/          ← Diretório opcional
│   ├── pacman/
│   │   ├── closed.png
│   │   └── open.png
│   ├── ghosts/
│   │   ├── red.png
│   │   ├── pink.png
│   │   ├── cyan.png
│   │   └── orange.png
│   └── tiles/
│       └── wall.png
└── levels/           ← Diretório opcional para mapas
    └── level1.txt
```

## 🔗 Outros Recursos

- **OpenGameArt**: https://opengameart.org/
- **Itch.io**: https://itch.io/game-assets/free
- **Game-icons.net**: https://game-icons.net/
- **Lee Zion Sprites**: Busque por "retro pixel art sprites"

## ❓ Troubleshooting

**Problema**: Sprite não aparece
- Solução: Verifique exatamente o nome do arquivo (case-sensitive em Linux/Mac)

**Problema**: Jogo fica lento com sprites grandes
- Solução: Redimensione para 32x32 pixels

**Problema**: Cores estranhas
- Solução: Converta para PNG com transparency, ou use .convert_alpha() no pygame

**Problema**: "Usará quadrados coloridos"
- Solução: Coloque os 3 arquivos PNG na mesma pasta que pacman.py

---

Bom divertimento! 🎮
