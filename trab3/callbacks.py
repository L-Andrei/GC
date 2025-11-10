# callbacks.py
# Contém toda a lógica de interação (eventos de mouse e teclado).

import glfw
import math
import state
import coords
from shapes import Triangle, Rectangle, Circle, Polygon
from utils import rotate_point, inverse_rotate_point

def finalize_drawing():
    if len(state.drawing_points) < 3:
        print('Polígono precisa de pelo menos 3 pontos.')
        state.drawing_points = []
        state.mode_mouse = None
        return

    pts = state.drawing_points[:]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    local_pts = [(p[0] - cx, p[1] - cy) for p in pts]

    s = Polygon(local_pts)
    s.x, s.y = (cx, cy)
    state.shapes.append(s)

    state.drawing_points = []
    state.mode_mouse = None


def mouse_over_handle(s, wx, wy, idx, size=0.035):
    try:
        # Tamanho do handle deve ser independente do zoom
        # Vamos calcular o tamanho em pixels e converter para mundo
        handle_size_world = size / state.global_zoom 
        
        hx, hy = s.get_handles_world()[idx]
        return abs(wx - hx) <= handle_size_world and abs(wy - hy) <= handle_size_world
    except IndexError:
        return False


def mouse_over_rotation_handle(s, wx, wy, radius=0.04):
    # Tamanho do handle independente do zoom
    radius_world = radius / state.global_zoom
    
    rx, ry = s.rotation_handle_world()
    return (wx - rx)**2 + (wy - ry)**2 <= radius_world**2


def mouse_button_callback(window, button, action, mods):
    x, y = glfw.get_cursor_pos(window)
    # Conversão de 2 passos
    vx, vy = coords.window_to_view(x, y)
    wx, wy = coords.view_to_world(vx, vy)

    # --- Lógica de Desenho (tem prioridade) ---
    if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
        if state.mode_mouse == 'drawing_circle_center':
            state.drawing_circle_pt_center = (wx, wy)
            state.mode_mouse = 'drawing_circle_radius'
            print('Modo: desenhar círculo — clique para definir o raio')
            return
        
        elif state.mode_mouse == 'drawing_circle_radius':
            cx, cy = state.drawing_circle_pt_center
            dx = wx - cx
            dy = wy - cy
            radius = math.sqrt(dx*dx + dy*dy)
            
            s = Circle(radius=max(radius, 0.01)) # Evita raio zero
            s.x, s.y = cx, cy
            state.shapes.append(s)
            state.selected = s
            print("Círculo criado.")
            
            # Reseta estado
            state.mode_mouse = None
            state.drawing_circle_pt_center = None
            return

    if state.mode_mouse == 'drawing_polygon':
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
            state.drawing_points.append((wx, wy))
            return
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_RIGHT:
            finalize_drawing()
            return
        return # Ignora seleção/etc enquanto desenha polígono
    
    # --- Lógica de Seleção / Interação ---
    if action == glfw.PRESS:
    
        # Lógica de Pan (Arrastar com Botão do Meio)
        if button == glfw.MOUSE_BUTTON_MIDDLE:
            state.dragging = True
            state.mode_mouse = 'pan'
            # Pan opera no espaço de VISUALIZAÇÃO
            state.prev_mouse = (vx, vy) 
            return # Ignora seleção/etc
            
        found = None
        found_handle = None
        found_rotation = False
        
        for s in reversed(state.shapes):
            if state.selected is not None and s == state.selected: 
                 handles = s.get_handles_world()
                 for i in range(len(handles)):
                    if mouse_over_handle(s, wx, wy, i):
                        found = s
                        found_handle = i
                        break
                 if found_handle is not None:
                     break
                 if mouse_over_rotation_handle(s, wx, wy):
                    found = s
                    found_rotation = True
                    break
            
            if found_handle is None and not found_rotation:
                if s.contains(wx, wy):
                    found = s
                    break

        if found is None and state.selected is not None:
             handles = state.selected.get_handles_world()
             for i in range(len(handles)):
                if mouse_over_handle(state.selected, wx, wy, i):
                    found = state.selected
                    found_handle = i
                    break
             if found_handle is None:
                if mouse_over_rotation_handle(state.selected, wx, wy):
                    found = state.selected
                    found_rotation = True
        
        elif found is not None and found != state.selected:
             handles = found.get_handles_world()
             for i in range(len(handles)):
                if mouse_over_handle(found, wx, wy, i):
                    found_handle = i
                    break
             if found_handle is None:
                if mouse_over_rotation_handle(found, wx, wy):
                    found_rotation = True
                    
        # Traz o objeto para a "frente"
        if found is not None:
            state.selected = found
            if state.selected in state.shapes:
                state.shapes.remove(state.selected)
                state.shapes.append(state.selected)
        else:
            state.selected = None # Clicar fora desseleciona

        state.prev_mouse = (wx, wy) # Padrão é coords de MUNDO
        state.dragging = True

        if found_handle is not None:
            # === BLOCO DE RESIZE ===
            state.resizing = True
            state.resizing_handle_idx = found_handle
            state.resizing_orig_scale = (state.selected.scale_x, state.selected.scale_y)
            
            opposite_idx = {
                0: 2, 1: 3, 2: 0, 3: 1,
                4: 6, 5: 7, 6: 4, 7: 5,
            }
            
            local_base_handles = state.selected.get_handles_local_base()
            state.resizing_orig_handle_base = local_base_handles[state.resizing_handle_idx]
            state.resizing_anchor = local_base_handles[opposite_idx[state.resizing_handle_idx]]
            
            ax_base, ay_base = state.resizing_anchor
            sax, say = ax_base * state.selected.scale_x, ay_base * state.selected.scale_y
            rsax, rsay = rotate_point(sax, say, state.selected.rotation)
            state.resizing_anchor_world = (rsax + state.selected.x, rsay + state.selected.y)
            
            state.mode_mouse = 'resize'
            # === FIM DO BLOCO DE RESIZE ===

        elif found_rotation:
            state.rotating = True
            state.rotation_orig = state.selected.rotation
            cx = state.selected.x
            cy = state.selected.y
            state.rotation_start_angle = math.atan2(wy - cy, wx - cx)
            state.mode_mouse = 'rotate'

        else:
            if state.selected is not None and state.selected.contains(wx, wy):
                state.mode_mouse = 'translate'
            else:
                state.mode_mouse = None
                state.selected = None # Garante deseleção se clicou no nada

    elif action == glfw.RELEASE:
        state.dragging = False
        
        # Só reseta o modo se estiver em um modo de interação (não desenho)
        if state.resizing:
            state.resizing = False
            state.resizing_handle_idx = None
            state.mode_mouse = None 
        elif state.rotating:
            state.rotating = False
            state.mode_mouse = None
        elif state.mode_mouse == 'translate':
            state.mode_mouse = None
        elif state.mode_mouse == 'pan': # Reseta o modo Pan
            state.mode_mouse = None
            

def cursor_pos_callback(window, xpos, ypos):
    # Conversão de 2 passos
    vx, vy = coords.window_to_view(xpos, ypos)
    wx, wy = coords.view_to_world(vx, vy)
    
    state.global_mouse_world = (wx, wy)

    if state.mode_mouse is None:
        state.prev_mouse = (wx, wy) # Padrão é MUNDO
        return

    # Lógica de Pan
    if state.mode_mouse == 'pan' and state.dragging:
        px, py = state.prev_mouse # Coords de VISUALIZAÇÃO
        dx = vx - px
        dy = vy - py
        
        pan_x, pan_y = state.global_pan
        state.global_pan = (pan_x + dx, pan_y + dy)
        state.prev_mouse = (vx, vy) # Atualiza pos de VISUALIZAÇÃO
        return

    if state.mode_mouse == 'translate' and state.dragging and state.selected is not None:
        px, py = state.prev_mouse # Coords de MUNDO
        dx = wx - px
        dy = wy - py
        state.selected.x += dx
        state.selected.y += dy
        state.prev_mouse = (wx, wy) # Atualiza pos de MUNDO

    elif state.mode_mouse == 'rotate' and state.rotating and state.selected is not None:
        cx = state.selected.x
        cy = state.selected.y
        ang_now = math.atan2(wy - cy, wx - cx)
        delta = ang_now - state.rotation_start_angle
        state.selected.rotation = (state.rotation_orig + math.degrees(delta)) % 360

    elif state.mode_mouse == 'resize' and state.resizing and state.selected is not None:
        # --- LÓGICA DE RESIZE CORRIGIDA ---
        awx, awy = state.resizing_anchor_world
        ax_base, ay_base = state.resizing_anchor
        hb_base_x, hb_base_y = state.resizing_orig_handle_base
        
        v_wx, v_wy = wx - awx, wy - awy
        v_rx, v_ry = inverse_rotate_point(v_wx, v_wy, state.selected.rotation)
        
        v_base_x = hb_base_x - ax_base
        v_base_y = hb_base_y - ay_base
        
        new_sx = state.selected.scale_x
        new_sy = state.selected.scale_y
        
        eps = 1e-7
        if abs(v_base_x) > eps:
            new_sx = v_rx / v_base_x
        
        if abs(v_base_y) > eps:
            new_sy = v_ry / v_base_y

        new_sx = max(new_sx, 0.02)
        new_sy = max(new_sy, 0.02)

        handle_type = state.resizing_handle_idx
        if handle_type in (4, 6): # top-center, bottom-center
             new_sx = state.selected.scale_x
        elif handle_type in (5, 7): # left-center, right-center
             new_sy = state.selected.scale_y

        state.selected.scale_x = new_sx
        state.selected.scale_y = new_sy
        
        ax, ay = state.resizing_anchor
        sax = ax * new_sx
        say = ay * new_sy
        rsax, rsay = rotate_point(sax, say, state.selected.rotation)
        
        state.selected.x = awx - rsax
        state.selected.y = awy - rsay
        # --- FIM DA LÓGICA DE RESIZE ---

    if state.mode_mouse not in ('rotate', 'resize', 'pan'):
        state.prev_mouse = (wx, wy)


def key_callback(window, key, scancode, action, mods):
    x, y = glfw.get_cursor_pos(window)
    # Conversão de 2 passos
    vx, vy = coords.window_to_view(x, y)
    wx, wy = coords.view_to_world(vx, vy)

    if action != glfw.PRESS:
        return

    # --- Primeiro, checa se está em modo de desenho ---
    if state.mode_mouse in ('drawing_polygon', 'drawing_circle_center', 'drawing_circle_radius'):
        if key == glfw.KEY_ESCAPE:
            state.drawing_points = []
            state.drawing_circle_pt_center = None
            state.mode_mouse = None
            print("Modo de desenho cancelado.")
        
        return # Ignora TODAS as outras teclas enquanto desenha

    # --- Se não está em modo de desenho, processa teclas normais ---
    
    if key == glfw.KEY_ESCAPE:
        state.selected = None
        print("Seleção limpa.")
        return

    if key == glfw.KEY_1:
        s = Triangle()
        s.x, s.y = wx, wy
        state.shapes.append(s)
    elif key == glfw.KEY_2:
        s = Rectangle()
        s.x, s.y = wx, wy
        state.shapes.append(s)
    elif key == glfw.KEY_3:
        state.mode_mouse = 'drawing_circle_center'
        state.drawing_circle_pt_center = None
        print('Modo: desenhar círculo — clique para definir o centro')
    elif key == glfw.KEY_4:
        state.drawing_points = []
        state.mode_mouse = 'drawing_polygon'
        print('Modo: desenhar polígono — clique para adicionar vértices, botão direito para finalizar')
    elif key in (glfw.KEY_DELETE, glfw.KEY_BACKSPACE):
        if state.selected and state.selected in state.shapes:
            state.shapes.remove(state.selected)
            state.selected = None
    elif key == glfw.KEY_C:
        state.shapes = []
        state.selected = None
        state.drawing_points = []
        state.drawing_circle_pt_center = None
        state.mode_mouse = None
        print("Canvas limpo.")


def scroll_callback(window, xoffset, yoffset):
    # 1. Obtém a posição do mouse na visualização (-1 a 1)
    x, y = glfw.get_cursor_pos(window)
    vx, vy = coords.window_to_view(x, y)
    
    # 2. Obtém a coordenada de MUNDO sob o mouse ANTES do zoom
    world_x_before, world_y_before = coords.view_to_world(vx, vy)
    
    # 3. Calcula o novo zoom
    zoom_factor = 1.1
    old_zoom = state.global_zoom
    
    if yoffset > 0:
        state.global_zoom *= zoom_factor
    elif yoffset < 0:
        state.global_zoom /= zoom_factor
        
    # Limita o zoom
    state.global_zoom = max(0.1, min(state.global_zoom, 10.0))
    
    if state.global_zoom == old_zoom:
        return # Não houve mudança (atingiu o limite)
        
    # 4. Ajusta o pan para que o ponto do mundo sob o cursor permaneça o mesmo
    # new_pan = view_mouse - (world_mouse * new_zoom)
    
    new_pan_x = vx - (world_x_before * state.global_zoom)
    new_pan_y = vy - (world_y_before * state.global_zoom)

    state.global_pan = (new_pan_x, new_pan_y)

    # Atualiza a posição global do mouse no mundo (importante!)
    cursor_pos_callback(window, x, y)