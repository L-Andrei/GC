import sys
import math
import glfw
from OpenGL.GL import *
import numpy as np

# ---------- utilitários ----------

def point_in_polygon(x, y, vertices):
    # Ray casting (funciona para polígonos simples)
    inside = False
    n = len(vertices)
    for i in range(n):
        x0, y0 = vertices[i]
        x1, y1 = vertices[(i + 1) % n]
        if ((y0 > y) != (y1 > y)):
            xinters = (x1 - x0) * (y - y0) / (y1 - y0 + 1e-12) + x0
            if x < xinters:
                inside = not inside
    return inside


def rotate_point(px, py, angle_deg):
    a = math.radians(angle_deg)
    ca = math.cos(a)
    sa = math.sin(a)
    return px * ca - py * sa, px * sa + py * ca


def inverse_rotate_point(px, py, angle_deg):
    return rotate_point(px, py, -angle_deg)


def convex_hull(points):
    pts = sorted(points)
    if len(pts) <= 1:
        return pts
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


# ---------- formas ----------
class Shape:
    def __init__(self, vertices):
        self.base_vertices = vertices[:]  # não modificar diretamente
        self.x = 0.0
        self.y = 0.0
        self.rotation = 0.0  # graus
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.color = (0.0, 0.0, 0.0)

    def transformed_vertices(self):
        out = []
        for bx, by in self.base_vertices:
            sx = bx * self.scale_x
            sy = by * self.scale_y
            rx, ry = rotate_point(sx, sy, self.rotation)
            out.append((rx + self.x, ry + self.y))
        return out

    def contains(self, px, py):
        verts = self.transformed_vertices()
        return point_in_polygon(px, py, verts)

    def draw(self):
        verts = self.transformed_vertices()
        glColor3f(*self.color)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        for vx, vy in verts:
            glVertex2f(vx, vy)
        glEnd()

    def local_bounds(self):
        xs = [p[0] for p in self.base_vertices]
        ys = [p[1] for p in self.base_vertices]
        return min(xs), max(xs), min(ys), max(ys)

    def bounding_box_world(self):
        verts = self.transformed_vertices()
        xs = [v[0] for v in verts]
        ys = [v[1] for v in verts]
        return min(xs), max(xs), min(ys), max(ys)

    def get_handles_world(self):
        minx, maxx, miny, maxy = self.bounding_box_world()
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        return [
            (minx, miny),  # bottom-left
            (maxx, miny),  # bottom-right
            (maxx, maxy),  # top-right
            (minx, maxy),  # top-left
            (cx, miny),    # bottom-center
            (maxx, cy),    # right-center
            (cx, maxy),    # top-center
            (minx, cy),    # left-center
        ]

    def rotation_handle_world(self):
        minx, maxx, miny, maxy = self.bounding_box_world()
        cx = (minx + maxx) / 2
        top = maxy
        offset = 0.06
        return (cx, top + offset)

    def world_to_base_with_scale(self, wx, wy, scale_x=None, scale_y=None):
        lx = wx - self.x
        ly = wy - self.y
        rx, ry = inverse_rotate_point(lx, ly, self.rotation)
        sx = scale_x if scale_x is not None else self.scale_x
        sy = scale_y if scale_y is not None else self.scale_y
        bx = rx / (sx + 1e-12)
        by = ry / (sy + 1e-12)
        return bx, by


class Triangle(Shape):
    def __init__(self, size=0.2):
        h = size * math.sqrt(3) / 2
        verts = [(-size/2, -h/3), (size/2, -h/3), (0.0, 2*h/3)]
        super().__init__(verts)


class Rectangle(Shape):
    def __init__(self, w=0.3, h=0.2):
        hw = w / 2
        hh = h / 2
        verts = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        super().__init__(verts)


class Circle(Shape):
    def __init__(self, radius=0.15, segments=48):
        verts = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            verts.append((math.cos(a) * radius, math.sin(a) * radius))
        super().__init__(verts)

class Polygon(Shape):
    def __init__(self, pts):
        super().__init__(pts)


# ---------- estado ----------
WINDOW_W = 900
WINDOW_H = 700
shapes = []
selected = None

mode_mouse = None  # 'translate','rotate','resize','drawing_polygon'
prev_mouse = (0.0, 0.0)

dragging = False

# resize state
resizing = False
resizing_handle_idx = None
resizing_orig_scale = (1.0, 1.0)
resizing_orig_bbox = None
resizing_anchor = None
resizing_orig_handle_base = None

# rotate state
rotating = False
rotation_start_angle = 0.0
rotation_orig = 0.0

# drawing polygon
drawing_points = []


def window_to_world(mx, my):
    nx = (mx / WINDOW_W) * 2 - 1
    ny = -((my / WINDOW_H) * 2 - 1)
    return nx, ny


def mouse_over_handle(s, wx, wy, idx, size=0.035):
    hx, hy = s.get_handles_world()[idx]
    return abs(wx - hx) <= size and abs(wy - hy) <= size


def mouse_over_rotation_handle(s, wx, wy, radius=0.04):
    rx, ry = s.rotation_handle_world()
    return (wx - rx)**2 + (wy - ry)**2 <= radius**2


# ---------- callbacks ----------

def mouse_button_callback(window, button, action, mods):
    global dragging, selected, mode_mouse, prev_mouse
    global resizing, resizing_handle_idx, resizing_orig_scale, resizing_orig_bbox, resizing_anchor, resizing_orig_handle_base
    global rotating, rotation_start_angle, rotation_orig
    global drawing_points

    x, y = glfw.get_cursor_pos(window)
    wx, wy = window_to_world(x, y)

    if mode_mouse == 'drawing_polygon':
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
            drawing_points.append((wx, wy))
            return
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_RIGHT:
            finalize_drawing()
            return
        return

    if action == glfw.PRESS:
        found = None
        found_handle = None
        found_rotation = False
        for s in reversed(shapes):
            handles = s.get_handles_world()
            for i in range(len(handles)):
                if mouse_over_handle(s, wx, wy, i, size=0.035):
                    found = s
                    found_handle = i
                    break
            if found_handle is not None:
                break
            if mouse_over_rotation_handle(s, wx, wy, radius=0.04):
                found = s
                found_rotation = True
                break
            if s.contains(wx, wy):
                found = s
                break

        selected = found
        prev_mouse = (wx, wy)
        dragging = True

        if found_handle is not None:
            # === NOVO BLOCO CORRIGIDO ===
            resizing = True
            resizing_handle_idx = found_handle
            resizing_orig_scale = (selected.scale_x, selected.scale_y)
            resizing_orig_bbox = selected.local_bounds()

            orig_sx, orig_sy = resizing_orig_scale
            opposite_idx = {
                0: 2, 1: 3, 2: 0, 3: 1,
                4: 6, 5: 7, 6: 4, 7: 5,
            }

            handles_world = selected.get_handles_world()
            handle_world = handles_world[resizing_handle_idx]
            anchor_world = handles_world[opposite_idx[resizing_handle_idx]]

            hb_x, hb_y = selected.world_to_base_with_scale(handle_world[0], handle_world[1],
                                                           scale_x=orig_sx, scale_y=orig_sy)
            ax, ay = selected.world_to_base_with_scale(anchor_world[0], anchor_world[1],
                                                       scale_x=orig_sx, scale_y=orig_sy)

            resizing_anchor = (ax, ay)
            resizing_orig_handle_base = (hb_x, hb_y)
            mode_mouse = 'resize'
            # === FIM DO BLOCO CORRIGIDO ===

        elif found_rotation:
            rotating = True
            rotation_orig = selected.rotation
            cx = selected.x
            cy = selected.y
            rotation_start_angle = math.atan2(wy - cy, wx - cx)
            mode_mouse = 'rotate'

        else:
            if selected is not None and selected.contains(wx, wy):
                mode_mouse = 'translate'
            else:
                mode_mouse = None

    elif action == glfw.RELEASE:
        dragging = False
        if resizing:
            resizing = False
            resizing_handle_idx = None
        if rotating:
            rotating = False
        mode_mouse = None


def cursor_pos_callback(window, xpos, ypos):
    global prev_mouse
    global resizing, resizing_handle_idx, resizing_orig_scale, resizing_anchor, resizing_orig_handle_base
    global rotating, rotation_start_angle, rotation_orig

    wx, wy = window_to_world(xpos, ypos)

    if mode_mouse is None:
        return

    if mode_mouse == 'translate' and dragging and selected is not None:
        px, py = prev_mouse
        dx = wx - px
        dy = wy - py
        selected.x += dx
        selected.y += dy
        prev_mouse = (wx, wy)

    elif mode_mouse == 'rotate' and rotating and selected is not None:
        cx = selected.x
        cy = selected.y
        ang_now = math.atan2(wy - cy, wx - cx)
        delta = ang_now - rotation_start_angle
        selected.rotation = (rotation_orig + math.degrees(delta)) % 360

    elif mode_mouse == 'resize' and resizing and selected is not None:
        orig_sx, orig_sy = resizing_orig_scale
        bx, by = selected.world_to_base_with_scale(wx, wy, scale_x=orig_sx, scale_y=orig_sy)
        ax, ay = resizing_anchor
        hb_x, hb_y = resizing_orig_handle_base
        eps = 1e-6
        new_sx = orig_sx
        new_sy = orig_sy
        denom_x = (hb_x - ax)
        denom_y = (hb_y - ay)
        if abs(denom_x) > eps:
            new_sx = orig_sx * ((bx - ax) / denom_x)
        if abs(denom_y) > eps:
            new_sy = orig_sy * ((by - ay) / denom_y)
        new_sx = max(new_sx, 0.02)
        new_sy = max(new_sy, 0.02)
        selected.scale_x = new_sx
        selected.scale_y = new_sy

    prev_mouse = (wx, wy)


def key_callback(window, key, scancode, action, mods):
    global shapes, selected, mode_mouse, drawing_points
    if action != glfw.PRESS:
        return

    if key == glfw.KEY_1:
        s = Triangle()
        shapes.append(s)
    elif key == glfw.KEY_2:
        s = Rectangle()
        shapes.append(s)
    elif key == glfw.KEY_3:
        s = Circle()
        shapes.append(s)
    elif key == glfw.KEY_4:
        drawing_points = []
        mode_mouse = 'drawing_polygon'
        print('Modo: desenhar polígono — clique para adicionar vértices, botão direito para finalizar')
    elif key in (glfw.KEY_DELETE, glfw.KEY_BACKSPACE):
        if selected and selected in shapes:
            shapes.remove(selected)
            selected = None
    elif key == glfw.KEY_C:
        shapes = []
        selected = None


def finalize_drawing():
    global drawing_points, mode_mouse, shapes
    if len(drawing_points) < 3:
        print('Polígono precisa de pelo menos 3 pontos.')
        drawing_points = []
        mode_mouse = None
        return

    pts = drawing_points[:]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    local_pts = [(p[0] - cx, p[1] - cy) for p in pts]

    s = Polygon(local_pts)
    s.x, s.y = (cx, cy)
    shapes.append(s)

    drawing_points = []
    mode_mouse = None


# ---------- render ----------

def init_glfw():
    if not glfw.init():
        print('Erro ao iniciar GLFW')
        sys.exit(1)
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    window = glfw.create_window(WINDOW_W, WINDOW_H, 'Canvas OpenGL - shapes', None, None)
    if not window:
        glfw.terminate()
        print('Erro ao criar janela')
        sys.exit(1)
    glfw.make_context_current(window)
    glfw.set_mouse_button_callback(window, mouse_button_callback)
    glfw.set_cursor_pos_callback(window, cursor_pos_callback)
    glfw.set_key_callback(window, key_callback)
    return window


def draw_handle_square(cx, cy, size=0.03):
    half = size / 2
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
    glColor3f(0.95, 0.6, 0.2)
    glBegin(GL_TRIANGLE_FAN)
    glVertex2f(cx, cy)
    for i in range(segments + 1):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
    glEnd()
    glColor3f(0.05, 0.05, 0.05)
    glBegin(GL_LINE_LOOP)
    for i in range(segments):
        a = 2 * math.pi * i / segments
        glVertex2f(cx + math.cos(a) * r, cy + math.sin(a) * r)
    glEnd()


def draw_grid():
    glColor3f(0.85, 0.85, 0.85)
    glLineWidth(1.0)
    glBegin(GL_LINES)
    step = 0.1
    for i in np.arange(-1.0, 1.001, step):
        glVertex2f(i, -1)
        glVertex2f(i, 1)
        glVertex2f(-1, i)
        glVertex2f(1, i)
    glEnd()


def render(window):
    glViewport(0, 0, WINDOW_W, WINDOW_H)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(-1, 1, -1, 1, -1, 1)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    draw_grid()

    for s in shapes:
        s.draw()

    if selected is not None:
        glPushAttrib(GL_CURRENT_BIT | GL_LINE_BIT)
        glLineWidth(2.0)
        glColor3f(1.0, 0.0, 0.0)
        verts = selected.transformed_vertices()
        glBegin(GL_LINE_LOOP)
        for vx, vy in verts:
            glVertex2f(vx, vy)
        glEnd()
        glPopAttrib()

        handles = selected.get_handles_world()
        for hx, hy in handles:
            draw_handle_square(hx, hy, size=0.035)
        rx, ry = selected.rotation_handle_world()
        draw_handle_circle(rx, ry, r=0.04)

    if mode_mouse == 'drawing_polygon' and len(drawing_points) > 0:
        glColor3f(0.2, 0.6, 0.9)
        glBegin(GL_LINE_STRIP)
        for px, py in drawing_points:
            glVertex2f(px, py)
        glEnd()

    glfw.swap_buffers(window)


def main():
    window = init_glfw()
    while not glfw.window_should_close(window):
        render(window)
        glfw.poll_events()
    glfw.terminate()


if __name__ == '__main__':
    main()
