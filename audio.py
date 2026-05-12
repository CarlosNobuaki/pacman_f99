import numpy as np
import pygame


class AudioPacman:
    """Efeitos sonoros gerados via numpy e reproduzidos com pygame.mixer."""

    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.som_ativo = True
        self._cache = {}

        try:
            if not pygame.get_init():
                pygame.init()
            if not pygame.mixer.get_init():
                pygame.mixer.init(
                    frequency=self.sample_rate,
                    size=-16,
                    channels=2,
                    buffer=512,
                )
            pygame.mixer.set_num_channels(8)
        except Exception:
            self.som_ativo = False

    def _onda_seno(self, frequencia, duracao, amplitude=0.3):
        frames = max(1, int(self.sample_rate * duracao))
        t = np.linspace(0, duracao, frames, endpoint=False)

        onda = amplitude * np.sin(2 * np.pi * frequencia * t)

        # Envelope curto para evitar clique no início/fim.
        attack = max(1, int(frames * 0.05))
        release = max(1, int(frames * 0.10))
        env = np.ones(frames)
        env[:attack] = np.linspace(0.0, 1.0, attack)
        env[-release:] = np.linspace(1.0, 0.0, release)
        onda *= env

        pcm = np.clip(onda * 32767, -32768, 32767).astype(np.int16)
        stereo = np.column_stack((pcm, pcm))
        return stereo

    def _silencio(self, duracao):
        frames = max(1, int(self.sample_rate * duracao))
        return np.zeros((frames, 2), dtype=np.int16)

    def _criar_som(self, chave, partes):
        if not self.som_ativo:
            return None
        if chave in self._cache:
            return self._cache[chave]

        dados = np.vstack(partes).astype(np.int16)
        som = pygame.sndarray.make_sound(dados)
        self._cache[chave] = som
        return som

    def _tocar(self, chave, partes):
        som = self._criar_som(chave, partes)
        if som is not None:
            som.play()

    def som_comecar_jogo(self):
        if not self.som_ativo:
            return
        self._tocar(
            "start",
            [
                self._onda_seno(400, 0.09),
                self._silencio(0.02),
                self._onda_seno(500, 0.09),
                self._silencio(0.02),
                self._onda_seno(600, 0.14),
            ],
        )

    def som_comer_pellet(self):
        if not self.som_ativo:
            return
        self._tocar(
            "pellet",
            [
                self._onda_seno(880, 0.03, 0.22),
                self._silencio(0.01),
                self._onda_seno(660, 0.03, 0.18),
            ],
        )

    def som_morrer(self):
        if not self.som_ativo:
            return
        partes = []
        for freq in [600, 560, 520, 470, 420, 360, 300, 240]:
            partes.append(self._onda_seno(freq, 0.04, 0.25))
            partes.append(self._silencio(0.01))
        self._tocar("death", partes)

    def som_vitoria(self):
        if not self.som_ativo:
            return
        partes = []
        for freq in [523.25, 659.25, 783.99, 1046.50]:
            partes.append(self._onda_seno(freq, 0.08, 0.26))
            partes.append(self._silencio(0.02))
        self._tocar("victory", partes)

    def som_game_over(self):
        if not self.som_ativo:
            return
        self._tocar(
            "gameover",
            [
                self._onda_seno(300, 0.25, 0.30),
                self._silencio(0.03),
                self._onda_seno(200, 0.30, 0.34),
            ],
        )
