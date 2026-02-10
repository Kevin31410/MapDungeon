import pygame
import sys
import os
import re
import json
import time
import copy
import math
import base64
from io import BytesIO

# --- CONFIGURATION INITIALE ---
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800
UI_WIDTH = 320
MENU_HEIGHT = 50  # Un peu plus haut pour le confort
TILE_SIZE = 64
ASSET_ROOT = "Neutral Stone"

# CONFIGURATION LAYOUT (PIXEL PERFECT)
BTN_HEIGHT = 40  # Boutons plus gros pour faciliter le clic
UI_MARGIN = 10
UI_GAP_X = 5
UI_GAP_Y = 10

# Configuration Historique
MAX_HISTORY = 30

# --- CONSTANTES DES COUCHES ---
LAYER_GROUND = 0
LAYER_OBJECTS = 1
LAYER_TOKENS = 2

# --- THEME "DARK FANTASY" ---
COLOR_BG = (20, 20, 25)
COLOR_VIEW_BG = (10, 10, 15)
COLOR_UI_BG = (35, 35, 40)
COLOR_UI_BORDER = (80, 80, 80)
COLOR_GRID = (80, 80, 80)
COLOR_TEXT = (220, 220, 200)
COLOR_BTN_NORMAL = (50, 50, 60)
COLOR_BTN_ACTIVE = (180, 140, 50)
COLOR_BTN_LAYER_ACTIVE = (100, 100, 180)
COLOR_BTN_DANGER = (150, 40, 40)
COLOR_BTN_SUCCESS = (60, 120, 60)
COLOR_BTN_WARNING = (160, 100, 20)
COLOR_WALL_PREVIEW = (255, 255, 255)
COLOR_WALL_FIXED = (200, 50, 50)
COLOR_OVERLAY = (0, 0, 0, 200)
COLOR_DROPDOWN_BG = (45, 45, 50)
COLOR_LEVEL_BTN = (80, 40, 40)
COLOR_MENU_BAR = (25, 25, 30)
COLOR_PANEL_DARK = (25, 25, 30)

COLOR_BORDER_GOLD = (160, 120, 40)
COLOR_BORDER_ACTIVE = (255, 215, 0)

# --- VARIABLES GLOBALES ---
undo_stack = []
redo_stack = []


# --- FONCTIONS UTILITAIRES ---

def draw_text_centered(surface, text, font, color, container_rect):
    text_surf = font.render(text, True, color)
    text_rect = text_surf.get_rect(center=container_rect.center)
    surface.blit(text_surf, text_rect)


def draw_fantasy_button(surface, rect, text, font, text_color, base_color, border_color, is_hovered=False):
    """Dessine un bouton style RPG."""
    x, y, w, h = rect.x, rect.y, rect.width, rect.height
    cut = 8

    points = [
        (x + cut, y), (x + w - cut, y),
        (x + w, y + cut), (x + w, y + h - cut),
        (x + w - cut, y + h), (x + cut, y + h),
        (x, y + h - cut), (x, y + cut)
    ]

    final_base = base_color
    if is_hovered:
        # Eclaircit le bouton au survol
        final_base = (min(255, base_color[0] + 30), min(255, base_color[1] + 30), min(255, base_color[2] + 30))

    pygame.draw.polygon(surface, final_base, points)

    final_border = (255, 255, 200) if is_hovered else border_color
    pygame.draw.polygon(surface, final_border, points, 2)

    text_surf = font.render(text, True, text_color)
    text_rect = text_surf.get_rect(center=rect.center)

    # Ombre du texte
    shadow_surf = font.render(text, True, (0, 0, 0))
    shadow_rect = text_surf.get_rect(center=(rect.centerx + 1, rect.centery + 1))

    surface.blit(shadow_surf, shadow_rect)
    surface.blit(text_surf, text_rect)


def parse_size_from_filename(filename):
    match = re.search(r"(\d+)x(\d+)", filename)
    if match: return int(match.group(1))
    return 1


def load_all_assets_from_folder(root_folder):
    loaded_assets_full = {}
    loaded_assets_thumb = {}
    loaded_sizes = {}
    loaded_libraries = {}

    # --- MODIFICATION POUR PYINSTALLER ---
    # On vérifie si on est dans un EXE "gelé"
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Si oui, le dossier de base est le dossier temporaire d'extraction
        base_dir = sys._MEIPASS
    else:
        # Sinon, c'est le dossier du script normal
        base_dir = os.path.dirname(os.path.abspath(__file__))
    # -------------------------------------

    full_root_path = os.path.join(base_dir, root_folder)

    if not os.path.exists(full_root_path):
        # Protection : si le dossier n'est pas trouvé, on le dit pour le debug
        print(f"ATTENTION : Dossier d'assets introuvable : {full_root_path}")
        return {}, {}, {}, {}

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
                except Exception as e:
                    print(f"Erreur chargement {filename}: {e}")

    loaded_libraries = {k: v for k, v in loaded_libraries.items() if v}
    return loaded_assets_full, loaded_assets_thumb, loaded_sizes, loaded_libraries


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
    return min_x, min_y, max_x, max_y


def resize_grid(old_grid, new_w_pixels, new_h_pixels):
    if new_w_pixels < TILE_SIZE: new_w_pixels = TILE_SIZE
    if new_h_pixels < TILE_SIZE: new_h_pixels = TILE_SIZE
    new_cols = new_w_pixels // TILE_SIZE
    new_rows = new_h_pixels // TILE_SIZE
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


def get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=0, offset_x_ui=0, target_layer=None):
    grid_mouse_x = mx - offset_x_ui
    grid_mouse_y = my - offset_y_ui
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    for y in range(rows - 1, -1, -1):
        for x in range(cols - 1, -1, -1):
            cell_stack = grid[y][x]
            if cell_stack:
                for idx in range(len(cell_stack) - 1, -1, -1):
                    item = cell_stack[idx]
                    item_layer = item.get('layer', LAYER_GROUND)
                    if target_layer is not None and item_layer != target_layer:
                        continue
                    key = item['key']
                    original = assets_full.get(key)
                    if original:
                        px, py = x * TILE_SIZE, y * TILE_SIZE
                        size = asset_sizes.get(key, 1)
                        offset_draw = get_draw_offset(size)
                        center_x = px + offset_draw
                        center_y = py + offset_draw
                        rect = original.get_rect(center=(center_x, center_y))
                        if rect.collidepoint(grid_mouse_x, grid_mouse_y):
                            return x, y, item, idx
    return None


def distance_point_to_segment(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    if dx == 0 and dy == 0: return math.hypot(px - x1, py - y1)
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    return math.hypot(px - closest_x, py - closest_y)


# --- HISTORIQUE ---
def save_history(grid, walls):
    global undo_stack, redo_stack
    state = {
        "grid": copy.deepcopy(grid),
        "walls": copy.deepcopy(walls)
    }
    undo_stack.append(state)
    if len(undo_stack) > MAX_HISTORY: undo_stack.pop(0)
    redo_stack.clear()


def perform_undo(curr_grid, curr_walls):
    global undo_stack, redo_stack
    if len(undo_stack) > 0:
        state_redo = {"grid": copy.deepcopy(curr_grid), "walls": copy.deepcopy(curr_walls)}
        redo_stack.append(state_redo)
        prev_state = undo_stack.pop()
        return prev_state["grid"], prev_state["walls"]
    return curr_grid, curr_walls


def perform_redo(curr_grid, curr_walls):
    global undo_stack, redo_stack
    if len(redo_stack) > 0:
        state_undo = {"grid": copy.deepcopy(curr_grid), "walls": copy.deepcopy(curr_walls)}
        undo_stack.append(state_undo)
        next_state = redo_stack.pop()
        return next_state["grid"], next_state["walls"]
    return curr_grid, curr_walls


# --- FICHIERS ---
def get_local_path(filename):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, filename)


def list_json_files():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    files = []
    try:
        for f in os.listdir(base_dir):
            if f.endswith(".json"): files.append(f)
    except:
        pass
    files.sort()
    return files


def save_project_named(levels_data, walls_data, custom_name):
    """Sauvegarde avec un nom choisi par l'utilisateur."""
    if not custom_name.endswith(".json"):
        custom_name += ".json"

    file_path = get_local_path(custom_name)

    save_data = {}
    levels_export = {}
    for level_idx, grid in levels_data.items():
        level_cells = []
        rows = len(grid)
        cols = len(grid[0]) if rows > 0 else 0
        for y in range(rows):
            for x in range(cols):
                if len(grid[y][x]) > 0:
                    stack_data = []
                    for item in grid[y][x]:
                        stack_data.append({
                            "key": item['key'],
                            "angle": item['angle'],
                            "layer": item.get('layer', 0)
                        })
                    level_cells.append({"x": x, "y": y, "stack": stack_data})
        levels_export[str(level_idx)] = level_cells

    save_data["levels"] = levels_export
    save_data["walls"] = walls_data

    try:
        with open(file_path, 'w') as f:
            json.dump(save_data, f)
        return f"Sauvé: {custom_name}"
    except Exception as e:
        return f"Err: {e}"


def load_project_file(filename, current_w, current_h_map):
    file_path = get_local_path(filename)
    try:
        with open(file_path, 'r') as f:
            save_data = json.load(f)

        if "levels" not in save_data:
            raw_levels = save_data
            loaded_walls = {}
        else:
            raw_levels = save_data["levels"]
            loaded_walls = save_data.get("walls", {})

        new_levels_data = {}
        for lvl_idx_str, cells in raw_levels.items():
            lvl_idx = int(lvl_idx_str)
            grid = resize_grid(None, current_w, current_h_map)
            rows = len(grid)
            cols = len(grid[0]) if rows > 0 else 0
            for cell_data in cells:
                x, y = cell_data['x'], cell_data['y']
                if 0 <= y < rows and 0 <= x < cols:
                    grid[y][x] = []
                    if "stack" in cell_data:
                        for item in cell_data["stack"]:
                            grid[y][x].append({
                                'key': item['key'],
                                'angle': item['angle'],
                                'layer': item.get('layer', 0)
                            })
            new_levels_data[lvl_idx] = grid

        return new_levels_data, loaded_walls, f"Chargé: {filename}"
    except Exception as e:
        return None, {}, f"Err: {e}"


# --- EXPORT UNIVERSAL VTT (.dd2vtt) ---
def export_universal_vtt_named(grid, walls, assets_full, asset_sizes, level_id, custom_name):
    """Export VTT avec un nom choisi par l'utilisateur."""
    if not custom_name.endswith(".dd2vtt"):
        custom_name += ".dd2vtt"

    # 1. Calcul des bornes de la map
    bounds = get_map_bounds(grid)
    if not bounds: return "Carte vide"
    min_x, min_y, max_x, max_y = bounds

    # 2. Dimensions réelles de l'image exportée
    width_px = (max_x - min_x + 1) * TILE_SIZE
    height_px = (max_y - min_y + 1) * TILE_SIZE

    # 3. Rendu de la map sur une Surface Pygame (sans grille, sans UI)
    surf = pygame.Surface((width_px, height_px))
    surf.fill(COLOR_VIEW_BG)  # Fond sombre

    # Offsets pour décaler les dessins (car l'image commence à 0,0, pas à min_x, min_y)
    offset_grid_x = min_x * TILE_SIZE
    offset_grid_y = min_y * TILE_SIZE

    # Boucle de dessin standard (reprise de la boucle main)
    for layer_pass in [LAYER_GROUND, LAYER_OBJECTS, LAYER_TOKENS]:
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
                    cell_stack = grid[y][x]
                    for item in cell_stack:
                        if item.get('layer', 0) == layer_pass:
                            key = item['key']
                            original = assets_full.get(key)
                            if original:
                                # Position relative à l'image exportée
                                draw_x = (x * TILE_SIZE) - offset_grid_x
                                draw_y = (y * TILE_SIZE) - offset_grid_y

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

    # 4. Conversion de l'image en Base64 (PNG)
    image_buffer = BytesIO()
    pygame.image.save(surf, image_buffer, "PNG")
    b64_image_str = base64.b64encode(image_buffer.getvalue()).decode("utf-8")

    # 5. Conversion des MURS (Walls) pour le format VTT
    # Le format attend des coordonnées en pixels relatifs à l'image.
    vtt_walls = []
    for w in walls:
        # Conversion coordonnées globales -> locales image
        p1 = {
            "x": w['x1'] - offset_grid_x,
            "y": w['y1'] - offset_grid_y
        }
        p2 = {
            "x": w['x2'] - offset_grid_x,
            "y": w['y2'] - offset_grid_y
        }
        # Format "line" simple
        vtt_walls.append({"p1": p1, "p2": p2})

    # 6. Structure JSON finale (.dd2vtt / Universal VTT)
    vtt_data = {
        "format": "dd2vtt",
        "resolution": {
            "map_origin": {"x": 0, "y": 0},
            "map_size": {"x": width_px, "y": height_px},
            "pixels_per_grid": TILE_SIZE,
        },
        "line_of_sight": vtt_walls,
        "portals": [],
        "lights": [],
        "image": f"data:image/png;base64,{b64_image_str}"
    }

    # 7. Sauvegarde
    path = get_local_path(custom_name)
    try:
        with open(path, 'w') as f:
            json.dump(vtt_data, f)
        return f"Export OK: {custom_name}"
    except Exception as e:
        return f"Err: {e}"


# --- MAIN LOOP ---

def main():
    pygame.init()

    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Map Dungeon")
    clock = pygame.time.Clock()

    current_w, current_h = screen.get_size()

    is_view_mode = False
    is_immersion_mode = False
    is_file_menu_open = False
    file_list_cache = []
    is_category_menu_open = False

    # Etats
    current_layer = LAYER_GROUND

    # Données
    walls_data = {}

    # Outils Murs
    wall_start_point = None

    # --- VARIABLES POUR LA SAISIE DE TEXTE ---
    input_active = False
    input_text = ""
    input_action = None  # "SAVE" ou "EXPORT"

    # CURSEUR
    cursor_pos = 0
    cursor_visible = True
    cursor_timer = 0

    map_view_height = current_h - MENU_HEIGHT

    # --- CHARGEMENT POLICES D&D ---
    fantasy_font_str = "modesto, bookantiqua, palatino, georgia, serif"
    font = pygame.font.SysFont(fantasy_font_str, 12, bold=True)
    menu_font = pygame.font.SysFont(fantasy_font_str, 12, bold=True)
    title_font = pygame.font.SysFont(fantasy_font_str, 18, bold=True)

    input_font = pygame.font.SysFont(fantasy_font_str, 24, bold=True)

    assets_full, assets_thumb, asset_sizes, libraries = load_all_assets_from_folder(ASSET_ROOT)

    if not libraries:
        libraries = {"Vide": []}
        lib_names = ["Vide"]
        current_lib_name = "Vide"
    else:
        lib_names = sorted(list(libraries.keys()))
        current_lib_name = lib_names[0]

    levels_data = {}
    current_level_idx = 0
    edit_map_h = current_h - MENU_HEIGHT
    edit_map_w = current_w - UI_WIDTH
    levels_data[0] = resize_grid(None, edit_map_w, edit_map_h)
    grid = levels_data[0]

    walls_data[0] = []

    tool_angles = {}
    for key in assets_full.keys(): tool_angles[key] = 0

    dragging_texture_key = None
    is_dragging = False
    drag_angle = 0
    scroll_y = 0

    system_msg = ""
    system_msg_timer = 0

    # Modes Outils
    TOOL_MODE_PLACE = 0
    TOOL_MODE_ERASE = 1
    TOOL_MODE_WALL = 2

    current_tool_mode = TOOL_MODE_PLACE

    COLS_PER_ROW = 4
    available_width = UI_WIDTH - 20
    col_step = available_width // COLS_PER_ROW

    running = True

    while running:
        mx, my = pygame.mouse.get_pos()
        current_time = pygame.time.get_ticks()

        # CLIGNOTEMENT CURSEUR (500ms)
        if current_time - cursor_timer > 500:
            cursor_visible = not cursor_visible
            cursor_timer = current_time

        if is_immersion_mode:
            map_view_width = current_w
            map_view_height = current_h
            ui_offset_x = 0
            ui_offset_y = 0
        else:
            map_view_width = current_w - UI_WIDTH
            map_view_height = current_h - MENU_HEIGHT
            ui_offset_x = 0
            ui_offset_y = MENU_HEIGHT

        # --- CALCUL AUTOMATIQUE DU LAYOUT (AVANT L'EVENT LOOP) ---
        # NOTE IMPORTANTE : Tout calcul de Rect se fait ICI pour être sûr que
        # le dessin et le clic utilisent EXACTEMENT les mêmes coordonnées.

        # 1. MENU HAUT
        nb_btns = 7
        spacing = 5
        btn_w = (current_w - 20 - (spacing * (nb_btns - 1))) // nb_btns

        btns_top = []
        for i in range(nb_btns):
            btns_top.append(pygame.Rect(10 + i * (btn_w + spacing), 5, btn_w, MENU_HEIGHT - 10))

        btn_save, btn_load, btn_export, btn_undo, btn_redo, btn_immersion, btn_quit = btns_top

        # BOUTON DE SORTIE IMMERSION
        btn_exit_immersion = pygame.Rect(current_w - 40, 10, 30, 30)

        # 2. UI LATERALE
        work_width = UI_WIDTH - (UI_MARGIN * 2)
        ui_x = map_view_width
        current_y_ui = MENU_HEIGHT + UI_GAP_Y

        # Ligne 1 : NIVEAUX
        lvl_text_width = (work_width - 2 * UI_GAP_X) // 3
        btn_lvl_w = lvl_text_width

        btn_lvl_down = pygame.Rect(ui_x + UI_MARGIN, current_y_ui, btn_lvl_w, BTN_HEIGHT)
        lvl_text_rect = pygame.Rect(btn_lvl_down.right + UI_GAP_X, current_y_ui, lvl_text_width, BTN_HEIGHT)
        btn_lvl_up = pygame.Rect(lvl_text_rect.right + UI_GAP_X, current_y_ui, btn_lvl_w, BTN_HEIGHT)

        current_y_ui += BTN_HEIGHT + UI_GAP_Y

        # Ligne 2 : Couches
        btn_layer_w = (work_width - 2 * UI_GAP_X) // 3
        btn_layer_ground = pygame.Rect(ui_x + UI_MARGIN, current_y_ui, btn_layer_w, BTN_HEIGHT)
        btn_layer_obj = pygame.Rect(ui_x + UI_MARGIN + btn_layer_w + UI_GAP_X, current_y_ui, btn_layer_w, BTN_HEIGHT)
        btn_layer_token = pygame.Rect(ui_x + UI_MARGIN + 2 * (btn_layer_w + UI_GAP_X), current_y_ui, btn_layer_w,
                                      BTN_HEIGHT)
        current_y_ui += BTN_HEIGHT + UI_GAP_Y

        # Ligne 3 : Outils 1
        btn_tool_w = (work_width - 2 * UI_GAP_X) // 3
        btn_mode_place = pygame.Rect(ui_x + UI_MARGIN, current_y_ui, btn_tool_w, BTN_HEIGHT)
        btn_mode_erase = pygame.Rect(ui_x + UI_MARGIN + btn_tool_w + UI_GAP_X, current_y_ui, btn_tool_w, BTN_HEIGHT)
        btn_tool_rotate = pygame.Rect(ui_x + UI_MARGIN + 2 * (btn_tool_w + UI_GAP_X), current_y_ui, btn_tool_w,
                                      BTN_HEIGHT)
        current_y_ui += BTN_HEIGHT + UI_GAP_Y

        # Ligne 4 : Outils 2
        btn_tool_wall = pygame.Rect(ui_x + UI_MARGIN, current_y_ui, work_width, BTN_HEIGHT)
        current_y_ui += BTN_HEIGHT + UI_GAP_Y

        # Ligne 5 : Dropdown
        btn_category_dropdown = pygame.Rect(ui_x + UI_MARGIN, current_y_ui, work_width, BTN_HEIGHT)
        current_y_ui += BTN_HEIGHT + UI_GAP_Y

        # TEXTURES
        start_y_tex = current_y_ui

        # 3. MODAL INPUT
        modal_w, modal_h = 400, 200
        modal_x = (current_w - modal_w) // 2
        modal_y = (current_h - modal_h) // 2

        input_box_rect = pygame.Rect(modal_x + 40, modal_y + 80, modal_w - 80, 40)
        btn_cancel_rect = pygame.Rect(modal_x + 20, modal_y + 140, 170, 40)
        btn_ok_rect = pygame.Rect(modal_x + 210, modal_y + 140, 170, 40)

        # 4. GRID DATA
        grid_h = len(grid)
        grid_w = len(grid[0]) if grid_h > 0 else 0

        options_to_show = [n for n in lib_names if n != current_lib_name]
        current_textures = libraries.get(current_lib_name, [])

        # --- CALCUL LIMITES SCROLL ---
        view_h_px = current_h - start_y_tex
        nb_rows = (len(current_textures) + COLS_PER_ROW - 1) // COLS_PER_ROW
        content_h_px = nb_rows * 74
        max_scroll_val = max(0, content_h_px - view_h_px + 20)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                current_w, current_h = event.w, event.h
                screen = pygame.display.set_mode((current_w, current_h), pygame.RESIZABLE)
                if not is_immersion_mode:
                    grid = resize_grid(grid, current_w - UI_WIDTH, current_h - MENU_HEIGHT)
                    levels_data[current_level_idx] = grid

            # --- GESTION SAISIE TEXTE ---
            elif event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_RETURN:
                    # Raccourci Validation
                    if input_text.strip() != "":
                        if input_action == "SAVE":
                            levels_data[current_level_idx] = grid
                            system_msg = save_project_named(levels_data, walls_data, input_text)
                        elif input_action == "EXPORT":
                            levels_data[current_level_idx] = grid
                            system_msg = export_universal_vtt_named(grid, walls_data.get(current_level_idx, []),
                                                                    assets_full, asset_sizes, current_level_idx,
                                                                    input_text)
                        system_msg_timer = current_time + 3000
                    input_active = False
                    input_text = ""
                    input_action = None

                elif event.key == pygame.K_ESCAPE:
                    input_active = False
                    input_text = ""
                    input_action = None

                elif event.key == pygame.K_BACKSPACE:
                    if cursor_pos > 0:
                        input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                        cursor_pos -= 1

                elif event.key == pygame.K_DELETE:
                    if cursor_pos < len(input_text):
                        input_text = input_text[:cursor_pos] + input_text[cursor_pos + 1:]

                elif event.key == pygame.K_LEFT:
                    if cursor_pos > 0: cursor_pos -= 1
                    cursor_visible = True

                elif event.key == pygame.K_RIGHT:
                    if cursor_pos < len(input_text): cursor_pos += 1
                    cursor_visible = True

                else:
                    if len(input_text) < 30 and event.unicode.isprintable():
                        input_text = input_text[:cursor_pos] + event.unicode + input_text[cursor_pos:]
                        cursor_pos += 1

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:

                    # --- SI MODAL ACTIF, ON INTERCEPTE LES CLICS ICI ---
                    if input_active:
                        # 1. Clic sur ANNULER
                        if btn_cancel_rect.collidepoint(mx, my):
                            input_active = False
                            input_text = ""
                            input_action = None

                        # 2. Clic sur ENREGISTRER
                        elif btn_ok_rect.collidepoint(mx, my):
                            if input_text.strip() != "":
                                if input_action == "SAVE":
                                    levels_data[current_level_idx] = grid
                                    system_msg = save_project_named(levels_data, walls_data, input_text)
                                elif input_action == "EXPORT":
                                    levels_data[current_level_idx] = grid
                                    system_msg = export_universal_vtt_named(grid, walls_data.get(current_level_idx, []),
                                                                            assets_full, asset_sizes, current_level_idx,
                                                                            input_text)
                                system_msg_timer = current_time + 3000
                            input_active = False
                            input_text = ""
                            input_action = None

                        # 3. Clic dans la zone de texte (Curseur)
                        elif input_box_rect.collidepoint(mx, my):
                            click_x = mx - (input_box_rect.x + 10)
                            for i in range(len(input_text) + 1):
                                w, _ = input_font.size(input_text[:i])
                                if w > click_x:
                                    cursor_pos = max(0, i - 1)
                                    break
                                cursor_pos = i
                            cursor_visible = True

                        # On bloque tout le reste
                        continue

                    if is_immersion_mode:
                        if btn_exit_immersion.collidepoint(mx, my): is_immersion_mode = False
                        continue

                    if is_file_menu_open:
                        menu_w, menu_h = 600, 500
                        menu_x, menu_y = (current_w - menu_w) // 2, (current_h - menu_h) // 2
                        btn_close_menu = pygame.Rect(menu_x + menu_w - 110, menu_y + menu_h - 60, 100, 50)
                        if btn_close_menu.collidepoint(mx, my): is_file_menu_open = False
                        start_y_files = menu_y + 60
                        for i, f_name in enumerate(file_list_cache):
                            f_rect = pygame.Rect(menu_x + 20, start_y_files + i * 50, menu_w - 40, 40)
                            if f_rect.collidepoint(mx, my):
                                loaded_lvls, loaded_walls, msg = load_project_file(f_name, current_w - UI_WIDTH,
                                                                                   current_h - MENU_HEIGHT)
                                system_msg = msg
                                system_msg_timer = current_time + 3000
                                if loaded_lvls:
                                    levels_data = loaded_lvls
                                    current_level_idx = 0
                                    walls_data = {}
                                    for k, v in loaded_walls.items(): walls_data[int(k)] = v
                                    if 0 not in levels_data: levels_data[0] = resize_grid(None, current_w - UI_WIDTH,
                                                                                          current_h - MENU_HEIGHT)
                                    if 0 not in walls_data: walls_data[0] = []
                                    grid = levels_data[current_level_idx]
                                    undo_stack.clear();
                                    redo_stack.clear()
                                is_file_menu_open = False
                        continue

                    if is_category_menu_open:
                        dropdown_h_list = len(options_to_show) * 40
                        dropdown_list_rect = pygame.Rect(ui_x + UI_MARGIN, btn_category_dropdown.bottom, work_width,
                                                         dropdown_h_list)
                        clicked_option = False
                        if dropdown_list_rect.collidepoint(mx, my):
                            for i, name in enumerate(options_to_show):
                                opt_rect = pygame.Rect(ui_x + UI_MARGIN, btn_category_dropdown.bottom + i * 40,
                                                       work_width, 40)
                                if opt_rect.collidepoint(mx, my):
                                    current_lib_name = name
                                    scroll_y = 0
                                    is_category_menu_open = False
                                    clicked_option = True
                                    break
                        elif btn_category_dropdown.collidepoint(mx, my):
                            is_category_menu_open = False
                            clicked_option = True
                        else:
                            is_category_menu_open = False
                        if clicked_option: continue

                    # MENU HAUT
                    if my < MENU_HEIGHT:
                        if btn_save.collidepoint(mx, my):
                            # ACTIVER INPUT MODE POUR SAUVER
                            input_active = True
                            input_action = "SAVE"
                            input_text = "projet"
                            cursor_pos = len(input_text)

                        elif btn_load.collidepoint(mx, my):
                            file_list_cache = list_json_files()
                            is_file_menu_open = True

                        elif btn_export.collidepoint(mx, my):
                            # ACTIVER INPUT MODE POUR EXPORT
                            input_active = True
                            input_action = "EXPORT"
                            input_text = "map_export"
                            cursor_pos = len(input_text)

                        elif btn_undo.collidepoint(mx, my):
                            grid, walls_data[current_level_idx] = perform_undo(grid,
                                                                               walls_data.get(current_level_idx, []))
                            levels_data[current_level_idx] = grid
                            system_msg = "Annulé";
                            system_msg_timer = current_time + 1000
                        elif btn_redo.collidepoint(mx, my):
                            grid, walls_data[current_level_idx] = perform_redo(grid,
                                                                               walls_data.get(current_level_idx, []))
                            levels_data[current_level_idx] = grid
                            system_msg = "Rétabli";
                            system_msg_timer = current_time + 1000
                        elif btn_immersion.collidepoint(mx, my):
                            is_immersion_mode = True
                        elif btn_quit.collidepoint(mx, my):
                            running = False

                    # MAP AREA
                    elif mx < map_view_width and not is_immersion_mode:

                        if current_tool_mode == TOOL_MODE_WALL:
                            grid_x = round((mx - ui_offset_x) / TILE_SIZE) * TILE_SIZE + ui_offset_x
                            grid_y = round((my - ui_offset_y) / TILE_SIZE) * TILE_SIZE + ui_offset_y
                            wall_start_point = (grid_x, grid_y)

                        elif current_tool_mode == TOOL_MODE_ERASE:
                            save_history(grid, walls_data.get(current_level_idx, []))
                            something_deleted = False
                            curr_walls = walls_data.get(current_level_idx, [])
                            for i in range(len(curr_walls) - 1, -1, -1):
                                w = curr_walls[i]
                                dist = distance_point_to_segment(mx, my - ui_offset_y, w['x1'], w['y1'], w['x2'],
                                                                 w['y2'])
                                if dist < 10:
                                    curr_walls.pop(i)
                                    something_deleted = True
                                    break
                            if not something_deleted:
                                hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=ui_offset_y,
                                                        target_layer=current_layer)
                                if hit:
                                    tx, ty, _, idx = hit
                                    if grid[ty][tx][idx].get('layer', 0) == current_layer:
                                        grid[ty][tx].pop(idx)

                        elif current_tool_mode == TOOL_MODE_PLACE:
                            hit = get_tile_at_pixel(grid, mx, my, assets_full, asset_sizes, offset_y_ui=ui_offset_y,
                                                    target_layer=current_layer)
                            if hit:
                                save_history(grid, walls_data.get(current_level_idx, []))
                                tx, ty, item, idx = hit
                                dragging_texture_key = item['key']
                                drag_angle = item['angle']
                                is_dragging = True
                                grid[ty][tx].pop(idx)
                            elif dragging_texture_key is not None:
                                is_dragging = True

                    # UI DROITE
                    elif mx > map_view_width and not is_immersion_mode:
                        if btn_lvl_up.collidepoint(mx, my):
                            new_level = current_level_idx + 1
                            levels_data[current_level_idx] = grid
                            current_level_idx = new_level
                            if current_level_idx not in levels_data: levels_data[current_level_idx] = resize_grid(None,
                                                                                                                  map_view_width,
                                                                                                                  map_view_height)
                            if current_level_idx not in walls_data: walls_data[current_level_idx] = []
                            grid = levels_data[current_level_idx]
                            undo_stack.clear();
                            redo_stack.clear()
                        elif btn_lvl_down.collidepoint(mx, my):
                            new_level = current_level_idx - 1
                            levels_data[current_level_idx] = grid
                            current_level_idx = new_level
                            if current_level_idx not in levels_data: levels_data[current_level_idx] = resize_grid(None,
                                                                                                                  map_view_width,
                                                                                                                  map_view_height)
                            if current_level_idx not in walls_data: walls_data[current_level_idx] = []
                            grid = levels_data[current_level_idx]
                            undo_stack.clear();
                            redo_stack.clear()

                        elif btn_layer_ground.collidepoint(mx, my):
                            current_layer = LAYER_GROUND
                        elif btn_layer_obj.collidepoint(mx, my):
                            current_layer = LAYER_OBJECTS
                        elif btn_layer_token.collidepoint(mx, my):
                            current_layer = LAYER_TOKENS

                        elif btn_mode_place.collidepoint(mx, my):
                            current_tool_mode = TOOL_MODE_PLACE
                        elif btn_mode_erase.collidepoint(mx, my):
                            current_tool_mode = TOOL_MODE_ERASE
                        elif btn_tool_rotate.collidepoint(mx, my):
                            if dragging_texture_key:
                                drag_angle = (drag_angle - 90) % 360
                                tool_angles[dragging_texture_key] = (tool_angles.get(dragging_texture_key,
                                                                                     0) - 90) % 360
                        elif btn_tool_wall.collidepoint(mx, my):
                            current_tool_mode = TOOL_MODE_WALL

                        elif btn_category_dropdown.collidepoint(mx, my):
                            is_category_menu_open = not is_category_menu_open

                        col, row = 0, 0
                        for tex_key in current_textures:
                            bx = ui_x + 10 + col * col_step + (col_step - 64) // 2
                            by = start_y_tex + row * 74 + scroll_y
                            if start_y_tex <= by < current_h:
                                icon_rect = pygame.Rect(bx, by, 64, 64)
                                if icon_rect.collidepoint(mx, my):
                                    dragging_texture_key = tex_key
                                    current_tool_mode = TOOL_MODE_PLACE
                                    drag_angle = tool_angles.get(tex_key, 0)
                                    is_dragging = True
                            col += 1
                            if col >= COLS_PER_ROW:
                                col = 0;
                                row += 1

                # SCROLL UP
                elif event.button == 4 and mx > map_view_width and not input_active:
                    scroll_y = min(0, scroll_y + 30)

                # SCROLL DOWN
                elif event.button == 5 and mx > map_view_width and not input_active:
                    scroll_y = max(-max_scroll_val, scroll_y - 30)

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    is_dragging = False

                    if input_active:
                        continue

                    if current_tool_mode == TOOL_MODE_WALL and wall_start_point:
                        if not is_immersion_mode and mx < map_view_width:
                            save_history(grid, walls_data.get(current_level_idx, []))
                            end_x = round((mx - ui_offset_x) / TILE_SIZE) * TILE_SIZE + ui_offset_x
                            end_y = round((my - ui_offset_y) / TILE_SIZE) * TILE_SIZE + ui_offset_y

                            if current_level_idx not in walls_data: walls_data[current_level_idx] = []
                            walls_data[current_level_idx].append({
                                'x1': wall_start_point[0], 'y1': wall_start_point[1] - ui_offset_y,
                                'x2': end_x, 'y2': end_y - ui_offset_y
                            })
                        wall_start_point = None

                    elif current_tool_mode == TOOL_MODE_PLACE and dragging_texture_key:
                        if not is_immersion_mode:
                            if mx < map_view_width and my > MENU_HEIGHT:
                                grid_my = my - MENU_HEIGHT
                                gx, gy = mx // TILE_SIZE, grid_my // TILE_SIZE
                                if 0 <= gx < grid_w and 0 <= gy < grid_h:
                                    save_history(grid, walls_data.get(current_level_idx, []))
                                    grid[gy][gx].append({
                                        'key': dragging_texture_key,
                                        'angle': drag_angle,
                                        'layer': current_layer
                                    })

        # --- DESSIN ---
        screen.fill(COLOR_BG)

        if is_immersion_mode:
            map_view_width = current_w
            map_view_height = current_h
            ui_offset_x = 0
            ui_offset_y = 0
        else:
            map_view_width = current_w - UI_WIDTH
            map_view_height = current_h - MENU_HEIGHT
            ui_offset_x = 0
            ui_offset_y = MENU_HEIGHT

        # 1. MAP
        for layer_pass in [LAYER_GROUND, LAYER_OBJECTS, LAYER_TOKENS]:
            for y in range(grid_h):
                for x in range(grid_w):
                    px, py = x * TILE_SIZE, y * TILE_SIZE + ui_offset_y
                    if px < map_view_width and py < current_h:
                        if layer_pass == LAYER_GROUND and not is_immersion_mode:
                            pygame.draw.rect(screen, COLOR_GRID, (px, py, TILE_SIZE, TILE_SIZE), 1)

                        if y < len(grid) and x < len(grid[0]):
                            for item in grid[y][x]:
                                if item.get('layer', 0) == layer_pass:
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

        # 2. MURS
        current_walls = walls_data.get(current_level_idx, [])
        for w in current_walls:
            wx1, wy1 = w['x1'], w['y1'] + ui_offset_y
            wx2, wy2 = w['x2'], w['y2'] + ui_offset_y
            pygame.draw.line(screen, COLOR_WALL_FIXED, (wx1, wy1), (wx2, wy2), 5)
            pygame.draw.circle(screen, COLOR_WALL_FIXED, (wx1, wy1), 5)
            pygame.draw.circle(screen, COLOR_WALL_FIXED, (wx2, wy2), 5)

        if current_tool_mode == TOOL_MODE_WALL and wall_start_point and not input_active:
            snap_x = round((mx - ui_offset_x) / TILE_SIZE) * TILE_SIZE + ui_offset_x
            snap_y = round((my - ui_offset_y) / TILE_SIZE) * TILE_SIZE + ui_offset_y
            pygame.draw.line(screen, COLOR_WALL_PREVIEW, wall_start_point, (snap_x, snap_y), 3)

        # BOUTON SORTIE IMMERSION
        if is_immersion_mode:
            hover_exit = btn_exit_immersion.collidepoint(mx, my) and not input_active
            draw_fantasy_button(screen, btn_exit_immersion, "X", font, COLOR_TEXT, COLOR_BTN_DANGER, COLOR_BORDER_GOLD,
                                hover_exit)

        if not is_immersion_mode:
            # UI BACKGROUND
            pygame.draw.rect(screen, COLOR_UI_BG, (map_view_width, MENU_HEIGHT, UI_WIDTH, current_h))
            pygame.draw.line(screen, COLOR_UI_BORDER, (map_view_width, MENU_HEIGHT), (map_view_width, current_h), 2)

            allow_hover = not input_active

            # --- DESSIN NIVEAUX ---
            hover_lvl_down = btn_lvl_down.collidepoint(mx, my) and allow_hover
            draw_fantasy_button(screen, btn_lvl_down, "ETAGE -", menu_font, COLOR_TEXT, COLOR_LEVEL_BTN,
                                COLOR_BORDER_GOLD, hover_lvl_down)

            draw_fantasy_button(screen, lvl_text_rect, f"Niv: {current_level_idx}", font, COLOR_TEXT, COLOR_PANEL_DARK,
                                COLOR_BORDER_GOLD, False)

            hover_lvl_up = btn_lvl_up.collidepoint(mx, my) and allow_hover
            draw_fantasy_button(screen, btn_lvl_up, "ETAGE +", menu_font, COLOR_TEXT, COLOR_LEVEL_BTN,
                                COLOR_BORDER_GOLD, hover_lvl_up)

            # COUCHES
            c_g = COLOR_BTN_LAYER_ACTIVE if current_layer == LAYER_GROUND else COLOR_BTN_NORMAL
            c_o = COLOR_BTN_LAYER_ACTIVE if current_layer == LAYER_OBJECTS else COLOR_BTN_NORMAL
            c_t = COLOR_BTN_LAYER_ACTIVE if current_layer == LAYER_TOKENS else COLOR_BTN_NORMAL

            b_g = COLOR_BORDER_ACTIVE if current_layer == LAYER_GROUND else COLOR_BORDER_GOLD
            b_o = COLOR_BORDER_ACTIVE if current_layer == LAYER_OBJECTS else COLOR_BORDER_GOLD
            b_t = COLOR_BORDER_ACTIVE if current_layer == LAYER_TOKENS else COLOR_BORDER_GOLD

            draw_fantasy_button(screen, btn_layer_ground, "SOL", font, COLOR_TEXT, c_g, b_g,
                                btn_layer_ground.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_layer_obj, "OBJETS", font, COLOR_TEXT, c_o, b_o,
                                btn_layer_obj.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_layer_token, "PIONS", font, COLOR_TEXT, c_t, b_t,
                                btn_layer_token.collidepoint(mx, my) and allow_hover)

            # TOOLS
            c_place = COLOR_BTN_ACTIVE if current_tool_mode == TOOL_MODE_PLACE else COLOR_BTN_NORMAL
            c_erase = COLOR_BTN_DANGER if current_tool_mode == TOOL_MODE_ERASE else COLOR_BTN_NORMAL
            c_wall = COLOR_BTN_ACTIVE if current_tool_mode == TOOL_MODE_WALL else COLOR_BTN_NORMAL

            b_place = COLOR_BORDER_ACTIVE if current_tool_mode == TOOL_MODE_PLACE else COLOR_BORDER_GOLD
            b_erase = COLOR_BORDER_ACTIVE if current_tool_mode == TOOL_MODE_ERASE else COLOR_BORDER_GOLD
            b_wall = COLOR_BORDER_ACTIVE if current_tool_mode == TOOL_MODE_WALL else COLOR_BORDER_GOLD

            draw_fantasy_button(screen, btn_mode_place, "POSER", font, COLOR_TEXT, c_place, b_place,
                                btn_mode_place.collidepoint(mx, my) and allow_hover)

            erase_txt = "GOMME (S)"
            if current_layer == LAYER_OBJECTS:
                erase_txt = "GOMME (O)"
            elif current_layer == LAYER_TOKENS:
                erase_txt = "GOMME (P)"
            draw_fantasy_button(screen, btn_mode_erase, erase_txt, font, COLOR_TEXT, c_erase, b_erase,
                                btn_mode_erase.collidepoint(mx, my) and allow_hover)

            draw_fantasy_button(screen, btn_tool_rotate, "PIVOTER", font, COLOR_TEXT, COLOR_BTN_NORMAL,
                                COLOR_BORDER_GOLD, btn_tool_rotate.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_tool_wall, "TRACER MUR", font, COLOR_TEXT, c_wall, b_wall,
                                btn_tool_wall.collidepoint(mx, my) and allow_hover)

            # DROPDOWN HEADER
            pygame.draw.rect(screen, COLOR_BTN_NORMAL, btn_category_dropdown, border_radius=5)
            text_cat = font.render(current_lib_name, True, COLOR_TEXT)
            screen.blit(text_cat, (btn_category_dropdown.x + 10, btn_category_dropdown.y + 10))

            # Triangle vectoriel
            center_x = btn_category_dropdown.right - 20
            center_y = btn_category_dropdown.centery
            if is_category_menu_open:
                points = [(center_x, center_y - 5), (center_x - 5, center_y + 5), (center_x + 5, center_y + 5)]
            else:
                points = [(center_x - 5, center_y - 5), (center_x + 5, center_y - 5), (center_x, center_y + 5)]
            pygame.draw.polygon(screen, COLOR_TEXT, points)

            # TEXTURES
            clip_rect = pygame.Rect(ui_x, start_y_tex, UI_WIDTH, current_h - start_y_tex)
            screen.set_clip(clip_rect)
            col, row = 0, 0
            for tex_key in current_textures:
                bx = ui_x + 10 + col * col_step + (col_step - 64) // 2
                by = start_y_tex + row * 74 + scroll_y
                if start_y_tex - 70 < by < current_h:
                    if tex_key == dragging_texture_key:
                        pygame.draw.rect(screen, COLOR_BTN_ACTIVE, (bx, by, 64, 64), 2, border_radius=3)
                    thumb = assets_thumb.get(tex_key)
                    if thumb:
                        rot = tool_angles.get(tex_key, 0)
                        if rot != 0:
                            img = pygame.transform.rotate(thumb, rot)
                            r = img.get_rect(center=(bx + 32, by + 32))
                            screen.blit(img, r)
                        else:
                            screen.blit(thumb, (bx, by))
                col += 1
                if col >= COLS_PER_ROW: col = 0; row += 1
            screen.set_clip(None)

            # --- SCROLLBAR VERTICALE ---
            if content_h_px > view_h_px:
                scrollbar_w = 10
                track_x = current_w - scrollbar_w - 5
                track_y = start_y_tex

                track_rect = pygame.Rect(track_x, track_y, scrollbar_w, view_h_px)
                pygame.draw.rect(screen, (30, 30, 35), track_rect, border_radius=5)

                ratio = view_h_px / content_h_px
                thumb_h = max(30, view_h_px * ratio)

                max_scroll_draw = content_h_px - view_h_px
                scroll_pct = abs(scroll_y) / max_scroll_draw if max_scroll_draw > 0 else 0

                track_scrollable_h = view_h_px - thumb_h
                thumb_y = track_y + (scroll_pct * track_scrollable_h)

                thumb_rect = pygame.Rect(track_x, thumb_y, scrollbar_w, thumb_h)
                pygame.draw.rect(screen, COLOR_BORDER_GOLD, thumb_rect, border_radius=5)

            # DROPDOWN LIST
            if is_category_menu_open:
                list_h = len(options_to_show) * 40
                bg_rect = pygame.Rect(ui_x + UI_MARGIN, btn_category_dropdown.bottom, work_width, list_h)
                pygame.draw.rect(screen, COLOR_DROPDOWN_BG, bg_rect)
                pygame.draw.rect(screen, COLOR_UI_BORDER, bg_rect, 1)
                for i, name in enumerate(options_to_show):
                    opt_rect = pygame.Rect(ui_x + UI_MARGIN, btn_category_dropdown.bottom + i * 40, work_width, 40)
                    if opt_rect.collidepoint(mx, my): pygame.draw.rect(screen, COLOR_BTN_ACTIVE, opt_rect)
                    name_surf = font.render(name, True, COLOR_TEXT)
                    screen.blit(name_surf, (opt_rect.x + 10, opt_rect.y + 10))

            # MENU HAUT (FANTASY BUTTONS)
            pygame.draw.rect(screen, COLOR_MENU_BAR, (0, 0, current_w, MENU_HEIGHT))

            draw_fantasy_button(screen, btn_save, "SAUVER", menu_font, COLOR_TEXT, COLOR_BTN_SUCCESS, COLOR_BORDER_GOLD,
                                btn_save.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_load, "CHARGER", menu_font, COLOR_TEXT, COLOR_BTN_NORMAL, COLOR_BORDER_GOLD,
                                btn_load.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_export, "EXPORT", menu_font, COLOR_TEXT, COLOR_BTN_NORMAL,
                                COLOR_BORDER_GOLD, btn_export.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_undo, "ANNULER", menu_font, COLOR_TEXT, COLOR_BTN_WARNING,
                                COLOR_BORDER_GOLD, btn_undo.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_redo, "RETABLIR", menu_font, COLOR_TEXT, COLOR_BTN_WARNING,
                                COLOR_BORDER_GOLD, btn_redo.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_immersion, "IMMERSION", menu_font, COLOR_TEXT, (50, 50, 150),
                                COLOR_BORDER_GOLD, btn_immersion.collidepoint(mx, my) and allow_hover)
            draw_fantasy_button(screen, btn_quit, "QUITTER", menu_font, COLOR_TEXT, COLOR_BTN_DANGER, COLOR_BORDER_GOLD,
                                btn_quit.collidepoint(mx, my) and allow_hover)

            if is_dragging and dragging_texture_key and not input_active:
                original_drag = assets_full.get(dragging_texture_key)
                if original_drag:
                    size = asset_sizes.get(dragging_texture_key, 1)
                    offset_drag = get_draw_offset(size)
                    if drag_angle != 0:
                        drag_img = pygame.transform.rotate(original_drag, drag_angle)
                    else:
                        drag_img = original_drag.copy()
                    alpha = 150
                    if current_layer == LAYER_OBJECTS: alpha = 200
                    if current_layer == LAYER_TOKENS: alpha = 255
                    drag_img.set_alpha(alpha)

                    if size % 2 == 0:
                        rect = drag_img.get_rect(center=(mx + offset_drag - 32, my + offset_drag - 32))
                    else:
                        rect = drag_img.get_rect(center=(mx, my))
                    screen.blit(drag_img, rect)

        if is_file_menu_open:
            overlay = pygame.Surface((current_w, current_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))
            menu_w, menu_h = 600, 500
            menu_x, menu_y = (current_w - menu_w) // 2, (current_h - menu_h) // 2
            pygame.draw.rect(screen, COLOR_UI_BG, (menu_x, menu_y, menu_w, menu_h), border_radius=10)
            pygame.draw.rect(screen, COLOR_UI_BORDER, (menu_x, menu_y, menu_w, menu_h), 2, border_radius=10)
            title_surf = title_font.render("CHOISIR UN FICHIER", True, COLOR_TEXT)
            screen.blit(title_surf, (menu_x + 20, menu_y + 20))
            btn_close_menu = pygame.Rect(menu_x + menu_w - 110, menu_y + menu_h - 60, 100, 50)
            draw_fantasy_button(screen, btn_close_menu, "Annuler", font, COLOR_TEXT, COLOR_BTN_DANGER,
                                COLOR_BORDER_GOLD, btn_close_menu.collidepoint(mx, my))
            start_y_files = menu_y + 60
            for i, f_name in enumerate(file_list_cache):
                f_rect = pygame.Rect(menu_x + 20, start_y_files + i * 50, menu_w - 40, 40)
                if f_rect.collidepoint(mx, my):
                    pygame.draw.rect(screen, COLOR_BTN_ACTIVE, f_rect, border_radius=5)
                else:
                    pygame.draw.rect(screen, COLOR_BTN_NORMAL, f_rect, border_radius=5)
                f_surf = font.render(f_name, True, COLOR_TEXT)
                screen.blit(f_surf, (f_rect.x + 10, f_rect.y + 10))

        # --- DESSIN DU MODAL INPUT (Si actif) ---
        if input_active:
            # Fond sombre semi-transparent (Overlay)
            overlay = pygame.Surface((current_w, current_h), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0, 0))

            # Boîte de dialogue
            modal_rect = pygame.Rect((current_w - 400) // 2, (current_h - 200) // 2, 400, 200)
            pygame.draw.rect(screen, COLOR_UI_BG, modal_rect, border_radius=10)
            pygame.draw.rect(screen, COLOR_BORDER_GOLD, modal_rect, 2, border_radius=10)

            # Titre
            prompt_text = "NOM DE LA SAUVEGARDE :" if input_action == "SAVE" else "NOM DU FICHIER EXPORT :"
            title_surf = title_font.render(prompt_text, True, COLOR_TEXT)
            screen.blit(title_surf, (modal_rect.centerx - title_surf.get_width() // 2, modal_rect.y + 40))

            # Zone saisie
            pygame.draw.rect(screen, (20, 20, 20), input_box_rect, border_radius=5)
            pygame.draw.rect(screen, COLOR_BORDER_ACTIVE, input_box_rect, 2, border_radius=5)

            # Texte
            txt_surf = input_font.render(input_text, True, (255, 255, 255))
            screen.blit(txt_surf, (input_box_rect.x + 10, input_box_rect.y + 8))

            # Curseur
            if cursor_visible:
                try:
                    c_x = input_font.size(input_text[:cursor_pos])[0]
                except:
                    c_x = 0
                pygame.draw.line(screen, COLOR_BORDER_GOLD, (input_box_rect.x + 10 + c_x, input_box_rect.y + 5),
                                 (input_box_rect.x + 10 + c_x, input_box_rect.y + 35), 2)

            # BOUTONS MODAL
            hover_cancel = btn_cancel_rect.collidepoint(mx, my)
            hover_ok = btn_ok_rect.collidepoint(mx, my)

            draw_fantasy_button(screen, btn_cancel_rect, "ANNULER", font, COLOR_TEXT, COLOR_BTN_DANGER,
                                COLOR_BORDER_GOLD, hover_cancel)
            draw_fantasy_button(screen, btn_ok_rect, "ENREGISTRER", font, COLOR_TEXT, COLOR_BTN_SUCCESS,
                                COLOR_BORDER_GOLD, hover_ok)

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