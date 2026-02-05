import pygame
import sys
import os
import re
import json
import time

# --- CONFIGURATION ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
MENU_HEIGHT = 60
UI_WIDTH = 300
TILE_SIZE = 64
ASSET_ROOT = "Neutral Stone"

# Couleurs
COLOR_BG = (30, 30, 30)
COLOR_VIEW_BG = (0, 0, 0)
COLOR_UI_BG = (50, 50, 60)
COLOR_UI_BORDER = (120, 120, 120)
COLOR_GRID = (60, 60, 60)
COLOR_TEXT = (240, 240, 240)
COLOR_BTN_NORMAL = (70, 70, 80)
COLOR_BTN_ACTIVE = (0, 150, 255)
COLOR_BTN_DANGER = (200, 60, 60)  # Rouge
COLOR_BTN_SUCCESS = (60, 160, 60)  # Vert
COLOR_LEVEL_BTN = (100, 60, 60)  # Couleur pour les niveaux
COLOR_MENU_BAR = (60, 60, 70)
COLOR_TOOLTIP_BG = (255, 255, 200)
COLOR_TOOLTIP_TEXT = (0, 0, 0)


# --- FONCTIONS UTILITAIRES ---

def parse_size_from_filename(filename):
    match = re.search(r"(\d+)x(\d+)", filename)
    if match: return int(match.group(1))
    return 1


def load_all_assets_from_folder(root_folder):
    loaded_assets_full = {}
    loaded_assets_thumb = {}
    loaded_sizes = {}
    loaded_libraries = {}
    loaded_descriptions = {}

    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_root_path = os.path.join(base_dir, root_folder)

    if not os.path.exists(full_root_path):
        print(f"Dossier introuvable: {full_root_path}")
        error_surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        error_surf.fill((255, 0, 255))
        return {"error": error_surf}, {"error": error_surf}, {"error": 1}, {"Erreur": ["error"]}, {
            "error": "Image manquante"}

    for current_root, dirs, files in os.walk(full_root_path):
        folder_name = os.path.relpath(current_root, full_root_path)
        category = "Base Tiles" if folder_name == "." else folder_name

        if category not in loaded_libraries: loaded_libraries[category] = []
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
    if not grid: return None
    rows = len(grid)
    if rows == 0: return None
    cols = len(grid[0])
    min_x, min_y = cols, rows
    max_x, max_y = -1, -1
    found_any = False

    for y in range(rows):
        for x in range(cols):
            if y < len(grid) and x < len(grid[0]) and len(grid[y][x]) > 0:
                if x < min_x: min_x = x
                if x > max_x: max_x = x
                if y < min_y: min_y = y
                if y > max_y: max_y = y
                found_any = True

    if not found_any: return None
    return (min_x, min_y, max_x, max_y)


def resize_grid(old_grid, new_w_pixels, new_h_pixels):
    new_cols = max(1, (new_w_pixels - UI_WIDTH) // TILE_SIZE)
    new_rows = max(1, (new_h_pixels - MENU_HEIGHT) // TILE_SIZE)

    new_grid = [[[] for _ in range(new_cols)] for _ in range(new_rows)]

    if not old_grid: return new_grid

    old_rows = len(old_grid)
    if old_rows == 0: return new_grid
    old_cols = len(old_grid[0])

    for y in range(min(old_rows, new_rows)):
        for x in range(min(old_cols, new_cols)):
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
    grid_mouse_y = my - offset_y_ui
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    for y in range(rows - 1, -1, -1):
        for x in range(cols - 1, -1, -1):
            cell_stack = grid[y][x]
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
                            return (x, y, item, idx)
    return None


# --- SYSTÈME FICHIERS LOCAL ---

def get_local_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def save_project_android(levels_data):
    file_path = get_local_path("projet_tablette.json")
    save_data = {}
    for level_idx, grid in levels_data.items():
        level_cells = []
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        for y in range(rows):
            for x in range(cols):
                if len(grid[y][x]) > 0:
                    stack_data = []
                    for item in grid[y][x]:
                        stack_data.append({"key": item['key'], "angle": item['angle']})
                    level_cells.append({"x": x, "y": y, "stack": stack_data})
        save_data[str(level_idx)] = level_cells

    try:
        with open(file_path, 'w') as f:
            json.dump(save_data, f)
        return f"Sauvegardé: {file_path}"
    except Exception as e:
        return f"Erreur: {e}"


def load_project_android(current_w, current_h_map):
    file_path = get_local_path("projet_tablette.json")
    if not os.path.exists(file_path): return None, "Aucun fichier trouvé"

    try:
        with open(file_path, 'r') as f:
            save_data = json.load(f)
        new_levels_data = {}
        for lvl_idx_str, cells in save_data.items():
            lvl_idx = int(lvl_idx_str)
            grid = resize_grid(None, current_w, current_h_map + MENU_HEIGHT)
            rows = len(grid)
            cols = len(grid[0]) if rows > 0 else 0

            for cell_data in cells:
                x, y = cell_data['x'], cell_data['y']
                if 0 <= y < rows and 0 <= x < cols:
                    grid[y][x] = []
                    if "stack" in cell_data:
                        for item in cell_data["stack"]:
                            grid[y][x].append({'key': item['key'], 'angle': item['angle']})
            new_levels_data[lvl_idx] = grid
        return new_levels_data, "Projet chargé !"
    except Exception as e:
        return None, f"Erreur: {e}"


def export_image_android(grid, assets_full, asset_sizes, level_id):
    bounds = get_map_bounds(grid)
    if not bounds: return "Carte vide"

    min_x, min_y, max_x, max_y = bounds
    margin = TILE_SIZE
    width = (max_x - min_x + 1) * TILE_SIZE + (margin * 2)
    height = (max_y - min_y + 1) * TILE_SIZE + (margin * 2)

    surf = pygame.Surface((width, height))
    surf.fill((20, 20, 20))
    offset_x, offset_y = margin, margin

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
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
                            surf.blit(img, rect)
                        else:
                            rect = original.get_rect(center=(draw_x + offset_draw, draw_y + offset_draw))
                            surf.blit(original, rect)

    filename = f"export_niveau_{level_id}.jpg"
    path = get_local_path(filename)
    try:
        pygame.image.save(surf, path)
        return f"Image sauvée: {filename}"
    except Exception as e:
        return f"Err: {e}"


# --- MAIN LOOP ---

def main():
    pygame.init()

    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    current_w, current_h = screen.get_size()

    pygame.display.set_caption("Map Editor Tablet")
    clock = pygame.time.Clock()

    is_view_mode = False

    map_view_width = current_w - UI_WIDTH
    map_view_height = current_h - MENU_HEIGHT

    font = pygame.font.SysFont("Arial", 18)
    menu_font = pygame.font.SysFont("Arial", 20, bold=True)
    title_font = pygame.font.SysFont("Arial", 22, bold=True)
    tooltip_font = pygame.font.SysFont("Arial", 16)

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
    levels_data[0] = resize_grid(None, current_w, map_view_height)
    grid = levels_data[0]

    tool_angles = {}
    for key in assets_full.keys(): tool_angles[key] = 0

    dragging_texture_key = None
    is_dragging = False
    drag_angle = 0
    hovered_texture_key = None
    hover_start_time = 0
    TOOLTIP_DELAY = 800
    scroll_y = 0

    system_msg = ""
    system_msg_timer = 0

    TOOL_MODE_PLACE = 0
    TOOL_MODE_ERASE = 1
    current_tool_mode = TOOL_MODE_PLACE

    running = True

    while running:
        mx, my = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        map_view_width = current_w - UI_WIDTH
        map_view_height = current_h - MENU_HEIGHT

        # --- UI DEFINITION ---

        # MENU HAUT
        btn_width = 140
        btn_save = pygame.Rect(10, 5, btn_width, MENU_HEIGHT - 10)
        btn_load = pygame.Rect(10 + btn_width + 10, 5, btn_width, MENU_HEIGHT - 10)
        btn_export = pygame.Rect(10 + (btn_width + 10) * 2, 5, btn_width, MENU_HEIGHT - 10)

        # BOUTON QUITTER (Top Droite)
        btn_quit = pygame.Rect(current_w - 90, 5, 80, MENU_HEIGHT - 10)
        # BOUTON VOIR (A gauche de Quitter)
        btn_view = pygame.Rect(current_w - 210, 5, 110, MENU_HEIGHT - 10)

        # UI LATERALE
        ui_x = map_view_width
        btn_lvl_up = pygame.Rect(ui_x + 10, MENU_HEIGHT + 10, (UI_WIDTH - 30) // 2, 50)
        btn_lvl_down = pygame.Rect(ui_x + 10 + (UI_WIDTH - 30) // 2 + 10, MENU_HEIGHT + 10, (UI_WIDTH - 30) // 2, 50)

        tool_y = MENU_HEIGHT + 90
        btn_mode_place = pygame.Rect(ui_x + 10, tool_y, 80, 50)
        btn_mode_erase = pygame.Rect(ui_x + 100, tool_y, 80, 50)
        btn_tool_rotate = pygame.Rect(ui_x + 190, tool_y, 100, 50)

        cat_y = tool_y + 70
        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0

        current_textures = libraries.get(current_lib_name, [])
        rows_needed = (len(current_textures) // 3) + 1
        total_content_height = rows_needed * 74
        visible_area_height = current_h - (cat_y + len(lib_names) * 45)

        # --- EVENTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                current_w, current_h = event.w, event.h
                if not is_view_mode:
                    screen = pygame.display.set_mode((current_w, current_h), pygame.FULLSCREEN)
                    grid = resize_grid(grid, current_w, current_h - MENU_HEIGHT)
                    levels_data[current_level_idx] = grid

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    # A. MENU HAUT
                    if my < MENU_HEIGHT:
                        if btn_save.collidepoint(mx, my):
                            levels_data[current_level_idx] = grid
                            system_msg = save_project_android(levels_data)
                            system_msg_timer = current_time + 3000
                        elif btn_load.collidepoint(mx, my):
                            loaded, msg = load_project_android(current_w, map_view_height)
                            system_msg = msg
                            system_msg_timer = current_time + 3000
                            if loaded:
                                levels_data = loaded
                                current_level_idx = 0
                                if 0 not in levels_data: levels_data[0] = resize_grid(None, current_w, map_view_height)
                                grid = levels_data[current_level_idx]
                        elif btn_export.collidepoint(mx, my):
                            levels_data[current_level_idx] = grid
                            system_msg = export_image_android(grid, assets_full, asset_sizes, current_level_idx)
                            system_msg_timer = current_time + 3000
                        elif btn_view.collidepoint(mx, my):
                            is_view_mode = not is_view_mode
                            if not is_view_mode:
                                screen = pygame.display.set_mode((current_w, current_h), pygame.FULLSCREEN)

                        # --- CLIC QUITTER ---
                        elif btn_quit.collidepoint(mx, my):
                            running = False

                    # B. MAP
                    elif mx < map_view_width and not is_view_mode:
                        if current_tool_mode == TOOL_MODE_ERASE:
                            hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=MENU_HEIGHT)
                            if hit:
                                tx, ty, _, idx = hit
                                grid[ty][tx].pop(idx)
                        elif current_tool_mode == TOOL_MODE_PLACE:
                            hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=MENU_HEIGHT)
                            if hit:
                                tx, ty, item, idx = hit
                                dragging_texture_key = item['key']
                                drag_angle = item['angle']
                                is_dragging = True
                                grid[ty][tx].pop(idx)
                            elif dragging_texture_key is not None:
                                is_dragging = True

                    # C. UI DROITE
                    elif mx > map_view_width and not is_view_mode:

                        if btn_lvl_up.collidepoint(mx, my):
                            new_level = current_level_idx + 1
                            if new_level is not None:
                                levels_data[current_level_idx] = grid
                                current_level_idx = new_level
                                if current_level_idx not in levels_data:
                                    levels_data[current_level_idx] = resize_grid(None, current_w, map_view_height)
                                else:
                                    existing = levels_data[current_level_idx]
                                    levels_data[current_level_idx] = resize_grid(existing, current_w, map_view_height)
                                grid = levels_data[current_level_idx]

                        elif btn_lvl_down.collidepoint(mx, my):
                            new_level = current_level_idx - 1
                            if new_level is not None:
                                levels_data[current_level_idx] = grid
                                current_level_idx = new_level
                                if current_level_idx not in levels_data:
                                    levels_data[current_level_idx] = resize_grid(None, current_w, map_view_height)
                                else:
                                    existing = levels_data[current_level_idx]
                                    levels_data[current_level_idx] = resize_grid(existing, current_w, map_view_height)
                                grid = levels_data[current_level_idx]

                        elif btn_mode_place.collidepoint(mx, my):
                            current_tool_mode = TOOL_MODE_PLACE
                        elif btn_mode_erase.collidepoint(mx, my):
                            current_tool_mode = TOOL_MODE_ERASE
                        elif btn_tool_rotate.collidepoint(mx, my):
                            if dragging_texture_key:
                                drag_angle = (drag_angle - 90) % 360
                                tool_angles[dragging_texture_key] = (tool_angles.get(dragging_texture_key,
                                                                                     0) - 90) % 360

                        for i, lib_name in enumerate(lib_names):
                            btn_rect = pygame.Rect(ui_x + 10, cat_y + i * 45, UI_WIDTH - 20, 40)
                            if btn_rect.collidepoint(mx, my):
                                current_lib_name = lib_name
                                scroll_y = 0

                        start_y_tex = cat_y + len(lib_names) * 45 + 10
                        col, row = 0, 0
                        for tex_key in current_textures:
                            bx = ui_x + 20 + col * 74
                            by = start_y_tex + row * 74 + scroll_y
                            if start_y_tex <= by < current_h:
                                icon_rect = pygame.Rect(bx, by, 64, 64)
                                if icon_rect.collidepoint(mx, my):
                                    dragging_texture_key = tex_key
                                    current_tool_mode = TOOL_MODE_PLACE
                                    drag_angle = tool_angles.get(tex_key, 0)
                                    is_dragging = True
                            col += 1
                            if col > 2: col = 0; row += 1

                elif event.button == 4 and mx > map_view_width:
                    scroll_y = min(0, scroll_y + 30)
                elif event.button == 5 and mx > map_view_width:
                    scroll_y -= 30

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and is_dragging:
                    if mx < map_view_width and my > MENU_HEIGHT:
                        grid_my = my - MENU_HEIGHT
                        gx, gy = mx // TILE_SIZE, grid_my // TILE_SIZE
                        if 0 <= gx < grid_w and 0 <= gy < grid_h:
                            grid[gy][gx].append({'key': dragging_texture_key, 'angle': drag_angle})
                    is_dragging = False

        # --- DESSIN ---
        screen.fill(COLOR_BG)

        if is_view_mode:
            screen.fill(COLOR_VIEW_BG)
            bounds = get_map_bounds(grid)
            if bounds:
                min_x, min_y, max_x, max_y = bounds
                offset_x = (current_w - ((max_x - min_x + 1) * TILE_SIZE)) // 2
                offset_y = (current_h - ((max_y - min_y + 1) * TILE_SIZE)) // 2
                for y in range(min_y, max_y + 1):
                    for x in range(min_x, max_x + 1):
                        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
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

            # Bouton retour flottant en View Mode
            back_rect = pygame.Rect(current_w - 60, 10, 50, 50)
            pygame.draw.rect(screen, (50, 50, 50), back_rect, border_radius=5)
            pygame.draw.rect(screen, (200, 200, 200), (current_w - 50, 20, 30, 30))
            if pygame.mouse.get_pressed()[0] and back_rect.collidepoint(mx, my):
                is_view_mode = False
                screen = pygame.display.set_mode((current_w, current_h), pygame.FULLSCREEN)

        else:
            # MAP AREA
            for y in range(grid_h):
                for x in range(grid_w):
                    px, py = x * TILE_SIZE, y * TILE_SIZE + MENU_HEIGHT
                    if px < map_view_width and py < current_h:
                        pygame.draw.rect(screen, COLOR_GRID, (px, py, TILE_SIZE, TILE_SIZE), 1)
                        if y < len(grid) and x < len(grid[0]):
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

            # UI BARRE DROITE
            pygame.draw.rect(screen, COLOR_UI_BG, (map_view_width, MENU_HEIGHT, UI_WIDTH, current_h))
            pygame.draw.line(screen, COLOR_UI_BORDER, (map_view_width, MENU_HEIGHT), (map_view_width, current_h), 2)

            pygame.draw.rect(screen, COLOR_LEVEL_BTN, btn_lvl_up, border_radius=8)
            pygame.draw.rect(screen, COLOR_LEVEL_BTN, btn_lvl_down, border_radius=8)
            t1 = menu_font.render("ETAGE +", True, COLOR_TEXT)
            t2 = menu_font.render("ETAGE -", True, COLOR_TEXT)
            screen.blit(t1, (btn_lvl_up.centerx - t1.get_width() // 2, btn_lvl_up.centery - t1.get_height() // 2))
            screen.blit(t2, (btn_lvl_down.centerx - t2.get_width() // 2, btn_lvl_down.centery - t2.get_height() // 2))

            lvl_txt = font.render(f"Niveau : {current_level_idx}", True, (100, 255, 100))
            screen.blit(lvl_txt, (map_view_width + 10, MENU_HEIGHT + 65))

            c_place = COLOR_BTN_ACTIVE if current_tool_mode == TOOL_MODE_PLACE else COLOR_BTN_NORMAL
            c_erase = COLOR_BTN_DANGER if current_tool_mode == TOOL_MODE_ERASE else COLOR_BTN_NORMAL

            pygame.draw.rect(screen, c_place, btn_mode_place, border_radius=5)
            pygame.draw.rect(screen, c_erase, btn_mode_erase, border_radius=5)
            pygame.draw.rect(screen, COLOR_BTN_NORMAL, btn_tool_rotate, border_radius=5)

            screen.blit(font.render("POSER", True, COLOR_TEXT), (btn_mode_place.x + 10, btn_mode_place.y + 15))
            screen.blit(font.render("GOMME", True, COLOR_TEXT), (btn_mode_erase.x + 5, btn_mode_erase.y + 15))
            screen.blit(font.render("PIVOTER", True, COLOR_TEXT), (btn_tool_rotate.x + 10, btn_tool_rotate.y + 15))

            for i, lib_name in enumerate(lib_names):
                btn_rect = pygame.Rect(ui_x + 10, cat_y + i * 45, UI_WIDTH - 20, 40)
                color = COLOR_BTN_ACTIVE if lib_name == current_lib_name else COLOR_BTN_NORMAL
                pygame.draw.rect(screen, color, btn_rect, border_radius=5)
                screen.blit(font.render(lib_name, True, COLOR_TEXT), (btn_rect.x + 10, btn_rect.y + 10))

            start_y_tex = cat_y + len(lib_names) * 45 + 10
            clip_rect = pygame.Rect(ui_x, start_y_tex, UI_WIDTH, current_h - start_y_tex)
            screen.set_clip(clip_rect)

            col, row = 0, 0
            for tex_key in current_textures:
                bx = ui_x + 20 + col * 74
                by = start_y_tex + row * 74 + scroll_y
                if start_y_tex - 70 < by < current_h:
                    icon_rect = pygame.Rect(bx + 2, by + 2, 64, 64)
                    if tex_key == dragging_texture_key:
                        pygame.draw.rect(screen, COLOR_BTN_ACTIVE, (bx, by, 68, 68), border_radius=3)
                    pygame.draw.rect(screen, (40, 40, 40), icon_rect)
                    thumb = assets_thumb.get(tex_key)
                    if thumb:
                        rot = tool_angles.get(tex_key, 0)
                        if rot != 0:
                            img = pygame.transform.rotate(thumb, rot)
                            r = img.get_rect(center=(bx + 34, by + 34))
                            screen.blit(img, r)
                        else:
                            screen.blit(thumb, (bx + 2, by + 2))
                col += 1
                if col > 2: col = 0; row += 1
            screen.set_clip(None)

            # 3. BARRE DE MENU HAUT
            pygame.draw.rect(screen, COLOR_MENU_BAR, (0, 0, current_w, MENU_HEIGHT))

            pygame.draw.rect(screen, COLOR_BTN_SUCCESS, btn_save, border_radius=5)
            pygame.draw.rect(screen, COLOR_BTN_NORMAL, btn_load, border_radius=5)
            pygame.draw.rect(screen, COLOR_BTN_NORMAL, btn_export, border_radius=5)
            pygame.draw.rect(screen, (50, 50, 150), btn_view, border_radius=5)
            # DESSIN BOUTON QUITTER
            pygame.draw.rect(screen, COLOR_BTN_DANGER, btn_quit, border_radius=5)

            screen.blit(menu_font.render("SAUVER", True, COLOR_TEXT), (btn_save.x + 20, btn_save.y + 15))
            screen.blit(menu_font.render("CHARGER", True, COLOR_TEXT), (btn_load.x + 15, btn_load.y + 15))
            screen.blit(menu_font.render("EXPORT", True, COLOR_TEXT), (btn_export.x + 20, btn_export.y + 15))
            screen.blit(menu_font.render("VOIR", True, COLOR_TEXT), (btn_view.x + 30, btn_view.y + 15))
            screen.blit(menu_font.render("QUITTER", True, COLOR_TEXT), (btn_quit.x + 5, btn_quit.y + 15))

            if is_dragging and dragging_texture_key:
                original_drag = assets_full.get(dragging_texture_key)
                if original_drag:
                    size = asset_sizes.get(dragging_texture_key, 1)
                    offset_drag = get_draw_offset(size)
                    if drag_angle != 0:
                        drag_img = pygame.transform.rotate(original_drag, drag_angle)
                    else:
                        drag_img = original_drag.copy()
                    drag_img.set_alpha(150)
                    if size % 2 == 0:
                        rect = drag_img.get_rect(center=(mx + offset_drag - 32, my + offset_drag - 32))
                    else:
                        rect = drag_img.get_rect(center=(mx, my))
                    screen.blit(drag_img, rect)

            if current_time < system_msg_timer:
                msg_surf = title_font.render(system_msg, True, (255, 255, 255))
                msg_bg = pygame.Rect(current_w // 2 - msg_surf.get_width() // 2 - 20, current_h // 2 - 30,
                                     msg_surf.get_width() + 40, 60)
                s = pygame.Surface((msg_bg.width, msg_bg.height))
                s.set_alpha(200)
                s.fill((0, 0, 0))
                screen.blit(s, (msg_bg.x, msg_bg.y))
                screen.blit(msg_surf,
                            (msg_bg.centerx - msg_surf.get_width() // 2, msg_bg.centery - msg_surf.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
