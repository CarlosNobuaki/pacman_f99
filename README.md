# Pac-Man Web Edition

Versão web do Pac-Man com até 5 jogadores simultâneos no mesmo mapa.

## Como jogar

1. Instale as dependências.
2. Inicie o servidor.
3. Acesse a URL no navegador.

### 1. Instalar dependências

```bash
cd /Users/carlosnobuaki/pacman
./.venv311/bin/pip install -r requirements.txt
```

### 2. Executar o servidor

```bash
cd /Users/carlosnobuaki/pacman
./.venv311/bin/python3 server.py
```

Se a porta 7001 estiver ocupada, o servidor tenta liberá-la automaticamente.

### 3. Acessar no navegador

Abra:

```text
http://localhost:7001
```

Se quiser acessar de outro dispositivo na mesma rede, use o IP da máquina:

```text
http://SEU-IP-LOCAL:7001
```

## Controles

- Setas do teclado ou WASD para mover
- ESC para pausar

## Objetivo

- Comer todos os pellets
- Evitar os fantasmas
- Fazer a maior pontuação possível

## Recursos

- Até 5 jogadores simultâneos
- Seleção de avatar por cor
- Fantasmas com IA no servidor
- Placar persistente em SQLite
- Interface web com sincronização em tempo real

## Estrutura do projeto

```text
pacman/
├── server.py
├── game_state.py
├── pacman.py
├── audio.py
├── texto.py
├── templates/
├── static/
├── levels/
├── requirements.txt
└── README.md
```

## Personalização

- Porta do servidor: `server.py`
- Velocidade do jogo: `game_state.py`
- Level inicial: `game_state.py`

## Troubleshooting

### O servidor não inicia

Verifique se a instalação está na virtualenv correta:

```bash
source /Users/carlosnobuaki/pacman/.venv311/bin/activate
python server.py
```

### A porta 7001 já está em uso

O servidor tenta liberar a porta automaticamente antes de subir. Se ainda houver conflito, feche o processo que estiver usando a porta.

### O navegador não atualiza

Faça um refresh forçado com `Cmd+Shift+R`.

## Desenvolvimento

- `server.py` controla o backend web
- `game_state.py` concentra a lógica do jogo
- `static/js/client.js` desenha o jogo no navegador
- `templates/index.html` contém a interface

