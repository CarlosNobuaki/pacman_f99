import os
import random

import pygame

from audio import AudioPacman
from texto import get_fonte

# Tile IDs compatíveis com crossref do projeto de referência.
TILE_GHOST_DOOR = 1
TILE_PELLET = 2
TILE_POWER_PELLET = 3
TILE_PACMAN_START = 4
GHOST_TILES = {10, 11, 12, 13}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVEL_PATH = os.path.join(BASE_DIR, "levels", "12.txt")

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
AMARELO = (255, 255, 0)
VERMELHO = (255, 0, 0)
AZUL = (0, 0, 255)
ROSA = (255, 184, 255)
CIANO = (0, 255, 255)
LARANJA = (255, 165, 0)

FPS = 60
HUD_ALTURA = 48
INTERVALO_MOV_PACMAN_MS = 130
INTERVALO_MOV_FANTASMA_MS = 170


def parse_cor(partes, padrao):
    if len(partes) < 4:
        return padrao
    try:
        return (int(partes[1]), int(partes[2]), int(partes[3]))
    except ValueError:
        return padrao


def carregar_level_referencia(level_path):
    if not os.path.exists(level_path):
        raise FileNotFoundError(f"Arquivo de level nao encontrado: {level_path}")

    with open(level_path, "r", encoding="utf-8") as f:
        linhas = f.readlines()

    metadata = {
        "lvlwidth": None,
        "lvlheight": None,
        "pelletcolor": (238, 183, 128),
    }
    lendo_mapa = False
    grid = []

    for linha in linhas:
        texto = linha.strip()
        if not texto:
            continue

        if texto.startswith("#"):
            tag = texto[1:].strip().lower()
            if tag == "startleveldata":
                lendo_mapa = True
                continue
            if tag == "endleveldata":
                lendo_mapa = False
                continue

            if not lendo_mapa:
                partes = tag.split()
                if not partes:
                    continue
                chave = partes[0]
                if chave in ("lvlwidth", "lvlheight") and len(partes) >= 2:
                    try:
                        metadata[chave] = int(partes[1])
                    except ValueError:
                        pass
                elif chave == "pelletcolor":
                    metadata["pelletcolor"] = parse_cor(partes, metadata["pelletcolor"])
            continue

        if lendo_mapa:
            try:
                grid.append([int(x) for x in texto.split()])
            except ValueError:
                continue

    if not grid:
        raise ValueError("Nao foi possivel carregar leveldata do arquivo.")

    altura = len(grid)
    largura = max(len(linha) for linha in grid)

    if metadata["lvlwidth"] is not None:
        largura = metadata["lvlwidth"]
    if metadata["lvlheight"] is not None:
        altura = metadata["lvlheight"]

    # Normaliza tamanho para evitar erro em linhas incompletas.
    while len(grid) < altura:
        grid.append([0] * largura)
    grid = [linha[:largura] + [0] * max(0, largura - len(linha)) for linha in grid[:altura]]

    mapa_parede = []
    pellets_template = []
    pacman_spawn = None
    ghost_spawns = {}

    for y in range(altura):
        linha_parede = []
        for x in range(largura):
            tile_id = grid[y][x]
            eh_parede = tile_id >= 100 or tile_id == TILE_GHOST_DOOR
            linha_parede.append(1 if eh_parede else 0)

            if tile_id == TILE_PELLET:
                pellets_template.append((x, y, 10, False))
            elif tile_id == TILE_POWER_PELLET:
                pellets_template.append((x, y, 50, True))
            elif tile_id == TILE_PACMAN_START:
                pacman_spawn = (x, y)
            elif tile_id in GHOST_TILES:
                ghost_spawns[tile_id] = (x, y)
        mapa_parede.append(linha_parede)

    if pacman_spawn is None:
        pacman_spawn = (1, 1)

    # Ordem original: blinky(10), pinky(11), inky(12), sue(13).
    ghosts_ordenados = []
    for ghost_id in [10, 11, 12, 13]:
        if ghost_id in ghost_spawns:
            ghosts_ordenados.append(ghost_spawns[ghost_id])

    if not ghosts_ordenados:
        ghosts_ordenados = [(9, 4), (10, 4), (9, 5), (10, 5)]

    return {
        "largura": largura,
        "altura": altura,
        "pelletcolor": metadata["pelletcolor"],
        "mapa_parede": mapa_parede,
        "pellets_template": pellets_template,
        "pacman_spawn": pacman_spawn,
        "ghost_spawns": ghosts_ordenados,
    }


def carregar_sprite(candidatos, tam_bloco, fallback_color):
    for nome in candidatos:
        caminho = os.path.join(BASE_DIR, nome)
        if os.path.exists(caminho):
            try:
                img = pygame.image.load(caminho).convert_alpha()
                return pygame.transform.scale(img, (tam_bloco, tam_bloco))
            except pygame.error:
                continue

    # fallback visual
    surface = pygame.Surface((tam_bloco, tam_bloco))
    surface.fill(fallback_color)
    return surface


class Personagem:
    def __init__(self, x, y, img, cores=None):
        self.x = x
        self.y = y
        self.img = img
        self.cores = cores or [VERMELHO]
        self.cor_idx = 0
        self.direcao = (0, 0)

    @property
    def rect(self):
        return pygame.Rect(self.x * TAM_BLOCO, self.y * TAM_BLOCO, TAM_BLOCO, TAM_BLOCO)

    def desenhar(self, surface):
        if self.img:
            surface.blit(self.img, self.rect)
        else:
            pygame.draw.rect(surface, self.cores[self.cor_idx], self.rect)


class Pacman(Personagem):
    def __init__(self, x, y, img):
        super().__init__(x, y, img)
        self.proximo_x = x
        self.proximo_y = y

    def atualizar(self, paredes):
        teste_rect = pygame.Rect(self.proximo_x * TAM_BLOCO, self.proximo_y * TAM_BLOCO, TAM_BLOCO, TAM_BLOCO)
        if not any(teste_rect.colliderect(p) for p in paredes):
            self.x = self.proximo_x
            self.y = self.proximo_y

    def tentar_mover(self, dx, dy):
        self.proximo_x = max(0, min(self.x + dx, COLS - 1))
        self.proximo_y = max(0, min(self.y + dy, LINHAS - 1))


class Fantasma(Personagem):
    def __init__(self, x, y, img, cor):
        super().__init__(x, y, img, [cor])
        self.contador = 0
        self.direcoes = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        self.direcao = random.choice(self.direcoes)

    def atualizar(self, pacman, paredes):
        self.contador += 1
        if self.contador > 30:
            self.contador = 0
            if random.random() < 0.7:
                dx_pkg = pacman.x - self.x
                dy_pkg = pacman.y - self.y
                if abs(dx_pkg) > abs(dy_pkg):
                    self.direcao = (1, 0) if dx_pkg > 0 else (-1, 0)
                else:
                    self.direcao = (0, 1) if dy_pkg > 0 else (0, -1)
            else:
                self.direcao = random.choice(self.direcoes)

        nova_x = self.x + self.direcao[0]
        nova_y = self.y + self.direcao[1]

        if 0 <= nova_x < COLS and 0 <= nova_y < LINHAS:
            teste_rect = pygame.Rect(nova_x * TAM_BLOCO, nova_y * TAM_BLOCO, TAM_BLOCO, TAM_BLOCO)
            if not any(teste_rect.colliderect(p) for p in paredes):
                self.x = nova_x
                self.y = nova_y
            else:
                self.direcao = random.choice(self.direcoes)
        else:
            self.direcao = random.choice(self.direcoes)


def criar_pellets(template):
    resultado = []
    for x, y, valor, power in template:
        margem = 2 if power else 3
        tam = 10 if power else 6
        rect = pygame.Rect(
            x * TAM_BLOCO + TAM_BLOCO // 2 - margem,
            y * TAM_BLOCO + TAM_BLOCO // 2 - margem,
            tam,
            tam,
        )
        resultado.append({"rect": rect, "valor": valor, "power": power})
    return resultado


def criar_fantasmas(spawns, img_fantasma):
    cores = [VERMELHO, ROSA, CIANO, LARANJA]
    fantasmas = []
    for i, spawn in enumerate(spawns[:4]):
        cor = cores[i % len(cores)]
        fantasmas.append(Fantasma(spawn[0], spawn[1], img_fantasma, cor))
    return fantasmas


level_data = carregar_level_referencia(LEVEL_PATH)
COLS = level_data["largura"]
LINHAS = level_data["altura"]

# Ajuste automático para caber mapas maiores (como o level 12 original).
TAM_BLOCO = max(16, min(28, min(960 // COLS, 700 // LINHAS)))
LARGURA = COLS * TAM_BLOCO
ALTURA = LINHAS * TAM_BLOCO + HUD_ALTURA

pygame.init()
tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("Pac-Man (Mapa referencia)")
clock = pygame.time.Clock()

fonte = get_fonte(36)
fonte_pequena = get_fonte(24)

try:
    audio = AudioPacman()
except Exception:
    print("Aviso: Sistema de audio indisponivel")
    audio = None

img_pacman = carregar_sprite(
    [
        "jogador.png",
        "pacman.png",
        os.path.join("res", "sprite", "pacman-r 1.gif"),
        os.path.join("pacman", "res", "sprite", "pacman-r 1.gif"),
    ],
    TAM_BLOCO,
    AMARELO,
)
img_fantasma = carregar_sprite(
    [
        "enemy.png",
        "fantasma.png",
        "ghost.png",
        os.path.join("res", "sprite", "ghost 1.gif"),
        os.path.join("pacman", "res", "sprite", "ghost 1.gif"),
    ],
    TAM_BLOCO,
    VERMELHO,
)
img_parede = carregar_sprite(
    [
        "maze.png",
        "parede.png",
        "wall.png",
        os.path.join("res", "tiles", "wall-straight-horiz.gif"),
        os.path.join("pacman", "res", "tiles", "wall-straight-horiz.gif"),
    ],
    TAM_BLOCO,
    AZUL,
)

paredes = [
    pygame.Rect(c * TAM_BLOCO, l * TAM_BLOCO, TAM_BLOCO, TAM_BLOCO)
    for l, linha in enumerate(level_data["mapa_parede"])
    for c, bloco in enumerate(linha)
    if bloco == 1
]

spawn_pacman = level_data["pacman_spawn"]
spawn_fantasmas = level_data["ghost_spawns"]
pellets_template = level_data["pellets_template"]


def resetar_jogo():
    jogador = Pacman(spawn_pacman[0], spawn_pacman[1], img_pacman)
    fantasmas = criar_fantasmas(spawn_fantasmas, img_fantasma)
    pellets = criar_pellets(pellets_template)
    pontos = 0
    vidas = 3
    estado = "jogando"
    return jogador, fantasmas, pellets, pontos, vidas, estado


jogador, fantasmas, pellets, pontos, vidas, estado_jogo = resetar_jogo()
tempo_mov_pacman = 0
tempo_mov_fantasma = 0

if audio:
    audio.som_comecar_jogo()

rodando = True
while rodando:
    tela.fill(PRETO)
    dt = clock.tick(FPS)

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            rodando = False
        elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_r and estado_jogo != "jogando":
            if audio:
                audio.som_comecar_jogo()
            jogador, fantasmas, pellets, pontos, vidas, estado_jogo = resetar_jogo()
            tempo_mov_pacman = 0
            tempo_mov_fantasma = 0

    if estado_jogo == "jogando":
        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT]:
            jogador.tentar_mover(-1, 0)
        if teclas[pygame.K_RIGHT]:
            jogador.tentar_mover(1, 0)
        if teclas[pygame.K_UP]:
            jogador.tentar_mover(0, -1)
        if teclas[pygame.K_DOWN]:
            jogador.tentar_mover(0, 1)

        tempo_mov_pacman += dt
        tempo_mov_fantasma += dt

        if tempo_mov_pacman >= INTERVALO_MOV_PACMAN_MS:
            jogador.atualizar(paredes)
            tempo_mov_pacman = 0

        if tempo_mov_fantasma >= INTERVALO_MOV_FANTASMA_MS:
            for fantasma in fantasmas:
                fantasma.atualizar(jogador, paredes)
            tempo_mov_fantasma = 0

        for pellet in pellets[:]:
            if jogador.rect.colliderect(pellet["rect"]):
                pellets.remove(pellet)
                pontos += pellet["valor"]
                if audio:
                    audio.som_comer_pellet()

        for fantasma in fantasmas:
            if jogador.rect.colliderect(fantasma.rect):
                vidas -= 1
                if audio:
                    audio.som_morrer()
                if vidas <= 0:
                    estado_jogo = "game_over"
                    if audio:
                        audio.som_game_over()
                else:
                    jogador = Pacman(spawn_pacman[0], spawn_pacman[1], img_pacman)
                    tempo_mov_pacman = 0
                    tempo_mov_fantasma = 0

        if not pellets:
            estado_jogo = "vitoria"
            if audio:
                audio.som_vitoria()

    # Draw mapa
    for p in paredes:
        tela.blit(img_parede, p)

    pellet_color = level_data["pelletcolor"]
    for pellet in pellets:
        raio = 5 if pellet["power"] else 3
        pygame.draw.circle(tela, pellet_color, pellet["rect"].center, raio)

    for fantasma in fantasmas:
        fantasma.desenhar(tela)
    jogador.desenhar(tela)

    # HUD
    hud_y = LINHAS * TAM_BLOCO
    pygame.draw.rect(tela, (20, 20, 20), (0, hud_y, LARGURA, HUD_ALTURA))
    texto_pontos = fonte_pequena.render(f"Pontos: {pontos}", True, BRANCO)
    texto_vidas = fonte_pequena.render(f"Vidas: {vidas}", True, BRANCO)
    texto_level = fonte_pequena.render("Level: 12 (referencia)", True, BRANCO)
    tela.blit(texto_pontos, (10, hud_y + 12))
    tela.blit(texto_vidas, (LARGURA // 2 - 40, hud_y + 12))
    tela.blit(texto_level, (LARGURA - 190, hud_y + 12))

    # Mensagens de estado
    if estado_jogo == "game_over":
        texto_gameover = fonte.render("GAME OVER!", True, VERMELHO)
        texto_restart = fonte_pequena.render("Pressione R para reiniciar", True, BRANCO)
        tela.blit(texto_gameover, (LARGURA // 2 - 110, LINHAS * TAM_BLOCO // 2 - 30))
        tela.blit(texto_restart, (LARGURA // 2 - 120, LINHAS * TAM_BLOCO // 2 + 10))
    elif estado_jogo == "vitoria":
        texto_vitoria = fonte.render("VOCE VENCEU!", True, AMARELO)
        texto_restart = fonte_pequena.render("Pressione R para reiniciar", True, BRANCO)
        tela.blit(texto_vitoria, (LARGURA // 2 - 120, LINHAS * TAM_BLOCO // 2 - 30))
        tela.blit(texto_restart, (LARGURA // 2 - 120, LINHAS * TAM_BLOCO // 2 + 10))

    pygame.display.flip()

pygame.quit()
