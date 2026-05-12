#!/usr/bin/env python3
"""
Script de configuração e teste do Pac-Man Game
Permite testar áudio, carregar sprites, etc.
"""

import os
import sys

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas"""
    deps = ['pygame', 'numpy']
    faltando = []
    
    for dep in deps:
        try:
            __import__(dep)
            print(f"✓ {dep} instalado")
        except ImportError:
            print(f"✗ {dep} NÃO instalado")
            faltando.append(dep)
    
    if faltando:
        print(f"\n⚠️  Faltam dependências: {', '.join(faltando)}")
        print(f"Execute: pip install {' '.join(faltando)}")
        return False
    
    print("\n✓ Todas as dependências instaladas!")
    return True

def testar_audio():
    """Testa o sistema de áudio"""
    print("\n" + "="*50)
    print("TESTANDO SISTEMA DE ÁUDIO")
    print("="*50)
    
    try:
        from audio import AudioPacman
        audio = AudioPacman()
        print("✓ Módulo de áudio carregado")
        
        print("\nTestando sons (isso vai levar alguns segundos)...")
        
        print("  • Som de início...", end='', flush=True)
        audio.som_comecar_jogo()
        print(" ✓")
        
        print("  • Som de pellet...", end='', flush=True)
        audio.som_comer_pellet()
        print(" ✓")
        
        print("  • Som de morrer...", end='', flush=True)
        audio.som_morrer()
        print(" ✓")
        
        print("  • Som de vitória...", end='', flush=True)
        audio.som_vitoria()
        print(" ✓")
        
        print("  • Som de game over...", end='', flush=True)
        audio.som_game_over()
        print(" ✓")
        
        print("\n✓ Sistema de áudio funcionando!")
        return True
    except Exception as e:
        print(f"\n✗ Erro ao testar áudio: {e}")
        return False

def verificar_sprites():
    """Verifica se os sprites estão disponíveis"""
    print("\n" + "="*50)
    print("VERIFICANDO SPRITES")
    print("="*50)
    
    sprites = ['jogador.png', 'fantasma.png', 'parede.png']
    encontrados = 0
    
    for sprite in sprites:
        if os.path.exists(sprite):
            print(f"✓ {sprite} encontrado")
            encontrados += 1
        else:
            print(f"✗ {sprite} NÃO encontrado (usará cores)")
    
    if encontrados == 0:
        print("\n⚠️  Nenhum sprite encontrado!")
        print("O jogo usará quadrados coloridos como fallback.")
        print("\nPara adicionar sprites:")
        print("1. Baixe de: https://www.spriters-resource.com/browser_games/")
        print("2. Redimensione para 32x32 pixels")
        print("3. Salve como: jogador.png, fantasma.png, parede.png")
        print("4. Coloque nesta pasta e execute novamente")
    
    return encontrados > 0

def limpar_cache():
    """Remove cache do Python"""
    import shutil
    if os.path.exists('__pycache__'):
        print("Removendo cache Python...")
        shutil.rmtree('__pycache__')
        print("✓ Cache removido")

def menu_principal():
    """Menu principal"""
    while True:
        print("\n" + "="*50)
        print("PAC-MAN GAME - MENU DE CONFIGURAÇÃO")
        print("="*50)
        print("\n1. Verificar dependências")
        print("2. Testar sistema de áudio")
        print("3. Verificar sprites")
        print("4. Executar jogo")
        print("5. Limpar cache")
        print("6. Sair")
        print("\nEscolha uma opção (1-6): ", end='')
        
        try:
            opcao = input().strip()
            
            if opcao == '1':
                verificar_dependencias()
            elif opcao == '2':
                testar_audio()
            elif opcao == '3':
                verificar_sprites()
            elif opcao == '4':
                print("\nIniciando jogo...")
                print("Controles: Setas do teclado para mover, R para reiniciar")
                os.system('python3 pacman.py')
            elif opcao == '5':
                limpar_cache()
            elif opcao == '6':
                print("Até logo! 👋")
                break
            else:
                print("Opção inválida!")
        except KeyboardInterrupt:
            print("\n\nAté logo! 👋")
            break
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Modo linha de comando
        cmd = sys.argv[1].lower()
        if cmd == '--check':
            verificar_dependencias()
            verificar_sprites()
            sys.exit(0 if verificar_dependencias() else 1)
        elif cmd == '--test-audio':
            testar_audio()
            sys.exit(0)
        elif cmd == '--play':
            os.system('python3 pacman.py')
            sys.exit(0)
        else:
            print("Uso: python3 setup.py [--check|--test-audio|--play]")
            sys.exit(1)
    else:
        # Modo interativo
        menu_principal()
