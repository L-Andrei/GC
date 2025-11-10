# coords.py
# Gerencia as conversões de coordenadas.

import state

def window_to_view(mx, my):
    """Converte coordenadas de janela (pixel) para visualização (-1 a 1)"""
    nx = (mx / state.WINDOW_W) * 2 - 1
    ny = -((my / state.WINDOW_H) * 2 - 1)
    return nx, ny

def view_to_world(vx, vy):
    """Converte coordenadas de visualização (-1 a 1) para mundo (com zoom/pan)"""
    pan_x, pan_y = state.global_pan
    # Inverte a transformação da renderização
    world_x = (vx - pan_x) / state.global_zoom
    world_y = (vy - pan_y) / state.global_zoom
    return world_x, world_y

def world_to_view(wx, wy):
    """Converte coordenadas de mundo para visualização (para desenhar)"""
    pan_x, pan_y = state.global_pan
    # Aplica a transformação da renderização
    view_x = wx * state.global_zoom + pan_x
    view_y = wy * state.global_zoom + pan_y
    return view_x, view_y