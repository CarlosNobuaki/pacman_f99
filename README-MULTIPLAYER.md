# 🎮 Pac-Man Multiplayer - Web Edition

Versão multiplayer web do Pac-Man com até 5 jogadores simultâneos no mesmo mapa!

## ✨ Recursos

- **5 Jogadores:** Até 5 pessoas jogando simultaneamente no mesmo nível
- **Avatares:** Escolha entre 5 cores de avatar (Amarelo, Vermelho, Rosa, Ciano, Laranja)
- **IA de Fantasmas:** 4 fantasmas inteligentes perseguindo jogadores
- **Scores Persistentes:** Placar salvo em banco de dados SQLite
- **Real-time Sync:** Sincronização via WebSocket (~60 FPS)
- **Responsive:** Funciona em desktop e mobile

## 🚀 Instalação

### 1. Instale as Dependências

```bash
cd /Users/carlosnobuaki/pacman
./.venv311/bin/pip install -r requirements.txt
```

### 2. Inicie o Servidor

```bash
./.venv311/bin/python3 server.py
```

Você verá:
```
🎮 Servidor Pac-Man iniciado em http://localhost:5001
```

### 3. Acesse o Jogo

Abra seu navegador em: **http://localhost:5001**

## 🎮 Como Jogar

1. **Escolha um Avatar:** Clique em uma das 5 cores
2. **Digite seu Nome:** Máximo 20 caracteres
3. **Clique em "Entrar no Jogo"**
4. **Controle seu Pac-Man:**
   - **Setas** ou **WASD** para mover
   - **ESC** para pausar

## 🎯 Objetivos

- **Comer Pellets:** 10 pontos cada
- **Comer Pellets de Poder:** 50 pontos cada (temporário em versões futuras)
- **Evitar Fantasmas:** Perdem 1 vida ao tocar
- **Vitória:** Comer todos os pellets do mapa

## 📊 Placar

- O placar é automaticamente salvo quando sua partida termina
- Veja o **Top 10** na tela de pausa
- Rankings persistem entre sessões

## 🏗️ Arquitetura

```
server.py           → Flask + SocketIO backend
game_state.py       → Lógica do jogo (server-side)
templates/index.html → Interface web
static/js/client.js → Lógica cliente
static/css/style.css → Styling
scores.db          → SQLite com scores
```

### Game Loop

- **Server-side:** Autoridade central (60 FPS, decoupled movement)
- **Client-side:** Renderização apenas (recebe estado, envia input)

### Movimentação

- **Pac-Man:** 130ms entre movimentos (~5 moves/sec)
- **Fantasmas:** 170ms entre movimentos (~4 moves/sec)

## 🔧 Personalização

### Mudar Porta

Edite `server.py`, linha 209:
```python
socketio.run(app, host="0.0.0.0", port=5001, ...)  # Mude 5001 para outra porta
```

### Mudar Velocidade

Edite `game_state.py`, linhas 26-27:
```python
INTERVALO_MOV_PACMAN_MS = 130    # Mais rápido = menor número
INTERVALO_MOV_FANTASMA_MS = 170  # Mais rápido = menor número
```

### Mudar Nível

Edite `game_state.py`, linha 31:
```python
LEVEL_PATH = os.path.join(BASE_DIR, "levels", "12.txt")  # Mude 12 para outro nível
```

## 🐛 Troubleshooting

### Erro: "Port is already in use"
```bash
# Mude de 5001 para 5002 em server.py
# Ou mate o processo: lsof -i :5001 | xargs kill -9
```

### Servidor não responde
```bash
# Verifique se está rodando:
ps aux | grep "python.*server.py"

# Veja logs:
tail -50 /tmp/pacman_server.log
```

### Clientes não veem uns aos outros
```bash
# Verifique a conexão WebSocket:
# Abra DevTools (F12) → Console
# Deve aparecer "Conectado ao servidor"
```

## 📝 Próximas Melhorias (Roadmap)

- [ ] Salas de jogo (múltiplas partidas simultâneas)
- [ ] Chat in-game
- [ ] Efeitos sonoros via Web Audio API
- [ ] Deploy em servidor publído
- [ ] Mobile app com React Native
- [ ] Níveis adicionais

## 👨‍💻 Desenvolvimento

### Estrutura de Dados (WebSocket)

**Estado do Jogo (enviado do servidor a cada frame):**
```json
{
    "jogadores": [
        {
            "id": "uuid...",
            "nome": "Carlos",
            "avatar": "amarelo",
            "x": 10,
            "y": 13,
            "score": 420,
            "vidas": 3,
            "cor": [255, 255, 0]
        }
    ],
    "fantasmas": [
        {
            "id": 0,
            "x": 9,
            "y": 4,
            "cor": [255, 0, 0]
        }
    ],
    "pellets": [[1, 1], [1, 2], ...],
    "power_pellets": [[5, 10], ...],
    "mapa_parede": [[0, 0], [0, 1], ...],
    "largura": 21,
    "altura": 27,
    "game_over": false,
    "venceu": false
}
```

**Eventos WebSocket:**
- `conectado` → Client enviar nome e avatar
- `criar_jogador` → Server cria jogador
- `mover` → Client envia movimento (dx, dy)
- `estado_atualizado` → Server envia estado
- `finalizar_partida` → Client avisa que vai sair (salva score)

## 📄 Licença

Projeto educacional. Baseado em Pac-Man clássico.

---

**Criado em 2026 | Multiplayer com ❤️**
