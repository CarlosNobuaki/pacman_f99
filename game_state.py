import os
import random
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Set


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVEL_PATH = os.path.join(BASE_DIR, "levels", "12.txt")

# Tile IDs
TILE_PELLET = 2
TILE_POWER_PELLET = 3
TILE_PACMAN_START = 4
GHOST_TILES = {10, 11, 12, 13}

# Constantes
INTERVALO_MOV_PACMAN_MS = 130
TAM_BLOCO = 32
FPS = 60

# Dificuldade progressiva dos fantasmas
FANTASMA_INTERVALO_INICIAL_MS = 500   # começa lento (500ms entre movimentos)
FANTASMA_INTERVALO_MINIMO_MS  = 140   # limite máximo de velocidade
FANTASMA_INTELIGENCIA_INICIAL = 0.10  # 10% de chance de perseguir no início
FANTASMA_INTELIGENCIA_MAXIMA  = 0.85  # 85% no máximo
FANTASMA_RAMP_DURACAO_MS      = 120_000  # 2 minutos para atingir velocidade/inteligência máxima

# Cores para avatares (em RGB)
CORES_AVATAR = {
    "amarelo": (255, 255, 0),
    "vermelho": (255, 0, 0),
    "rosa": (255, 184, 255),
    "ciano": (0, 255, 255),
    "laranja": (255, 165, 0),
}


KILL_POWERUP_INTERVALO_MS = 40_000   # spawn a cada 40s
KILL_POWERUP_DURACAO_MS   = 10_000   # poder dura 10s
KILL_POWERUP_COR          = (255, 0, 0)


@dataclass
class Jogador:
    """Representa um jogador Pac-Man."""
    id: str
    nome: str
    avatar: str
    x: int
    y: int
    proximo_x: int
    proximo_y: int
    score: int = 0
    vidas: int = 3
    eliminado: bool = False
    kill_poder: bool = False
    kill_poder_ms: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "avatar": self.avatar,
            "x": self.x,
            "y": self.y,
            "score": self.score,
            "vidas": self.vidas,
            "eliminado": self.eliminado,
            "cor": CORES_AVATAR.get(self.avatar, (255, 255, 0)),
            "kill_poder": self.kill_poder,
            "kill_poder_ms": self.kill_poder_ms,
        }


@dataclass
class Fantasma:
    """Representa um fantasma IA."""
    id: int
    x: int
    y: int
    cor: Tuple[int, int, int]
    
    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "cor": self.cor,
        }


class GameState:
    """Gerencia estado do jogo multiplayer (servidor)."""
    
    def __init__(self):
        self.mapa_parede: Set[Tuple[int, int]] = set()
        self.pellets: Set[Tuple[int, int]] = set()
        self.power_pellets: Set[Tuple[int, int]] = set()
        self.spawn_jogadores_list: List[Tuple[int, int]] = []
        self.spawn_fantasmas_list: List[Tuple[int, int]] = []
        
        self.jogadores: Dict[str, Jogador] = {}
        self.fantasmas: List[Fantasma] = []
        
        self.tempo_mov_pacman = 0
        self.tempo_mov_fantasma = 0
        self.frame_counter = 0
        self.tempo_jogo_ms = 0

        self.kill_powerup_pos: Tuple[int, int] | None = None
        self.kill_powerup_timer_ms: int = KILL_POWERUP_INTERVALO_MS  # primeiro spawn em 40s

        self.game_over = False
        self.venceu = False
        
        self._carregar_level()
        self._inicializar_fantasmas()
    
    def _carregar_level(self):
        """Carrega nível do arquivo."""
        if not os.path.exists(LEVEL_PATH):
            raise FileNotFoundError(f"Arquivo de level não encontrado: {LEVEL_PATH}")
        
        with open(LEVEL_PATH, "r", encoding="utf-8") as f:
            linhas = f.readlines()
        
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
            
            if lendo_mapa:
                try:
                    grid.append([int(x) for x in texto.split()])
                except ValueError:
                    continue
        
        if not grid:
            raise ValueError("Não foi possível carregar leveldata do arquivo.")
        
        self.altura = len(grid)
        self.largura = len(grid[0]) if grid else 0
        
        # Parse grid e identifica spawns e elementos
        for y, linha in enumerate(grid):
            for x, tile_id in enumerate(linha):
                if tile_id >= 100:  # Parede
                    self.mapa_parede.add((x, y))
                elif tile_id == TILE_PELLET:
                    self.pellets.add((x, y))
                elif tile_id == TILE_POWER_PELLET:
                    self.power_pellets.add((x, y))
                elif tile_id == TILE_PACMAN_START:
                    self.spawn_jogadores_list.append((x, y))
                elif tile_id in GHOST_TILES:
                    self.spawn_fantasmas_list.append((x, y))
        
        # Se não houver spawn de jogador, coloca no canto
        if not self.spawn_jogadores_list:
            self.spawn_jogadores_list = [(1, 1)]
        
        if not self.spawn_fantasmas_list:
            self.spawn_fantasmas_list = [(9, 4), (10, 4), (9, 5), (10, 5)]
    
    def _inicializar_fantasmas(self):
        """Cria os 4 fantasmas IA."""
        cores_fantasmas = [
            (255, 0, 0),      # Vermelho
            (255, 184, 255),  # Rosa
            (0, 255, 255),    # Ciano
            (255, 165, 0),    # Laranja
        ]
        
        for i in range(min(4, len(self.spawn_fantasmas_list))):
            spawn = self.spawn_fantasmas_list[i % len(self.spawn_fantasmas_list)]
            fantasma = Fantasma(
                id=i,
                x=spawn[0],
                y=spawn[1],
                cor=cores_fantasmas[i]
            )
            self.fantasmas.append(fantasma)
    
    def adicionar_jogador(self, jogador_id: str, nome: str, avatar: str) -> Jogador:
        """Adiciona novo jogador ao jogo."""
        if len(self.jogadores) >= 5:
            raise ValueError("Máximo de 5 jogadores atingido!")
        
        if avatar not in CORES_AVATAR:
            avatar = "amarelo"
        
        spawn = self.spawn_jogadores_list[len(self.jogadores) % len(self.spawn_jogadores_list)]
        
        jogador = Jogador(
            id=jogador_id,
            nome=nome,
            avatar=avatar,
            x=spawn[0],
            y=spawn[1],
            proximo_x=spawn[0],
            proximo_y=spawn[1],
            score=0,
            vidas=3,
        )
        
        self.jogadores[jogador_id] = jogador
        return jogador
    
    def remover_jogador(self, jogador_id: str):
        """Remove jogador do jogo."""
        if jogador_id in self.jogadores:
            del self.jogadores[jogador_id]
    
    def tentar_mover_jogador(self, jogador_id: str, dx: int, dy: int):
        """Tenta mover jogador na direção (dx, dy)."""
        if jogador_id not in self.jogadores:
            return
        
        jogador = self.jogadores[jogador_id]
        novo_x = jogador.x + dx
        novo_y = jogador.y + dy
        
        # Verifica colisão com parede
        if (novo_x, novo_y) not in self.mapa_parede:
            jogador.proximo_x = novo_x
            jogador.proximo_y = novo_y
    
    def _spawn_kill_powerup(self):
        """Escolhe uma posição livre (sem parede, pellet ou jogador) para o power-up."""
        ocupados = self.mapa_parede | self.pellets | self.power_pellets
        ocupados |= {(j.x, j.y) for j in self.jogadores.values()}
        if self.kill_powerup_pos:
            ocupados.add(self.kill_powerup_pos)

        livres = [
            (x, y)
            for x in range(1, self.largura - 1)
            for y in range(1, self.altura - 1)
            if (x, y) not in ocupados
        ]
        if livres:
            self.kill_powerup_pos = random.choice(livres)

    def _dificuldade_atual(self):
        """Retorna (intervalo_ms, inteligencia) progressivos baseados no tempo de jogo."""
        progresso = min(1.0, self.tempo_jogo_ms / FANTASMA_RAMP_DURACAO_MS)
        intervalo = FANTASMA_INTERVALO_INICIAL_MS - progresso * (
            FANTASMA_INTERVALO_INICIAL_MS - FANTASMA_INTERVALO_MINIMO_MS
        )
        inteligencia = FANTASMA_INTELIGENCIA_INICIAL + progresso * (
            FANTASMA_INTELIGENCIA_MAXIMA - FANTASMA_INTELIGENCIA_INICIAL
        )
        return int(intervalo), inteligencia

    def atualizar(self, dt: int):
        """Atualiza estado do jogo a cada frame (dt em ms)."""
        self.frame_counter += 1
        self.tempo_jogo_ms += dt
        self.tempo_mov_pacman += dt
        self.tempo_mov_fantasma += dt

        intervalo_fantasma, inteligencia = self._dificuldade_atual()

        # Atualiza posição dos jogadores (ignora eliminados)
        if self.tempo_mov_pacman >= INTERVALO_MOV_PACMAN_MS:
            for jogador in self.jogadores.values():
                if jogador.eliminado:
                    continue
                if (jogador.proximo_x, jogador.proximo_y) not in self.mapa_parede:
                    colisao_jogador = any(
                        j.x == jogador.proximo_x and j.y == jogador.proximo_y
                        for j in self.jogadores.values()
                        if j.id != jogador.id and not j.eliminado
                    )
                    if not colisao_jogador:
                        jogador.x = jogador.proximo_x
                        jogador.y = jogador.proximo_y
            self.tempo_mov_pacman = 0

        # Atualiza posição dos fantasmas com dificuldade progressiva
        if self.tempo_mov_fantasma >= intervalo_fantasma:
            for fantasma in self.fantasmas:
                self._atualizar_fantasma(fantasma, inteligencia)
            self.tempo_mov_fantasma = 0
        
        # Timer do kill power-up vermelho
        self.kill_powerup_timer_ms -= dt
        if self.kill_powerup_timer_ms <= 0 and self.kill_powerup_pos is None:
            self._spawn_kill_powerup()
            self.kill_powerup_timer_ms = KILL_POWERUP_INTERVALO_MS

        # Verifica colisão de jogadores com pellets e power-ups
        for jogador in self.jogadores.values():
            if jogador.eliminado:
                continue
            pos = (jogador.x, jogador.y)

            if pos in self.pellets:
                self.pellets.discard(pos)
                jogador.score += 10
            elif pos in self.power_pellets:
                self.power_pellets.discard(pos)
                jogador.score += 50

            # Coleta o kill power-up vermelho
            if self.kill_powerup_pos and pos == self.kill_powerup_pos:
                self.kill_powerup_pos = None
                self.kill_powerup_timer_ms = KILL_POWERUP_INTERVALO_MS
                jogador.kill_poder = True
                jogador.kill_poder_ms = KILL_POWERUP_DURACAO_MS

            # Decrementa timer do poder
            if jogador.kill_poder:
                jogador.kill_poder_ms -= dt
                if jogador.kill_poder_ms <= 0:
                    jogador.kill_poder = False
                    jogador.kill_poder_ms = 0

            # Colisão com fantasmas → invencível se tiver kill poder
            for fantasma in self.fantasmas:
                if jogador.kill_poder:
                    break
                if jogador.x == fantasma.x and jogador.y == fantasma.y:
                    jogador.vidas -= 1
                    if jogador.vidas <= 0:
                        jogador.eliminado = True
                        jogador.kill_poder = False
                    else:
                        spawn = self.spawn_jogadores_list[0]
                        jogador.x = spawn[0]
                        jogador.y = spawn[1]
                        jogador.proximo_x = spawn[0]
                        jogador.proximo_y = spawn[1]
                    break

        # Colisão kill poder vs outros jogadores
        jogadores_ativos = [j for j in self.jogadores.values() if not j.eliminado]
        for atacante in jogadores_ativos:
            if not atacante.kill_poder:
                continue
            for vitima in jogadores_ativos:
                if vitima.id == atacante.id:
                    continue
                if atacante.x == vitima.x and atacante.y == vitima.y:
                    vitima.vidas -= 1
                    atacante.score += 100
                    if vitima.vidas <= 0:
                        vitima.eliminado = True
                        vitima.kill_poder = False
                    else:
                        spawn = self.spawn_jogadores_list[0]
                        vitima.x = spawn[0]
                        vitima.y = spawn[1]
                        vitima.proximo_x = spawn[0]
                        vitima.proximo_y = spawn[1]

        # Vitória: todos os pellets comidos
        if not self.pellets and not self.power_pellets:
            self.venceu = True

        # Verifica condições de fim considerando eliminações
        ativos = [j for j in self.jogadores.values() if not j.eliminado]
        total = len(self.jogadores)

        if total == 1 and len(ativos) == 0:
            # Jogo solo: jogador foi eliminado
            self.game_over = True
        elif total > 1:
            if len(ativos) == 0:
                # Todos eliminados ao mesmo tempo
                self.game_over = True
            elif len(ativos) == 1:
                # Último sobrevivente: ele vence
                ativos[0].score += 500
                self.venceu = True
    
    def _atualizar_fantasma(self, fantasma: Fantasma, inteligencia: float = 0.5):
        """Atualiza posição de um fantasma com IA progressiva (4 direções cardinais)."""
        DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]

        ativos = [j for j in self.jogadores.values() if not j.eliminado]
        if ativos and random.random() < inteligencia:
            alvo = random.choice(ativos)
            tx, ty = alvo.x, alvo.y

            # Ordena as 4 direções pela distância Manhattan ao alvo
            def prioridade(d):
                nx, ny = fantasma.x + d[0], fantasma.y + d[1]
                return abs(nx - tx) + abs(ny - ty)

            candidatos = sorted(DIRS, key=prioridade)
        else:
            candidatos = random.sample(DIRS, len(DIRS))

        # Tenta cada direção em ordem até achar uma livre
        for dx, dy in candidatos:
            nx = fantasma.x + dx
            ny = fantasma.y + dy
            if 0 <= nx < self.largura and 0 <= ny < self.altura and (nx, ny) not in self.mapa_parede:
                fantasma.x = nx
                fantasma.y = ny
                return
    
    def get_estado(self) -> dict:
        """Retorna estado completo do jogo."""
        _, inteligencia = self._dificuldade_atual()
        nivel = min(10, int(inteligencia / FANTASMA_INTELIGENCIA_MAXIMA * 10))
        return {
            "jogadores": [j.to_dict() for j in self.jogadores.values()],
            "fantasmas": [f.to_dict() for f in self.fantasmas],
            "pellets": list(self.pellets),
            "power_pellets": list(self.power_pellets),
            "kill_powerup": list(self.kill_powerup_pos) if self.kill_powerup_pos else None,
            "mapa_parede": list(self.mapa_parede),
            "largura": self.largura,
            "altura": self.altura,
            "game_over": self.game_over,
            "venceu": self.venceu,
            "nivel_dificuldade": nivel,
            "tempo_jogo_ms": self.tempo_jogo_ms,
        }
