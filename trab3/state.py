# state.py
# Armazena todo o estado global da aplicação.
# Outros módulos irão importar este e acessar/modificar
# as variáveis como 'state.shapes', 'state.global_zoom', etc.

# ---------- estado ----------
WINDOW_W = 900
WINDOW_H = 700
shapes = []
selected = None

mode_mouse = None  # 'translate','rotate','resize','drawing_polygon', 'drawing_circle_center', 'drawing_circle_radius', 'pan'
prev_mouse = (0.0, 0.0)
global_mouse_world = (0.0, 0.0)

dragging = False

# Estado da Câmera (View)
global_zoom = 1.0
global_pan = (0.0, 0.0)

# resize state
resizing = False
resizing_handle_idx = None
resizing_orig_scale = (1.0, 1.0)
resizing_anchor = None # Coordenadas BASE da ancora
resizing_orig_handle_base = None # Coordenadas BASE do handle
resizing_anchor_world = None # Coordenadas MUNDO da ancora

# rotate state
rotating = False
rotation_start_angle = 0.0
rotation_orig = 0.0

# drawing polygon
drawing_points = []

# drawing circle
drawing_circle_pt_center = None