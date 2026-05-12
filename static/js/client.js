// Configuração
const TAM_BLOCO = 32;
const COLS = 21;
const ROWS = 27;
const HUD_ALTURA = 48;
const CANVAS_WIDTH = COLS * TAM_BLOCO;
const CANVAS_HEIGHT = ROWS * TAM_BLOCO + HUD_ALTURA;

// Elementos DOM
const canvas = document.getElementById('canvas-jogo');
const ctx = canvas.getContext('2d');
const modalEntrada = document.getElementById('modal-entrada');
const modalPausa = document.getElementById('modal-pausa');
const hud = document.getElementById('hud');
ctx.imageSmoothingEnabled = false;

// Estado do cliente
let socket = null;
let jogador = null;
let jogador_id = null;
let avatar_selecionado = 'amarelo';
let estado_jogo = null;
let teclas_pressionadas = {};
let direcao_proxima = { dx: 0, dy: 0 };
let pausa = false;
let conectado = false;

// Cores
const CORES = {
    amarelo: '#FFFF00',
    vermelho: '#FF0000',
    rosa: '#FFB8FF',
    ciano: '#00FFFF',
    laranja: '#FFA500',
};

const SPRITES = {
    enemy: null,
    maze: null,
    enemyReady: false,
    mazeReady: false,
    validacao: {
        pacman: false,
        fantasmaVermelho: false,
        parede: false,
        mapa: false,
    },
};

const RECORTES_ENEMY = {
    pacman: { sx: 608, sy: 0, sw: 16, sh: 16 },
    fantasmas: {
        vermelho: { sx: 0, sy: 0, sw: 16, sh: 16 },
        rosa: { sx: 200, sy: 0, sw: 16, sh: 16 },
        ciano: { sx: 400, sy: 0, sw: 16, sh: 16 },
        laranja: { sx: 800, sy: 368, sw: 16, sh: 16 },
    },
};

const RECORTE_MAZE_PAREDE = { sx: 8, sy: 8, sw: 16, sh: 16 };
// Usa apenas a metade sem pellets "impressos" para evitar efeito de sobreposição
// com os pellets/power pellets que o jogo desenha dinamicamente.
const RECORTE_MAZE_MAPA = { sx: 112, sy: 0, sw: 112, sh: 203 };

function carregarImagem(src) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        img.onload = () => resolve(img);
        img.onerror = () => reject(new Error(`Falha ao carregar: ${src}`));
        img.src = src;
    });
}

function recorteValido(img, recorte) {
    const canvasTmp = document.createElement('canvas');
    canvasTmp.width = recorte.sw;
    canvasTmp.height = recorte.sh;
    const ctxTmp = canvasTmp.getContext('2d', { willReadFrequently: true });

    ctxTmp.drawImage(
        img,
        recorte.sx,
        recorte.sy,
        recorte.sw,
        recorte.sh,
        0,
        0,
        recorte.sw,
        recorte.sh
    );

    const data = ctxTmp.getImageData(0, 0, recorte.sw, recorte.sh).data;
    let pixelsComAlpha = 0;
    let brilhoTotal = 0;

    for (let i = 0; i < data.length; i += 4) {
        const alpha = data[i + 3];
        if (alpha > 10) {
            pixelsComAlpha += 1;
            brilhoTotal += data[i] + data[i + 1] + data[i + 2];
        }
    }

    return pixelsComAlpha > 10 && brilhoTotal > 1000;
}

async function inicializarSprites() {
    try {
        SPRITES.enemy = await carregarImagem('/static/enemy.png');
        SPRITES.enemyReady = true;
        SPRITES.validacao.pacman = recorteValido(SPRITES.enemy, RECORTES_ENEMY.pacman);
        SPRITES.validacao.fantasmaVermelho = recorteValido(SPRITES.enemy, RECORTES_ENEMY.fantasmas.vermelho);
    } catch (err) {
        console.warn('enemy.png indisponivel, usando fallback por cor.', err.message);
    }

    try {
        SPRITES.maze = await carregarImagem('/static/maze.png');
        SPRITES.mazeReady = true;
        SPRITES.validacao.parede = recorteValido(SPRITES.maze, RECORTE_MAZE_PAREDE);
        SPRITES.validacao.mapa = recorteValido(SPRITES.maze, RECORTE_MAZE_MAPA);
    } catch (err) {
        console.warn('maze.png indisponivel, usando fallback por cor.', err.message);
    }
}

function desenharSpriteComFallback(img, recorte, dx, dy, dw, dh, fallbackColor) {
    if (img && recorte) {
        ctx.drawImage(
            img,
            recorte.sx,
            recorte.sy,
            recorte.sw,
            recorte.sh,
            dx,
            dy,
            dw,
            dh
        );
        return;
    }

    ctx.fillStyle = fallbackColor;
    ctx.fillRect(dx, dy, dw, dh);
}

function desenharParede(x, y) {
    const dx = x * TAM_BLOCO;
    const dy = y * TAM_BLOCO + HUD_ALTURA;

    // Preenchimento azul escuro
    ctx.fillStyle = '#00008B';
    ctx.fillRect(dx, dy, TAM_BLOCO, TAM_BLOCO);

    // Borda interna brilhante (estilo arcade clássico)
    ctx.strokeStyle = '#3333FF';
    ctx.lineWidth = 2;
    ctx.strokeRect(dx + 1, dy + 1, TAM_BLOCO - 2, TAM_BLOCO - 2);
}

function desenharFundoMaze() {
    // Desabilitado: maze.png não alinha com o grid do servidor.
    // Paredes são sempre desenhadas tile-a-tile a partir dos dados do servidor.
    return false;
}

function recorteFantasmaPorCor(rgbArray) {
    const [r, g, b] = rgbArray;
    if (r > 240 && g < 80 && b < 80) return RECORTES_ENEMY.fantasmas.vermelho;
    if (r > 230 && g > 130 && b > 230) return RECORTES_ENEMY.fantasmas.rosa;
    if (r < 80 && g > 200 && b > 200) return RECORTES_ENEMY.fantasmas.ciano;
    if (r > 230 && g > 120 && b < 80) return RECORTES_ENEMY.fantasmas.laranja;
    return RECORTES_ENEMY.fantasmas.vermelho;
}

function desenharFantasma(fantasma) {
    const dx = fantasma.x * TAM_BLOCO;
    const dy = fantasma.y * TAM_BLOCO + HUD_ALTURA;

    if (SPRITES.enemyReady && SPRITES.validacao.fantasmaVermelho) {
        const recorte = recorteFantasmaPorCor(fantasma.cor);
        desenharSpriteComFallback(
            SPRITES.enemy,
            recorte,
            dx,
            dy,
            TAM_BLOCO,
            TAM_BLOCO,
            `rgb(${fantasma.cor[0]}, ${fantasma.cor[1]}, ${fantasma.cor[2]})`
        );
    } else {
        ctx.fillStyle = `rgb(${fantasma.cor[0]}, ${fantasma.cor[1]}, ${fantasma.cor[2]})`;
        ctx.fillRect(dx, dy, TAM_BLOCO, TAM_BLOCO);
    }

    ctx.fillStyle = '#000';
    ctx.fillRect(dx + 8, dy + 8, 6, 6);
    ctx.fillRect(dx + 18, dy + 8, 6, 6);
}

function desenharJogadorSprite(jogadorInfo) {
    const dx = jogadorInfo.x * TAM_BLOCO;
    const dy = jogadorInfo.y * TAM_BLOCO + HUD_ALTURA;

    if (SPRITES.enemyReady && SPRITES.validacao.pacman) {
        desenharSpriteComFallback(
            SPRITES.enemy,
            RECORTES_ENEMY.pacman,
            dx,
            dy,
            TAM_BLOCO,
            TAM_BLOCO,
            `rgb(${jogadorInfo.cor[0]}, ${jogadorInfo.cor[1]}, ${jogadorInfo.cor[2]})`
        );
    } else {
        ctx.fillStyle = `rgb(${jogadorInfo.cor[0]}, ${jogadorInfo.cor[1]}, ${jogadorInfo.cor[2]})`;
        ctx.fillRect(dx, dy, TAM_BLOCO, TAM_BLOCO);
    }
}

// ============ INICIALIZAÇÃO ============

function inicializar() {
    socket = io();
    inicializarSprites();
    
    socket.on('connect', () => {
        console.log('Conectado ao servidor');
        conectado = true;
    });
    
    socket.on('erro', (data) => {
        mostrar_erro(data.mensagem);
    });
    
    socket.on('jogador_criado', (data) => {
        jogador_id = data.jogador_id;
        jogador = data.jogador;
        estado_jogo = data.estado;
        
        // Oculta modal de entrada
        modalEntrada.style.display = 'none';
        hud.style.display = 'flex';
        
        console.log('Jogador criado:', jogador);
    });
    
    socket.on('estado_atualizado', (data) => {
        estado_jogo = data;
        desenhar_jogo();
    });
    
    socket.on('novo_jogador', (data) => {
        console.log('Novo jogador conectado:', data.jogador.nome);
    });
    
    socket.on('jogador_saiu', (data) => {
        console.log('Jogador saiu:', data.jogador_id);
    });
    
    socket.on('jogo_reiniciado', () => {
        console.log('Jogo reiniciado');
        jogador = null;
        jogador_id = null;
        estado_jogo = null;
        pausa = false;
        modalEntrada.style.display = 'flex';
        hud.style.display = 'none';
        modalPausa.style.display = 'none';
    });
    
    // Event listeners para entrada
    const botoes_avatar = document.querySelectorAll('.avatar-btn');
    botoes_avatar.forEach(btn => {
        btn.addEventListener('click', () => {
            botoes_avatar.forEach(b => b.classList.remove('selecionado'));
            btn.classList.add('selecionado');
            avatar_selecionado = btn.dataset.avatar;
        });
    });
    
    // Seleciona avatar padrão
    document.querySelector('[data-avatar="amarelo"]').classList.add('selecionado');
    
    document.getElementById('btn-entrar').addEventListener('click', criar_jogador);
    document.getElementById('btn-sair').addEventListener('click', sair_jogo);
    document.getElementById('btn-continuar').addEventListener('click', toggle_pausa);
    document.getElementById('btn-nova-partida').addEventListener('click', nova_partida);
    
    // Event listeners para teclado
    document.addEventListener('keydown', handle_keydown);
    document.addEventListener('keyup', handle_keyup);
    
    // Carrega top scores
    carregar_top_scores();
}

// ============ NETWORK ============

function criar_jogador() {
    const nome = document.getElementById('nome-jogador').value.trim();
    
    if (!nome) {
        mostrar_erro('Digite um nome!');
        return;
    }
    
    socket.emit('criar_jogador', {
        nome: nome,
        avatar: avatar_selecionado,
    });
}

function sair_jogo() {
    if (jogador_id) {
        socket.emit('finalizar_partida');
        socket.disconnect();
        window.location.reload();
    }
}

function nova_partida() {
    socket.emit('reiniciar_jogo');
}

function toggle_pausa() {
    pausa = !pausa;
    const btn = document.getElementById('btn-continuar');
    btn.textContent = pausa ? 'Retomar' : 'Continuar';
    modalPausa.style.display = pausa ? 'flex' : 'none';
}

// ============ INPUT ============

function handle_keydown(e) {
    if (!jogador_id) return;
    
    teclas_pressionadas[e.key.toLowerCase()] = true;
    
    // Pausa com ESC
    if (e.key === 'Escape') {
        toggle_pausa();
        return;
    }
    
    // Direções
    switch(e.key.toLowerCase()) {
        case 'arrowup':
        case 'w':
            direcao_proxima = { dx: 0, dy: -1 };
            break;
        case 'arrowdown':
        case 's':
            direcao_proxima = { dx: 0, dy: 1 };
            break;
        case 'arrowleft':
        case 'a':
            direcao_proxima = { dx: -1, dy: 0 };
            break;
        case 'arrowright':
        case 'd':
            direcao_proxima = { dx: 1, dy: 0 };
            break;
    }
    
    if (direcao_proxima.dx !== 0 || direcao_proxima.dy !== 0) {
        socket.emit('mover', direcao_proxima);
    }
}

function handle_keyup(e) {
    teclas_pressionadas[e.key.toLowerCase()] = false;
}

// ============ RENDER ============

function desenhar_jogo() {
    if (!estado_jogo) return;
    
    // Limpa canvas
    ctx.fillStyle = '#000';
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
    
    // Desenha HUD
    desenhar_hud();
    
    // Se houver maze valido, usa a imagem completa para ficar fiel ao visual do sprite sheet.
    // Caso contrario, usa desenho por tiles de parede.
    const fundoMazeDesenhado = desenharFundoMaze();
    if (!fundoMazeDesenhado) {
        for (const [x, y] of estado_jogo.mapa_parede) {
            desenharParede(x, y);
        }
    }
    
    // Desenha pellets
    ctx.fillStyle = '#FFB897';
    for (const [x, y] of estado_jogo.pellets) {
        const px = x * TAM_BLOCO + TAM_BLOCO / 2;
        const py = y * TAM_BLOCO + HUD_ALTURA + TAM_BLOCO / 2;
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, Math.PI * 2);
        ctx.fill();
    }

    // Desenha power pellets (piscando a cada 500ms)
    const piscando = Math.floor(Date.now() / 300) % 2 === 0;
    if (piscando) {
        ctx.fillStyle = '#FFE000';
        for (const [x, y] of estado_jogo.power_pellets) {
            const px = x * TAM_BLOCO + TAM_BLOCO / 2;
            const py = y * TAM_BLOCO + HUD_ALTURA + TAM_BLOCO / 2;
            ctx.beginPath();
            ctx.arc(px, py, 7, 0, Math.PI * 2);
            ctx.fill();
        }
    }
    
    // Desenha kill power-up vermelho (piscando)
    if (estado_jogo.kill_powerup) {
        const [kx, ky] = estado_jogo.kill_powerup;
        const pisca = Math.floor(Date.now() / 200) % 2 === 0;
        if (pisca) {
            const px = kx * TAM_BLOCO + TAM_BLOCO / 2;
            const py = ky * TAM_BLOCO + HUD_ALTURA + TAM_BLOCO / 2;
            // brilho externo
            ctx.shadowColor = '#FF0000';
            ctx.shadowBlur = 12;
            ctx.fillStyle = '#FF0000';
            ctx.beginPath();
            ctx.arc(px, py, 8, 0, Math.PI * 2);
            ctx.fill();
            ctx.shadowBlur = 0;
            // cruz no centro
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(px - 1, py - 5, 2, 10);
            ctx.fillRect(px - 5, py - 1, 10, 2);
        }
    }

    // Desenha fantasmas
    for (const fantasma of estado_jogo.fantasmas) {
        desenharFantasma(fantasma);
    }

    // Desenha jogadores (eliminados ficam invisíveis)
    for (const jogador_info of estado_jogo.jogadores) {
        if (jogador_info.eliminado) continue;
        desenharJogadorSprite(jogador_info);

        // Aura vermelha se tiver kill poder
        if (jogador_info.kill_poder) {
            const dx = jogador_info.x * TAM_BLOCO;
            const dy = jogador_info.y * TAM_BLOCO + HUD_ALTURA;
            const pisca = Math.floor(Date.now() / 150) % 2 === 0;
            ctx.strokeStyle = pisca ? '#FF0000' : '#FF8800';
            ctx.lineWidth = 3;
            ctx.shadowColor = '#FF0000';
            ctx.shadowBlur = 10;
            ctx.strokeRect(dx + 1, dy + 1, TAM_BLOCO - 2, TAM_BLOCO - 2);
            ctx.shadowBlur = 0;

            // Contador regressivo
            if (jogador_info.id === jogador_id) {
                const seg = Math.ceil(jogador_info.kill_poder_ms / 1000);
                ctx.fillStyle = '#FF4444';
                ctx.font = 'bold 11px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(`${seg}s`, dx + TAM_BLOCO / 2, dy - 3);
            }
        }

        // Destaca myself
        if (jogador_info.id === jogador_id && !jogador_info.kill_poder) {
            ctx.strokeStyle = '#FFFF00';
            ctx.lineWidth = 2;
            ctx.strokeRect(
                jogador_info.x * TAM_BLOCO,
                jogador_info.y * TAM_BLOCO + HUD_ALTURA,
                TAM_BLOCO,
                TAM_BLOCO
            );
        }
    }
    
    // Atualiza HUD
    document.getElementById('cont-jogadores').textContent = estado_jogo.jogadores.length;
    
    // Verifica eliminação do jogador local
    if (jogador_id && estado_jogo.jogadores) {
        const eu = estado_jogo.jogadores.find(j => j.id === jogador_id);
        if (eu && eu.eliminado && !pausa) {
            mostrar_eliminado(eu);
        }
    }

    // Game over / vitória globais
    if (estado_jogo.venceu) {
        mostrar_vitoria();
    } else if (estado_jogo.game_over) {
        mostrar_game_over();
    }
}

function desenhar_hud() {
    ctx.fillStyle = '#111';
    ctx.fillRect(0, 0, CANVAS_WIDTH, HUD_ALTURA);

    if (jogador) {
        ctx.font = 'bold 16px Arial';
        ctx.textAlign = 'left';
        ctx.fillStyle = '#FFF';
        ctx.fillText(`${jogador.nome}: ${jogador.score}`, 10, 30);

        ctx.fillStyle = '#FF6666';
        ctx.fillText(`♥ ${jogador.vidas}`, CANVAS_WIDTH - 80, 30);
    }

    if (estado_jogo && estado_jogo.nivel_dificuldade !== undefined) {
        const nivel = estado_jogo.nivel_dificuldade;
        const cor = nivel <= 3 ? '#44FF44' : nivel <= 6 ? '#FFAA00' : '#FF4444';
        ctx.font = 'bold 13px Arial';
        ctx.textAlign = 'center';
        ctx.fillStyle = cor;
        ctx.fillText(`Fantasmas Lv.${nivel}`, CANVAS_WIDTH / 2, 30);
    }
}

// ============ UI ============

function mostrar_erro(msg) {
    document.getElementById('msg-erro').textContent = msg;
    setTimeout(() => {
        document.getElementById('msg-erro').textContent = '';
    }, 5000);
}

async function carregar_top_scores() {
    try {
        const res = await fetch('/api/top-scores');
        const scores = await res.json();
        
        const lista = document.getElementById('lista-scores');
        lista.innerHTML = '';
        
        scores.forEach((score, idx) => {
            const div = document.createElement('div');
            div.className = 'score-item';
            div.innerHTML = `
                <span><span class="score-rank">${idx + 1}.</span> ${score.nome}</span>
                <span>${score.score}</span>
            `;
            lista.appendChild(div);
        });
    } catch (e) {
        console.error('Erro ao carregar scores:', e);
    }
}

function mostrar_vitoria() {
    pausa = true;
    document.getElementById('titulo-pausa').textContent = 'Vitória!';
    atualizar_stats_pausa();
    modalPausa.style.display = 'flex';
}

function mostrar_game_over() {
    pausa = true;
    document.getElementById('titulo-pausa').textContent = 'Game Over';
    atualizar_stats_pausa();
    modalPausa.style.display = 'flex';
}

function mostrar_eliminado(eu) {
    pausa = true;
    document.getElementById('titulo-pausa').textContent = 'Você foi eliminado!';
    const stats = document.getElementById('stats-jogador');
    stats.innerHTML = `
        <div><strong>Jogador:</strong> ${eu.nome}</div>
        <div><strong>Score final:</strong> ${eu.score}</div>
        <div style="margin-top:8px; color:#aaa; font-size:13px;">
            Os outros jogadores ainda estão jogando.<br>Aguarde o fim da partida.
        </div>
    `;
    document.getElementById('btn-continuar').style.display = 'none';
    carregar_top_scores();
    modalPausa.style.display = 'flex';
}

function atualizar_stats_pausa() {
    const stats_div = document.getElementById('stats-jogador');
    
    if (jogador) {
        stats_div.innerHTML = `
            <div><strong>Jogador:</strong> ${jogador.nome}</div>
            <div><strong>Avatar:</strong> ${jogador.avatar}</div>
            <div><strong>Score:</strong> ${jogador.score}</div>
            <div><strong>Vidas:</strong> ${jogador.vidas}</div>
        `;
    }
    
    carregar_top_scores();
}

// ============ FANTASMA NOTIFICAÇÃO ============

const NOTIF_MENSAGENS = [
    'Vamo bate o ponto',
    'Maravilhoso',
    'Ta em prod ?',
    'Apontem suas horas',
];
const NOTIF_CORES    = ['#FFFF00', '#FF2222', '#00FF44', '#00AAFF'];
const NOTIF_INTERVALO_MS = 15_000;
const NOTIF_DURACAO_MS   = 4_000;

let notif = {
    ativo: false,
    mensagem: '',
    inicio: 0,
    ultimo_spawn: 0,
    indice: 0,
};

function atualizar_notif() {
    const agora = Date.now();

    if (!notif.ativo && agora - notif.ultimo_spawn >= NOTIF_INTERVALO_MS) {
        notif.ativo      = true;
        notif.inicio     = agora;
        notif.ultimo_spawn = agora;
        notif.mensagem   = NOTIF_MENSAGENS[notif.indice % NOTIF_MENSAGENS.length];
        notif.indice    += 1;
    }

    if (notif.ativo && agora - notif.inicio >= NOTIF_DURACAO_MS) {
        notif.ativo = false;
    }
}

function desenhar_notif_fantasma() {
    if (!notif.ativo) return;

    const agora = Date.now();

    // pisca a cada 120ms trocando cor
    const cor_idx = Math.floor(agora / 120) % NOTIF_CORES.length;
    const cor     = NOTIF_CORES[cor_idx];

    // posição: centro superior da tela de jogo
    const cx = CANVAS_WIDTH / 2;
    const cy = HUD_ALTURA + 60;
    const tam = 40;

    // sombra/brilho
    ctx.shadowColor = cor;
    ctx.shadowBlur  = 18;

    // corpo do fantasma
    ctx.fillStyle = cor;
    ctx.beginPath();
    ctx.arc(cx, cy, tam / 2, Math.PI, 0, false);          // topo arredondado
    ctx.lineTo(cx + tam / 2, cy + tam / 2);                // lado direito
    // ondas na base
    const ondas = 3;
    for (let i = ondas; i >= 0; i--) {
        const x0 = cx + tam / 2 - (i * tam / ondas);
        const x1 = cx + tam / 2 - ((i + 0.5) * tam / ondas);
        const dir = i % 2 === 0 ? cy + tam / 2 + 8 : cy + tam / 2 - 2;
        ctx.quadraticCurveTo(x1, dir, x0 - tam / ondas / 2, cy + tam / 2);
    }
    ctx.closePath();
    ctx.fill();

    // olhos brancos
    ctx.shadowBlur = 0;
    ctx.fillStyle  = '#FFFFFF';
    ctx.beginPath(); ctx.arc(cx - 9, cy - 4, 6, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx + 9, cy - 4, 6, 0, Math.PI * 2); ctx.fill();

    // pupilas pretas
    ctx.fillStyle = '#000';
    ctx.beginPath(); ctx.arc(cx - 7, cy - 3, 3, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx + 11, cy - 3, 3, 0, Math.PI * 2); ctx.fill();

    // balão de fala acima do fantasma
    ctx.shadowBlur = 0;
    ctx.font = 'bold 14px Arial';
    ctx.textAlign = 'center';
    const txtW   = ctx.measureText(notif.mensagem).width;
    const pad    = 10;
    const bW     = txtW + pad * 2;
    const bH     = 28;
    const bX     = cx - bW / 2;
    const bY     = cy - tam / 2 - bH - 18;

    // fundo branco do balão
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.roundRect(bX, bY, bW, bH, 6);
    ctx.fill();

    // bordinha colorida
    ctx.strokeStyle = cor;
    ctx.lineWidth   = 2;
    ctx.stroke();

    // rabinho do balão apontando para o fantasma
    ctx.fillStyle = '#FFFFFF';
    ctx.beginPath();
    ctx.moveTo(cx - 6, bY + bH);
    ctx.lineTo(cx + 6, bY + bH);
    ctx.lineTo(cx,     bY + bH + 10);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = cor;
    ctx.lineWidth = 1.5;
    ctx.stroke();

    // texto dentro do balão
    ctx.fillStyle = '#111111';
    ctx.fillText(notif.mensagem, cx, bY + bH - 8);
}

// ============ LOOP ============

function game_loop() {
    atualizar_notif();
    desenhar_jogo();
    desenhar_notif_fantasma();
    requestAnimationFrame(game_loop);
}

// Inicia tudo
inicializar();
game_loop();
