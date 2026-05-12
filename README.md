# 🎮 Pac-Man Game - Guia Completo

Um jogo Pac-Man totalmente funcional em Python com Pygame!

## 🚀 Como Executar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Executar o jogo
python3 pacman.py
```

## 🎮 Controles

- **Setas do Teclado**: Mover Pac-Man (← ↑ → ↓)
- **R**: Reiniciar após Game Over ou Vitória

## 🎯 Objetivo

- **Coma todos os pellets** (bolinhas amarelas) para vencer
- **Evite os fantasmas** (4 inimigos com cores diferentes)
- **Pontuação**: +10 pontos por pellet comido

## 📁 Estrutura do Projeto

```
pacman/
├── pacman.py          # Jogo principal com lógica e renderização
├── audio.py           # Sistema de áudio (sem pygame.mixer)
├── requirements.txt   # Dependências do projeto
└── (sprites opcionais)
    ├── jogador.png    # Sprite do Pac-Man (32x32 recomendado)
    ├── fantasma.png   # Sprite dos fantasmas
    └── parede.png     # Sprite das paredes
```

## 🎨 Usando Sprites Personalizados

O jogo tenta carregar imagens automaticamente. Se não encontrar, usa quadrados coloridos.

### Fontes de Sprites:
- **Sprites Resource**: https://www.spriters-resource.com/browser_games/
- **OpenGameArt**: https://opengameart.org/
- **Pac-Man Sprites**: Procure por "Arcade Pac-Man" no site

### Como adicionar:
1. Baixe os sprites (idealmente 32x32 pixels)
2. Renomeie para `jogador.png`, `fantasma.png`, `parede.png`
3. Coloque na mesma pasta que `pacman.py`
4. Execute o jogo - ele detectará automaticamente!

## 🔊 Áudio

O jogo possui efeitos sonoros para:
- ✅ Início do jogo (3 tons crescentes)
- ✅ Comendo pellet (2 tons)
- ✅ Morrer (descida de frequência)
- ✅ Vitória (melodia celebratória)
- ✅ Game Over (tom grave)

Os sons são gerados em tempo real usando NumPy (sem dependência de arquivos de áudio).

## 🎓 Estrutura do Código

### Classe `Personagem`
Base para todos os personagens do jogo (Pac-Man e fantasmas).

### Classe `Pacman(Personagem)`
Estende personagem com lógica de movimento do jogador:
- Colisão com paredes
- Mudança de direção suave
- Coleta de pellets

### Classe `Fantasma(Personagem)`
IA básica de inimigos:
- Movimento aleatório
- 70% de chance de perseguir Pac-Man
- Muda direção a cada 30 frames

### Classe `AudioPacman`
Sistema de áudio com sons gerados proceduralmente:
- Gera ondas senoidais
- Diferentes frequências para diferentes eventos

## 🕹️ Regras do Jogo

1. **Vitória**: Coma todos os pellets sem morrer
2. **Derrota**: Seja atingido por 3 fantasmas
3. **Pontuação**: Cada pellet = 10 pontos
4. **Reiniciar**: Pressione R na tela de fim de jogo

## 💡 Dicas para Expansão

1. **Mais Fantasmas**: Adicione cores diferentes (já temos 4 cores definidas)
2. **Power-Ups**: Crie pellets especiais que deixam Pac-Man invencível
3. **Níveis**: Crie múltiplos mapas com dificuldade crescente
4. **IA Melhorada**: Use pathfinding (A*) para fantasmas mais inteligentes
5. **Animações**: Alterne frames da imagem de Pac-Man (boca aberta/fechada)

## 🐛 Troubleshooting

### "Imagens não encontradas"
Isso é normal! O jogo funciona com quadrados coloridos. Para usar sprites:
1. Baixe do link acima
2. Coloque na pasta `pacman/`
3. Nomeie corretamente: `jogador.png`, `fantasma.png`, `parede.png`

### "pygame.mixer não disponível"
Normal em algumas instalações. O jogo foi adaptado para usar áudio sem mixer!

### Jogo muito rápido/lento?
Ajuste a variável `FPS` no topo de `pacman.py` (padrão: 60)

## 📊 Variáveis Personalizáveis

```python
LARGURA, ALTURA = 640, 480    # Tamanho da tela
TAM_BLOCO = 32                 # Tamanho de cada célula do grid
FPS = 60                        # Frames por segundo
```

## 🎪 Divirta-se!

O jogo está pronto para jogar. Boa sorte em coletar todos os pellets!

---

Criado com ❤️ usando Pygame e Python
