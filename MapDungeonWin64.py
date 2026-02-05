import pygame
import sys
import os
import re
import json
import tkinter as tk
from tkinter import filedialog

# --- CONFIGURATION INITIALE ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
UI_WIDTH = 320
MENU_HEIGHT = 30
TILE_SIZE = 64
ASSET_ROOT = "Neutral Stone"

# Couleurs
COLOR_BG = (30, 30, 30)
COLOR_VIEW_BG = (0, 0, 0)
COLOR_UI_BG = (45, 45, 55)
COLOR_UI_BORDER = (100, 100, 100)
COLOR_GRID = (50, 50, 50)
COLOR_TEXT = (220, 220, 220)
COLOR_BTN_ACTIVE = (0, 120, 200)
COLOR_BTN_INACTIVE = (80, 80, 100)
COLOR_LEVEL_BTN = (100, 60, 60)
COLOR_MENU_BAR = (60, 60, 70)
COLOR_MENU_BTN = (80, 80, 90)
COLOR_MENU_DROPDOWN = (70, 70, 80)
COLOR_SEPARATOR = (50, 50, 60)
COLOR_TOOLTIP_BG = (255, 255, 225)
COLOR_TOOLTIP_BORDER = (0, 0, 0)
COLOR_TOOLTIP_TEXT = (0, 0, 0)

root = tk.Tk()
root.withdraw()


# --- FONCTIONS UTILITAIRES ---

def parse_size_from_filename(filename):
    match = re.search(r"(\d+)x(\d+)", filename)
    if match:
        return int(match.group(1))
    return 1


def load_all_assets_from_folder(root_folder):
    loaded_assets_full = {}
    loaded_assets_thumb = {}
    loaded_sizes = {}
    loaded_libraries = {}
    loaded_descriptions = {}

    if not os.path.exists(root_folder):
        print(f"ERREUR : Dossier '{root_folder}' introuvable.")
        return {}, {}, {}, {}, {}

    for current_root, dirs, files in os.walk(root_folder):
        folder_name = os.path.relpath(current_root, root_folder)
        category = "Base Tiles" if folder_name == "." else folder_name

        if category not in loaded_libraries:
            loaded_libraries[category] = []
        files.sort()

        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_path = os.path.join(current_root, filename)
                key = os.path.splitext(filename)[0]
                try:
                    size_multiplier = parse_size_from_filename(filename)
                    img_original = pygame.image.load(full_path).convert_alpha()

                    real_dim = size_multiplier * TILE_SIZE
                    img_full = pygame.transform.scale(img_original, (real_dim, real_dim))
                    img_thumb = pygame.transform.smoothscale(img_original, (TILE_SIZE, TILE_SIZE))

                    loaded_assets_full[key] = img_full
                    loaded_assets_thumb[key] = img_thumb
                    loaded_sizes[key] = size_multiplier

                    loaded_libraries[category].append(key)
                    loaded_descriptions[key] = f"{key} ({size_multiplier}x{size_multiplier})"
                except Exception as e:
                    print(f"Erreur chargement {filename}: {e}")

    loaded_libraries = {k: v for k, v in loaded_libraries.items() if v}
    return loaded_assets_full, loaded_assets_thumb, loaded_sizes, loaded_libraries, loaded_descriptions


def get_map_bounds(grid):
    if not grid:
        return None
    rows = len(grid)
    if rows == 0:
        return None
    cols = len(grid[0])
    min_x, min_y = cols, rows
    max_x, max_y = -1, -1
    found_any = False

    for y in range(rows):
        for x in range(cols):
            # grid[y][x] est maintenant une LISTE. Si elle n'est pas vide, c'est bon.
            if y < len(grid) and x < len(grid[0]) and len(grid[y][x]) > 0:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
                found_any = True

    if not found_any:
        return None
    return min_x, min_y, max_x, max_y


def resize_grid(old_grid, new_w_pixels, new_h_pixels):
    """
    Redimensionne la grille.
    NOUVEAU : Chaque cellule est initialisée comme une liste vide [] au lieu de None.
    """
    new_cols = (new_w_pixels - UI_WIDTH) // TILE_SIZE
    new_rows = new_h_pixels // TILE_SIZE
    if new_cols < 1:
        new_cols = 1
    if new_rows < 1:
        new_rows = 1

    # Initialisation avec des listes vides
    new_grid = [[[] for _ in range(new_cols)] for _ in range(new_rows)]

    if not old_grid:
        return new_grid

    old_rows = len(old_grid)
    if old_rows == 0:
        return new_grid
    old_cols = len(old_grid[0])

    for y in range(min(old_rows, new_rows)):
        for x in range(min(old_cols, new_cols)):
            # Copie de la liste (pour éviter les références partagées)
            if old_grid[y][x]:
                new_grid[y][x] = list(old_grid[y][x])
            else:
                new_grid[y][x] = []
    return new_grid


def get_draw_offset(size):
    if size % 2 == 0:
        return TILE_SIZE
    else:
        return TILE_SIZE // 2


def get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=0):
    """
    Retourne la tuile sous la souris.
    Priorité au "Top" de la pile.
    Retourne (x, y, tile_data, index_in_stack)
    """
    grid_mouse_y = my - offset_y_ui
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    for y in range(rows - 1, -1, -1):
        for x in range(cols - 1, -1, -1):
            cell_stack = grid[y][x]

            # On parcourt la pile à l'envers (du haut vers le bas)
            if cell_stack:
                for idx in range(len(cell_stack) - 1, -1, -1):
                    item = cell_stack[idx]
                    key = item['key']
                    original = assets_full.get(key)
                    if original:
                        px, py = x * TILE_SIZE, y * TILE_SIZE
                        size = asset_sizes.get(key, 1)
                        offset_draw = get_draw_offset(size)
                        center_x = px + offset_draw
                        center_y = py + offset_draw
                        rect = original.get_rect(center=(center_x, center_y))

                        if rect.collidepoint(mx, grid_mouse_y):
                            return x, y, item, idx
    return None


# --- FONCTIONS FICHIERS ---

def save_project(levels_data):
    file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Map Project", "*.json")])
    if not file_path:
        return
    save_data = {}
    for level_idx, grid in levels_data.items():
        level_cells = []
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        for y in range(rows):
            for x in range(cols):
                # Si la pile contient des éléments
                if len(grid[y][x]) > 0:
                    # On sauvegarde toute la pile pour cette coordonnée
                    stack_data = []
                    for item in grid[y][x]:
                        stack_data.append({
                            "key": item['key'],
                            "angle": item['angle']
                        })

                    level_cells.append({
                        "x": x, "y": y,
                        "stack": stack_data
                    })
        save_data[str(level_idx)] = level_cells
    try:
        with open(file_path, 'w') as f:
            json.dump(save_data, f, indent=4)
        print("Sauvegardé.")
    except Exception as e:
        print(f"Erreur : {e}")


def load_project(map_area_w, map_area_h):
    file_path = filedialog.askopenfilename(filetypes=[("Map Project", "*.json")])
    if not file_path:
        return None
    try:
        with open(file_path, 'r') as f:
            save_data = json.load(f)
        new_levels_data = {}
        for lvl_idx_str, cells in save_data.items():
            lvl_idx = int(lvl_idx_str)
            grid = resize_grid(None, map_area_w, map_area_h)
            rows = len(grid)
            cols = len(grid[0]) if rows > 0 else 0

            for cell_data in cells:
                x, y = cell_data['x'], cell_data['y']
                if 0 <= y < rows and 0 <= x < cols:
                    # Rétro-compatibilité ou nouveau format
                    if "stack" in cell_data:
                        # Nouveau format : liste d'objets
                        grid[y][x] = []
                        for item in cell_data["stack"]:
                            grid[y][x].append({
                                'key': item['key'],
                                'angle': item['angle']
                            })
                    elif "key" in cell_data:
                        # Ancien format (support legacy) : un seul objet
                        grid[y][x] = [{
                            'key': cell_data['key'],
                            'angle': cell_data['angle']
                        }]

            new_levels_data[lvl_idx] = grid
        print("Chargé.")
        return new_levels_data
    except Exception as e:
        print(f"Erreur : {e}")
        return None


def export_current_level_image(grid, assets_full, asset_sizes):
    file_path = filedialog.asksaveasfilename(
        defaultextension=".png",
        filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"), ("BMP Image", "*.bmp")],
        title="Exporter l'étage courant"
    )
    if not file_path:
        return

    bounds = get_map_bounds(grid)
    if not bounds:
        print("Carte vide.")
        return

    min_x, min_y, max_x, max_y = bounds
    margin = TILE_SIZE
    width = (max_x - min_x + 1) * TILE_SIZE + (margin * 2)
    height = (max_y - min_y + 1) * TILE_SIZE + (margin * 2)

    surf = pygame.Surface((width, height))
    surf.fill((20, 20, 20))

    offset_x, offset_y = margin, margin

    # Dessin des piles
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                cell_stack = grid[y][x]
                # On dessine toute la pile du bas vers le haut
                for item in cell_stack:
                    key = item['key']
                    original = assets_full.get(key)
                    if original:
                        draw_x = offset_x + (x - min_x) * TILE_SIZE
                        draw_y = offset_y + (y - min_y) * TILE_SIZE
                        size = asset_sizes.get(key, 1)
                        offset_draw = get_draw_offset(size)
                        angle = item['angle']
                        if angle != 0:
                            img = pygame.transform.rotate(original, angle)
                            rect = img.get_rect(center=(draw_x + offset_draw, draw_y + offset_draw))
                            surf.blit(img, rect)
                        else:
                            rect = original.get_rect(center=(draw_x + offset_draw, draw_y + offset_draw))
                            surf.blit(original, rect)
    try:
        pygame.image.save(surf, file_path)
        print("Export réussi.")
    except Exception as e:
        print(f"Erreur export : {e}")


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Map Editor - Layering & Stacking")
    clock = pygame.time.Clock()

    is_view_mode = False
    current_w, current_h = WINDOW_WIDTH, WINDOW_HEIGHT

    map_view_height = current_h - MENU_HEIGHT

    font = pygame.font.SysFont("Arial", 14)
    menu_font = pygame.font.SysFont("Arial", 14, bold=True)
    title_font = pygame.font.SysFont("Arial", 18, bold=True)
    level_font = pygame.font.SysFont("Arial", 16, bold=True)
    tooltip_font = pygame.font.SysFont("Arial", 12)

    assets_full, assets_thumb, asset_sizes, libraries, descriptions = load_all_assets_from_folder(ASSET_ROOT)

    if not libraries:
        libraries = {"Vide": []}
        lib_names = ["Vide"]
        current_lib_name = "Vide"
    else:
        lib_names = sorted(list(libraries.keys()))
        current_lib_name = lib_names[0]

    levels_data = {}
    current_level_idx = 0
    # Initialisation
    levels_data[0] = resize_grid(None, current_w, map_view_height)
    grid = levels_data[0]

    tool_angles = {}
    for key in assets_full.keys():
        tool_angles[key] = 0

    dragging_texture_key = None
    is_dragging = False
    drag_angle = 0
    hovered_texture_key = None
    hover_start_time = 0
    tooltip_delay = 1000
    scroll_y = 0

    is_menu_open = False
    menu_options = ["Sauvegarder Projet", "Charger Projet", "Export Image (Courant)", "SEPARATOR", "Fermer"]

    running = True

    while running:
        mx, my = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        map_view_width = current_w - UI_WIDTH

        btn_up_rect = pygame.Rect(map_view_width + 10, MENU_HEIGHT + 50, (UI_WIDTH - 30) // 2, 30)
        btn_down_rect = pygame.Rect(map_view_width + 10 + (UI_WIDTH - 30) // 2 + 10, MENU_HEIGHT + 50,
                                    (UI_WIDTH - 30) // 2, 30)
        menu_btn_rect = pygame.Rect(5, 2, 80, MENU_HEIGHT - 4)

        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0

        current_textures = libraries.get(current_lib_name, [])
        rows_needed = (len(current_textures) // 3) + 1
        total_content_height = rows_needed * 74
        visible_area_height = current_h - (MENU_HEIGHT + 130 + len(lib_names) * 35)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                current_w, current_h = event.w, event.h
                if not is_view_mode:
                    screen = pygame.display.set_mode((current_w, current_h), pygame.RESIZABLE)
                    new_map_h = current_h - MENU_HEIGHT
                    grid = resize_grid(grid, current_w, new_map_h)
                    levels_data[current_level_idx] = grid
                else:
                    screen = pygame.display.set_mode((current_w, current_h), pygame.FULLSCREEN)

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    is_view_mode = not is_view_mode
                    if is_view_mode:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1280, 800), pygame.RESIZABLE)
                    current_w, current_h = screen.get_size()
                    if not is_view_mode:
                        new_map_h = current_h - MENU_HEIGHT
                        grid = resize_grid(grid, current_w, new_map_h)
                        levels_data[current_level_idx] = grid

            if not is_view_mode:
                if event.type == pygame.MOUSEWHEEL:
                    if mx > map_view_width and my > MENU_HEIGHT:
                        scroll_y += event.y * 20
                        if scroll_y > 0:
                            scroll_y = 0
                        min_scroll = min(0, -total_content_height + visible_area_height)
                        if scroll_y < min_scroll:
                            scroll_y = min_scroll

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    hovered_texture_key = None

                    if event.button == 1:
                        # MENU
                        if menu_btn_rect.collidepoint(mx, my):
                            is_menu_open = not is_menu_open

                        elif is_menu_open:
                            clicked_option = False
                            current_opt_y = MENU_HEIGHT
                            for idx, option in enumerate(menu_options):
                                if option == "SEPARATOR":
                                    current_opt_y += 10
                                    continue
                                opt_rect = pygame.Rect(5, current_opt_y, 200, 30)
                                if opt_rect.collidepoint(mx, my):
                                    clicked_option = True
                                    is_menu_open = False
                                    if option == "Sauvegarder Projet":
                                        levels_data[current_level_idx] = grid
                                        save_project(levels_data)
                                    elif option == "Charger Projet":
                                        loaded = load_project(current_w, current_h - MENU_HEIGHT)
                                        if loaded:
                                            levels_data = loaded
                                            current_level_idx = 0
                                            if 0 not in levels_data:
                                                levels_data[0] = resize_grid(None, current_w, current_h - MENU_HEIGHT)
                                            grid = levels_data[current_level_idx]
                                    elif option == "Export Image (Courant)":
                                        levels_data[current_level_idx] = grid
                                        export_current_level_image(grid, assets_full, asset_sizes)
                                    elif option == "Fermer":
                                        running = False
                                current_opt_y += 30
                            if not clicked_option:
                                is_menu_open = False

                        elif not is_menu_open:
                            # TOOLBAR
                            if mx > map_view_width and my > MENU_HEIGHT:
                                new_level = None
                                if btn_up_rect.collidepoint(mx, my):
                                    new_level = current_level_idx + 1
                                elif btn_down_rect.collidepoint(mx, my):
                                    new_level = current_level_idx - 1

                                if new_level is not None:
                                    levels_data[current_level_idx] = grid
                                    current_level_idx = new_level
                                    if current_level_idx not in levels_data:
                                        levels_data[current_level_idx] = resize_grid(None, current_w,
                                                                                     current_h - MENU_HEIGHT)
                                    else:
                                        existing = levels_data[current_level_idx]
                                        levels_data[current_level_idx] = resize_grid(existing, current_w,
                                                                                     current_h - MENU_HEIGHT)
                                    grid = levels_data[current_level_idx]

                                base_y_cat = MENU_HEIGHT + 90
                                for i, lib_name in enumerate(lib_names):
                                    btn_rect = pygame.Rect(map_view_width + 10, base_y_cat + i * 35, UI_WIDTH - 20, 30)
                                    if btn_rect.collidepoint(mx, my):
                                        current_lib_name = lib_name
                                        scroll_y = 0

                                start_y_textures = base_y_cat + len(lib_names) * 35 + 40
                                col, row = 0, 0
                                for tex_key in current_textures:
                                    bx = map_view_width + 20 + col * 74
                                    by = start_y_textures + row * 74 + scroll_y
                                    if start_y_textures <= by < current_h:
                                        icon_rect = pygame.Rect(bx, by, 64, 64)
                                        if icon_rect.collidepoint(mx, my):
                                            dragging_texture_key = tex_key
                                            is_dragging = True
                                            drag_angle = tool_angles.get(tex_key, 0)
                                    col += 1
                                    if col > 2:
                                        col = 0
                                        row += 1

                            # MAP
                            elif mx < map_view_width and my > MENU_HEIGHT:
                                # Pick up (Prend le dernier élément)
                                hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=MENU_HEIGHT)
                                if hit:
                                    tx, ty, item, idx = hit
                                    dragging_texture_key = item['key']
                                    drag_angle = item['angle']
                                    is_dragging = True
                                    # On retire cet élément spécifique de la pile
                                    grid[ty][tx].pop(idx)

                    elif event.button == 3 and not is_menu_open:
                        if mx > map_view_width and my > MENU_HEIGHT:
                            # Rotation Toolbar
                            base_y_cat = MENU_HEIGHT + 90
                            start_y_textures = base_y_cat + len(lib_names) * 35 + 40
                            col, row = 0, 0
                            for tex_key in current_textures:
                                bx = map_view_width + 20 + col * 74
                                by = start_y_textures + row * 74 + scroll_y
                                if start_y_textures <= by < current_h:
                                    icon_rect = pygame.Rect(bx, by, 64, 64)
                                    if icon_rect.collidepoint(mx, my):
                                        tool_angles[tex_key] = (tool_angles.get(tex_key, 0) - 90) % 360
                                col += 1
                                if col > 2:
                                    col = 0
                                    row += 1

                        elif mx < map_view_width and my > MENU_HEIGHT:
                            # Delete (Top only)
                            hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=MENU_HEIGHT)
                            if hit:
                                tx, ty, _, idx = hit
                                grid[ty][tx].pop(idx)
                            else:
                                # Fallback au cas où (vide la case)
                                grid_my = my - MENU_HEIGHT
                                gx, gy = mx // TILE_SIZE, grid_my // TILE_SIZE
                                if 0 <= gx < grid_w and 0 <= gy < grid_h:
                                    # Optionnel : vider tout ou juste le dernier ?
                                    if grid[gy][gx]:
                                        grid[gy][gx].pop()

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and is_dragging:
                        if mx < map_view_width and my > MENU_HEIGHT:
                            grid_my = my - MENU_HEIGHT
                            gx, gy = mx // TILE_SIZE, grid_my // TILE_SIZE
                            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                                # AJOUTER A LA LISTE (ON TOP)
                                grid[gy][gx].append({
                                    'key': dragging_texture_key,
                                    'angle': drag_angle
                                })
                        is_dragging = False
                        dragging_texture_key = None

        # ================= DESSIN =================
        if is_view_mode:
            screen.fill(COLOR_VIEW_BG)
            bounds = get_map_bounds(grid)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                content_width = (max_x - min_x + 1) * TILE_SIZE
                content_height = (max_y - min_y + 1) * TILE_SIZE
                offset_x = (current_w - content_width) // 2
                offset_y = (current_h - content_height) // 2
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                            # Dessiner toute la pile
                            for item in grid[y][x]:
                                key = item['key']
                                original = assets_full.get(key)
                                if original:
                                    draw_x = offset_x + (x - min_x) * TILE_SIZE
                                    draw_y = offset_y + (y - min_y) * TILE_SIZE
                                    size = asset_sizes.get(key, 1)
                                    offset_draw = get_draw_offset(size)
                                    angle = item['angle']
                                    if angle != 0:
                                        img = pygame.transform.rotate(original, angle)
                                        rect = img.get_rect(center=(draw_x + offset_draw, draw_y + offset_draw))
                                        screen.blit(img, rect)
                                    else:
                                        rect = original.get_rect(center=(draw_x + offset_draw, draw_y + offset_draw))
                                        screen.blit(original, rect)
        else:
            screen.fill(COLOR_BG)

            # 1. MAP
            for y in range(grid_h):
                for x in range(grid_w):
                    px, py = x * TILE_SIZE, y * TILE_SIZE + MENU_HEIGHT
                    if px < map_view_width and py < current_h:
                        pygame.draw.rect(screen, COLOR_GRID, (px, py, TILE_SIZE, TILE_SIZE), 1)
                        if y < len(grid) and x < len(grid[0]):
                            # DESSINER LA PILE
                            for item in grid[y][x]:
                                key = item['key']
                                original = assets_full.get(key)
                                if original:
                                    size = asset_sizes.get(key, 1)
                                    offset_draw = get_draw_offset(size)
                                    angle = item['angle']
                                    if angle != 0:
                                        img = pygame.transform.rotate(original, angle)
                                        rect = img.get_rect(center=(px + offset_draw, py + offset_draw))
                                        screen.blit(img, rect)
                                    else:
                                        rect = original.get_rect(center=(px + offset_draw, py + offset_draw))
                                        screen.blit(original, rect)

            # 2. TOOLBAR
            pygame.draw.rect(screen, COLOR_UI_BG, (map_view_width, MENU_HEIGHT, UI_WIDTH, current_h - MENU_HEIGHT))
            pygame.draw.line(screen, COLOR_UI_BORDER, (map_view_width, MENU_HEIGHT), (map_view_width, current_h), 2)

            title = title_font.render("NEUTRAL STONE", True, (255, 200, 0))
            screen.blit(title, (map_view_width + 20, MENU_HEIGHT + 15))

            pygame.draw.rect(screen, COLOR_LEVEL_BTN, btn_up_rect, border_radius=5)
            pygame.draw.rect(screen, COLOR_LEVEL_BTN, btn_down_rect, border_radius=5)
            up_txt = level_font.render("Niveau +", True, COLOR_TEXT)
            down_txt = level_font.render("Niveau -", True, COLOR_TEXT)
            screen.blit(up_txt,
                        (btn_up_rect.centerx - up_txt.get_width() // 2, btn_up_rect.centery - up_txt.get_height() // 2))
            screen.blit(down_txt, (
                btn_down_rect.centerx - down_txt.get_width() // 2, btn_down_rect.centery - down_txt.get_height() // 2))
            lvl_info = font.render(f"Étage : {current_level_idx}", True, (0, 255, 0))
            screen.blit(lvl_info, (map_view_width + 20, MENU_HEIGHT + 15 + 20))

            base_y_cat = MENU_HEIGHT + 90
            for i, lib_name in enumerate(lib_names):
                btn_rect = pygame.Rect(map_view_width + 10, base_y_cat + i * 35, UI_WIDTH - 20, 30)
                color = COLOR_BTN_INACTIVE if lib_name != current_lib_name else COLOR_BTN_ACTIVE
                pygame.draw.rect(screen, color, btn_rect, border_radius=5)
                display = lib_name if len(lib_name) < 25 else lib_name[:22] + "..."
                txt = font.render(display, True, COLOR_TEXT)
                screen.blit(txt, (btn_rect.x + 10, btn_rect.y + 7))

            start_y_textures = base_y_cat + len(lib_names) * 35 + 40
            pygame.draw.line(screen, COLOR_UI_BORDER, (map_view_width + 10, start_y_textures - 10),
                             (current_w - 10, start_y_textures - 10))
            clip_rect = pygame.Rect(map_view_width, start_y_textures, UI_WIDTH, current_h - start_y_textures)
            screen.set_clip(clip_rect)

            found_hover = False
            col, row = 0, 0
            for tex_key in current_textures:
                bx = map_view_width + 20 + col * 74
                by = start_y_textures + row * 74 + scroll_y
                if start_y_textures - 70 < by < current_h:
                    icon_rect = pygame.Rect(bx + 2, by + 2, 64, 64)
                    pygame.draw.rect(screen, (30, 30, 30), icon_rect)
                    thumb = assets_thumb.get(tex_key)
                    if thumb:
                        current_angle = tool_angles.get(tex_key, 0)
                        if current_angle != 0:
                            toolbar_img = pygame.transform.rotate(thumb, current_angle)
                            img_rect = toolbar_img.get_rect(center=(bx + 32, by + 32))
                            screen.blit(toolbar_img, img_rect)
                        else:
                            screen.blit(thumb, (bx, by))
                    if icon_rect.collidepoint(mx, my) and not is_dragging and not is_menu_open:
                        found_hover = True
                        if hovered_texture_key != tex_key:
                            hovered_texture_key = tex_key
                            hover_start_time = current_time
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            screen.set_clip(None)

            if not found_hover:
                hovered_texture_key = None
                hover_start_time = 0

            # 3. BARRE DE MENU
            pygame.draw.rect(screen, COLOR_MENU_BAR, (0, 0, current_w, MENU_HEIGHT))
            pygame.draw.line(screen, (30, 30, 30), (0, MENU_HEIGHT), (current_w, MENU_HEIGHT), 1)

            color_btn = COLOR_BTN_ACTIVE if is_menu_open else COLOR_MENU_BTN
            pygame.draw.rect(screen, color_btn, menu_btn_rect, border_radius=3)
            txt_menu = menu_font.render("Fichier", True, COLOR_TEXT)
            screen.blit(txt_menu, (
                menu_btn_rect.centerx - txt_menu.get_width() // 2, menu_btn_rect.centery - txt_menu.get_height() // 2))

            if is_menu_open:
                dropdown_h = 0
                for opt in menu_options:
                    if opt == "SEPARATOR":
                        dropdown_h += 10
                    else:
                        dropdown_h += 30

                dropdown_rect = pygame.Rect(5, MENU_HEIGHT, 200, dropdown_h)
                pygame.draw.rect(screen, COLOR_MENU_DROPDOWN, dropdown_rect)
                pygame.draw.rect(screen, COLOR_UI_BORDER, dropdown_rect, 1)

                current_opt_y = MENU_HEIGHT
                for opt in menu_options:
                    if opt == "SEPARATOR":
                        pygame.draw.line(screen, COLOR_SEPARATOR, (10, current_opt_y + 5), (200, current_opt_y + 5))
                        current_opt_y += 10
                        continue
                    opt_rect = pygame.Rect(5, current_opt_y, 200, 30)
                    if opt_rect.collidepoint(mx, my):
                        pygame.draw.rect(screen, COLOR_BTN_ACTIVE, opt_rect)
                    txt_opt = font.render(opt, True, COLOR_TEXT)
                    screen.blit(txt_opt, (opt_rect.x + 10, opt_rect.y + 7))
                    current_opt_y += 30

            if is_dragging and dragging_texture_key:
                original_drag = assets_full.get(dragging_texture_key)
                if original_drag:
                    size = asset_sizes.get(dragging_texture_key, 1)
                    offset_drag = get_draw_offset(size)
                    if drag_angle != 0:
                        drag_img = pygame.transform.rotate(original_drag, drag_angle)
                    else:
                        drag_img = original_drag.copy()
                    drag_img.set_alpha(180)
                    if size % 2 == 0:
                        rect = drag_img.get_rect(center=(mx + offset_drag - 32, my + offset_drag - 32))
                    else:
                        rect = drag_img.get_rect(center=(mx, my))
                    screen.blit(drag_img, rect)

            if hovered_texture_key and (current_time - hover_start_time > tooltip_delay) and not is_menu_open:
                text_str = descriptions.get(hovered_texture_key, hovered_texture_key)
                text_surf = tooltip_font.render(text_str, True, COLOR_TOOLTIP_TEXT)
                bg_rect = text_surf.get_rect()
                bg_rect.topleft = (mx + 15, my + 15)
                bg_rect.width += 10
                bg_rect.height += 6
                if bg_rect.right > current_w:
                    bg_rect.right = current_w - 5
                if bg_rect.bottom > current_h:
                    bg_rect.bottom = current_h - 5
                pygame.draw.rect(screen, COLOR_TOOLTIP_BG, bg_rect, border_radius=4)
                pygame.draw.rect(screen, COLOR_TOOLTIP_BORDER, bg_rect, 1, border_radius=4)
                screen.blit(text_surf, (bg_rect.x + 5, bg_rect.y + 3))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
