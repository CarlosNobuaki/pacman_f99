from PIL import Image
import numpy as np

img_e = Image.open('enemy.png').convert('RGBA')
img_m = Image.open('maze.png').convert('RGBA')

# ===== ANALISE DE FANTASMAS =====
de = np.array(img_e)
sprite_size = 16

def buscar_patches(de, r_min, r_max, g_min, g_max, b_min, b_max, ratio_min=0.20, label=''):
    cands = []
    for y in range(0, de.shape[0]-sprite_size, sprite_size):
        for x in range(0, de.shape[1]-sprite_size, sprite_size):
            p = de[y:y+sprite_size, x:x+sprite_size]
            mask = ((p[:,:,0]>=r_min)&(p[:,:,0]<=r_max)&
                    (p[:,:,1]>=g_min)&(p[:,:,1]<=g_max)&
                    (p[:,:,2]>=b_min)&(p[:,:,2]<=b_max)&
                    (p[:,:,3]>150))
            vis = p[:,:,3] > 100
            ratio = mask.sum() / max(vis.sum(), 1)
            if ratio > ratio_min:
                cands.append((x, y, round(float(ratio),2)))
    if cands:
        print(f"{label}: primeiros 5 = {cands[:5]}")
    else:
        print(f"{label}: NENHUM PATCH ENCONTRADO")
    return cands

print("=== BUSCA DE SPRITES ===")
# Blinky (vermelho puro)
red = buscar_patches(de, 180,255, 0,80, 0,80, 0.25, 'Blinky (vermelho)')
# Pinky (rosa magenta)
pink = buscar_patches(de, 200,255, 100,180, 200,255, 0.20, 'Pinky (rosa)')
# Inky (ciano)
cyan = buscar_patches(de, 0,100, 200,255, 200,255, 0.20, 'Inky (ciano)')
# Clyde (laranja)
orange = buscar_patches(de, 200,255, 100,180, 0,100, 0.20, 'Clyde (laranja)')

# Salva amostras
def save_spr(img_e, cands, path, label):
    if cands:
        x0, y0, _ = cands[0]
        spr = img_e.crop((x0, y0, x0+sprite_size, y0+sprite_size)).resize((32,32), Image.NEAREST)
        spr.save(path)
        print(f"-> salvo {path} de ({x0},{y0})")

save_spr(img_e, red, '/tmp/spr_blinky.png', 'Blinky')
save_spr(img_e, pink, '/tmp/spr_pinky.png', 'Pinky')
save_spr(img_e, cyan, '/tmp/spr_inky.png', 'Inky')
save_spr(img_e, orange, '/tmp/spr_clyde.png', 'Clyde')

# Salva Pac-Man confirmado
img_e.crop((608, 0, 624, 16)).resize((32,32), Image.NEAREST).save('/tmp/spr_pac.png')
print("-> salvo /tmp/spr_pac.png de (608,0,16,16)")

# Quadrante de parede do maze
img_m.crop((0, 0, 225, 203)).save('/tmp/spr_wall_quad.png')
print(f"-> salvo /tmp/spr_wall_quad.png")

# Tile de parede 32x32 direto do quadrante superior esquerdo
img_m.crop((2, 2, 34, 34)).save('/tmp/spr_wall_tile.png')
print(f"-> salvo /tmp/spr_wall_tile.png (2,2,34,34)")

we, he = img_e.size
wm, hm = img_m.size
print(f"enemy.png: {we}x{he}")
print(f"maze.png:  {wm}x{hm}")

de = np.array(img_e)
dm = np.array(img_m)

# Localiza pixels amarelos (Pac-Man) em enemy.png
yellow = (de[:,:,0]>200) & (de[:,:,1]>180) & (de[:,:,2]<100) & (de[:,:,3]>150)
rows_y = np.where(yellow.any(axis=1))[0]
cols_y = np.where(yellow.any(axis=0))[0]
if len(rows_y):
    print(f"\nAmarelo - linhas: {rows_y[0]}..{rows_y[-1]}")
    print(f"Amarelo - cols:   {cols_y[0]}..{cols_y[-1]}")

# Procura sprites amarelos isolados (caixas 16x16)
sprite_size = 16
candidatos_16 = []
for y in range(0, he - sprite_size, sprite_size):
    for x in range(0, we - sprite_size, sprite_size):
        patch = de[y:y+sprite_size, x:x+sprite_size]
        is_y = (patch[:,:,0]>200) & (patch[:,:,1]>180) & (patch[:,:,2]<100) & (patch[:,:,3]>150)
        vis   = patch[:,:,3] > 100
        ratio = is_y.sum() / max(vis.sum(), 1)
        if ratio > 0.15:
            candidatos_16.append((x, y, round(float(ratio), 2)))

print(f"\nPatch 16x16 com >15% amarelo (primeiros 10): {candidatos_16[:10]}")

# Tenta 14x14 também
candidatos_14 = []
for y in range(0, he - 14, 14):
    for x in range(0, we - 14, 14):
        patch = de[y:y+14, x:x+14]
        is_y = (patch[:,:,0]>200) & (patch[:,:,1]>180) & (patch[:,:,2]<100) & (patch[:,:,3]>150)
        vis   = patch[:,:,3] > 100
        ratio = is_y.sum() / max(vis.sum(), 1)
        if ratio > 0.20:
            candidatos_14.append((x, y, round(float(ratio), 2)))

print(f"Patch 14x14 com >20% amarelo (primeiros 10): {candidatos_14[:10]}")

# Fantasmas: branco/azul (ghost azul assustado) ou vermelho (Blinky)
red_mask = (de[:,:,0]>200) & (de[:,:,1]<80) & (de[:,:,2]<80) & (de[:,:,3]>150)
rows_r = np.where(red_mask.any(axis=1))[0]
cols_r = np.where(red_mask.any(axis=0))[0]
if len(rows_r):
    print(f"\nVermelho (Blinky?) - linhas: {rows_r[0]}..{rows_r[-1]}, cols: {cols_r[0]}..{cols_r[-1]}")

# Fantasma branco/azul (sprites de ghost com corpo branco + olhos)
white_mask = (de[:,:,0]>220) & (de[:,:,1]>220) & (de[:,:,2]>220) & (de[:,:,3]>150)

# maze.png: conta paredes azuis
blue_wall = (dm[:,:,2]>150) & (dm[:,:,0]<100) & (dm[:,:,1]<100) & (dm[:,:,3]>150)
total_blue = blue_wall.sum()
rows_w = np.where(blue_wall.any(axis=1))[0]
cols_w = np.where(blue_wall.any(axis=0))[0]
print(f"\nmaze.png paredes azuis: {total_blue} px")
if len(rows_w):
    print(f"  rows: {rows_w[0]}..{rows_w[-1]}, cols: {cols_w[0]}..{cols_w[-1]}")
    # Tile de parede: pega 32x32 do quadrante superior esquerdo
    print(f"  Tile wall crop sugerido: (0, 0, {wm//2}, {hm//2})")

# Salva crops de amostra para inspeção visual
try:
    # Pega o primeiro candidato amarelo e salva
    if candidatos_16:
        x0, y0, _ = candidatos_16[0]
        crop_pac = img_e.crop((x0, y0, x0+32, y0+32))
        crop_pac.save('/tmp/sample_pacman.png')
        print(f"\nSalvou /tmp/sample_pacman.png (sprite={x0},{y0})")
    # Tile de parede
    half_w, half_h = wm//2, hm//2
    crop_wall = img_m.crop((0, 0, half_w, half_h))
    crop_wall.save('/tmp/sample_wall.png')
    print(f"Salvou /tmp/sample_wall.png (maze quadrante 0,0,{half_w},{half_h})")
except Exception as e:
    print(f"Erro ao salvar crops: {e}")
