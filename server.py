import os
import signal
import subprocess
import atexit
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from game_state import GameState, CORES_AVATAR
import sqlite3
import threading
import time


app = Flask(__name__)
app.config["SECRET_KEY"] = "pacman-multiplayer-secret"
socketio = SocketIO(app, cors_allowed_origins="*")

PORT = 7001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Estado global do jogo
game_state = GameState()
game_loop_thread = None
game_running = True
client_sessions = {}  # Mapeia session_id -> jogador_id

DB_PATH = os.path.join(BASE_DIR, "scores.db")


def _pids_escutando_porta(porta: int) -> list[int]:
    """Retorna PIDs em LISTEN para a porta informada."""
    try:
        resultado = subprocess.run(
            ["lsof", "-tiTCP:%d" % porta, "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
        pids = []
        for linha in resultado.stdout.splitlines():
            linha = linha.strip()
            if linha.isdigit():
                pids.append(int(linha))
        return pids
    except Exception:
        return []


def liberar_porta_se_necessario(porta: int):
    """Encerra qualquer processo em LISTEN na porta para garantir subida limpa."""
    pids = _pids_escutando_porta(porta)
    if not pids:
        return

    for pid in pids:
        if pid == os.getpid():
            continue

        try:
            print(f"Liberando porta {porta}: encerrando PID {pid}")
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.25)
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"Aviso: nao foi possivel encerrar PID {pid}: {e}")


def solicitar_shutdown(*_args):
    """Encerra o processo imediatamente ao Ctrl+C."""
    global game_running
    game_running = False
    os._exit(0)


signal.signal(signal.SIGINT, solicitar_shutdown)
signal.signal(signal.SIGTERM, solicitar_shutdown)


def init_db():
    """Inicializa banco de dados de scores."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            score INTEGER NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


def salvar_score(nome: str, score: int):
    """Salva um score no banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scores (nome, score, data) VALUES (?, ?, ?)",
              (nome, score, datetime.now()))
    conn.commit()
    conn.close()


def obter_top_scores(limite: int = 10) -> list:
    """Retorna top scores."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT nome, score, data FROM scores ORDER BY score DESC LIMIT ?", (limite,))
    scores = c.fetchall()
    conn.close()
    return [{"nome": s[0], "score": s[1], "data": s[2]} for s in scores]


def game_loop():
    """Loop principal do jogo (roda em thread separada)."""
    clock_ms = 1000 / 60  # ~16.67ms para 60 FPS
    
    while game_running:
        start_time = time.time()
        
        try:
            # Atualiza estado do jogo
            game_state.atualizar(int(clock_ms))
            
            # Envia estado atualizado para todos os clientes
            estado = game_state.get_estado()
            socketio.emit("estado_atualizado", estado, namespace="/", skip_sid=None)
            
        except Exception as e:
            print(f"Erro no game loop: {e}")
        
        # Controla FPS com sleep pequeno e frequente para responsividade
        elapsed = (time.time() - start_time) * 1000
        sleep_time = max(0, clock_ms - elapsed) / 1000.0
        # Dorme em incrementos pequenos para responder rápido a shutdown
        steps = max(1, int(sleep_time / 0.01))
        for _ in range(steps):
            if not game_running:
                break
            time.sleep(min(0.01, sleep_time / steps))


@app.route("/")
def index():
    """Página principal."""
    return render_template("index.html")


@app.route("/api/top-scores")
def api_top_scores():
    """API para obter top scores."""
    scores = obter_top_scores(10)
    return jsonify(scores)


@socketio.on("connect", namespace="/")
def handle_connect():
    """Novo cliente conectado."""
    print(f"Cliente conectado: {request.sid}")
    emit("conectado", {"session_id": request.sid})


@socketio.on("disconnect", namespace="/")
def handle_disconnect():
    """Cliente desconectado."""
    print(f"Cliente desconectado: {request.sid}")
    
    if request.sid in client_sessions:
        jogador_id = client_sessions[request.sid]
        game_state.remover_jogador(jogador_id)
        del client_sessions[request.sid]
        
        # Notifica outros clientes
        socketio.emit("jogador_saiu", {"jogador_id": jogador_id}, namespace="/")


@socketio.on("criar_jogador", namespace="/")
def handle_criar_jogador(data):
    """Cria novo jogador."""
    try:
        nome = data.get("nome", "Jogador").strip()
        avatar = data.get("avatar", "amarelo").lower()
        
        if not nome or len(nome) > 20:
            nome = f"Jogador{len(game_state.jogadores) + 1}"
        
        if avatar not in CORES_AVATAR:
            avatar = "amarelo"
        
        # Verifica se já há jogador nesta sessão
        if request.sid in client_sessions:
            emit("erro", {"mensagem": "Você já está no jogo!"})
            return
        
        # Cria jogador
        jogador_id = str(uuid.uuid4())
        jogador = game_state.adicionar_jogador(jogador_id, nome, avatar)
        
        client_sessions[request.sid] = jogador_id
        
        # Retorna dados do jogador
        emit("jogador_criado", {
            "jogador_id": jogador_id,
            "jogador": jogador.to_dict(),
            "estado": game_state.get_estado(),
        })
        
        # Notifica outros clientes sobre novo jogador
        socketio.emit("novo_jogador", {"jogador": jogador.to_dict()}, skip_sid=request.sid, namespace="/")
        
        print(f"Jogador criado: {nome} ({avatar})")
        
    except ValueError as e:
        emit("erro", {"mensagem": str(e)})
    except Exception as e:
        print(f"Erro ao criar jogador: {e}")
        emit("erro", {"mensagem": "Erro ao criar jogador"})


@socketio.on("mover", namespace="/")
def handle_mover(data):
    """Processa movimento de um jogador."""
    try:
        if request.sid not in client_sessions:
            return
        
        jogador_id = client_sessions[request.sid]
        dx = data.get("dx", 0)
        dy = data.get("dy", 0)
        
        game_state.tentar_mover_jogador(jogador_id, dx, dy)
        
    except Exception as e:
        print(f"Erro ao processar movimento: {e}")


@socketio.on("finalizar_partida", namespace="/")
def handle_finalizar_partida():
    """Finaliza partida e salva scores."""
    try:
        if request.sid not in client_sessions:
            return
        
        jogador_id = client_sessions[request.sid]
        
        if jogador_id in game_state.jogadores:
            jogador = game_state.jogadores[jogador_id]
            salvar_score(jogador.nome, jogador.score)
            print(f"Score salvo: {jogador.nome} = {jogador.score}")
        
    except Exception as e:
        print(f"Erro ao finalizar partida: {e}")


@socketio.on("reiniciar_jogo", namespace="/")
def handle_reiniciar_jogo():
    """Reinicia o jogo."""
    global game_state
    print("Jogo reiniciado")
    game_state = GameState()
    client_sessions.clear()
    socketio.emit("jogo_reiniciado", namespace="/")


if __name__ == "__main__":
    try:
        init_db()
        liberar_porta_se_necessario(PORT)
        
        # Inicia loop do jogo em thread separada
        game_loop_thread = threading.Thread(target=game_loop, daemon=True)
        game_loop_thread.start()
        
        print(f"🎮 Servidor Pac-Man iniciado em http://localhost:{PORT}")
        print("Pressione Ctrl+C para parar o servidor")
        
        socketio.run(
            app,
            host="0.0.0.0",
            port=PORT,
            debug=False,
            use_reloader=False,
            allow_unsafe_werkzeug=True
        )
    except KeyboardInterrupt:
        print("\n⏹️  Encerrando servidor...")
        solicitar_shutdown()
        # Aguarda thread do game loop terminar
        if game_loop_thread and game_loop_thread.is_alive():
            game_loop_thread.join(timeout=2.0)
        print("Servidor encerrado.")
