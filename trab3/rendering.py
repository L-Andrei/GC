# rendering.py
# Contém toda a lógica de desenho (OpenGL).

import glfw
from OpenGL.GL import *
import numpy as np
import math
import state

def draw_handle_square(cx, cy, size=0.03):
    # Tamanho do handle (em 'view space') para ser independente do zoom
    half = (size / 2) / state.global_zoom 
    
    glColor3f(0.95, 0.95, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(cx - half, cy - half)
    glVertex2f(cx + half, cy - half)
    glVertex2f(cx + half, cy + half)
    glVertex2f(cx - half, cy + half)
    glEnd()
    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_LINE_LOOP)
    glVertex2f(cx - half, cy - half)
    glVertex2f(cx + half, cy - half)
    glVertex2f(cx + half, cy + half)
    glVertex2f(cx - half, cy + half)
    glEnd()


def draw_handle_circle(cx, cy, r=0.03, segments=18):
    # Tamanho do handle (em 'view space') para ser independente do zoom
    radius = r / state.global_zoom
    
    glColor3f(0.95, 0.6, 0.2)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * radius, cy + math.sin(a) * radius)
    glEnd()
    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * radius, cy + math.sin(a) * radius)
    glEnd()


def draw_grid():
    glColor3f(0.85, 0.85, 0.85)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    
    # Desenha um grid maior para acomodar o zoom out
    step = 0.1
    world_range = 5.0 
    for i in np.arange(-world_range, world_range + 1e-9, step):
        glVertex2f(i, -world_range)
        glVertex2f(i, world_range)
        glVertex2f(-world_range, i)
        glVertex2f(world_range, i)
    glEnd()


def render(window):
    glViewport(0, 0, state.WINDOW_W, state.WINDOW_H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity() # Reseta a matriz de Modelo/Visão

    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    # === APLICA A TRANSFORMAÇÃO DA CÂMERA ===
    glPushMatrix()
    
    # 1. Aplica o Pan (Translação da Visão)
    glTranslatef(state.global_pan[0], state.global_pan[1], 0.0)
    
    # 2. Aplica o Zoom (Escala da Visão)
    glScalef(state.global_zoom, state.global_zoom, 1.0)
    
    # ========================================

    draw_grid() # O grid agora será afetado pelo zoom/pan

    for s in state.shapes:
        s.draw()

    if state.selected is not None:
        glPushAttrib(GL_CURRENT_BIT | GL_LINE_BIT)
        glLineWidth(2.0)
        glColor3f(1.0, 0.0, 0.0)
        verts = state.selected.transformed_vertices()
        glBegin(GL_LINE_LOOP)
        for vx, vy in verts:
            glVertex2f(vx, vy)
        glEnd()
        glPopAttrib()

        handles = state.selected.get_handles_world()
        for hx, hy in handles:
            draw_handle_square(hx, hy, size=0.035)
        rx, ry = state.selected.rotation_handle_world()
        draw_handle_circle(rx, ry, r=0.04)

    # Preview do polígono
    if state.mode_mouse == 'drawing_polygon' and len(state.drawing_points) > 0:
        glColor3f(0.2, 0.6, 0.9)
        glBegin(GL_LINE_STRIP)
        for px, py in state.drawing_points:
            glVertex2f(px, py)
        # Linha até o mouse
        glVertex2f(state.global_mouse_world[0], state.global_mouse_world[1])
        glEnd()
    
    # Preview do círculo
    if state.mode_mouse == 'drawing_circle_radius' and state.drawing_circle_pt_center is not None:
        cx, cy = state.drawing_circle_pt_center
        mx, my = state.global_mouse_world
        dx = mx - cx
        dy = my - cy
        radius = math.sqrt(dx*dx + dy*dy)
        
        if radius > 0.001:
            glColor3f(0.2, 0.6, 0.9) 
            glLineWidth(1.5)
            glBegin(GL_LINE_LOOP)
            segments = 48
            for i in range(segments + 1):
                a = 2 * math.pi * i / segments
                glVertex2f(cx + math.cos(a) * radius, cy + math.sin(a) * radius)
            glEnd()

    glPopMatrix() # <-- Libera a matriz da câmera

    glfw.swap_buffers(window)