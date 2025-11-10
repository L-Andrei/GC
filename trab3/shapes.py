# shapes.py
# Define a classe base Shape e todas as formas concretas.

import math
from OpenGL.GL import *
from utils import rotate_point, inverse_rotate_point, point_in_polygon

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

    def get_handles_local_base(self):
        """
        Retorna os 8 handles no espaço base (antes de scale/rotate/translate)
        """
        minx, maxx, miny, maxy = self.local_bounds()
        cx = (minx + maxx) / 2
        cy = (miny + maxy) / 2
        return [
            (minx, miny),  # bottom-left (0)
            (maxx, miny),  # bottom-right (1)
            (maxx, maxy),  # top-right (2)
            (minx, maxy),  # top-left (3)
            (cx, miny),    # bottom-center (4)
            (maxx, cy),    # right-center (5)
            (cx, maxy),    # top-center (6)
            (minx, cy),    # left-center (7)
        ]

    def get_handles_world(self):
        """
        Transforma os handles 'base' para o espaço do mundo
        """
        handles_world = []
        base_handles = self.get_handles_local_base()
        
        for bx, by in base_handles:
            # 1. Aplicar escala
            sx = bx * self.scale_x
            sy = by * self.scale_y
            # 2. Aplicar rotação
            rx, ry = rotate_point(sx, sy, self.rotation)
            # 3. Aplicar translação (posição do objeto)
            handles_world.append((rx + self.x, ry + self.y))
            
        return handles_world

    def rotation_handle_world(self):
        minx, maxx, miny, maxy = self.bounding_box_world()
        cx = (minx + maxx) / 2
        top = maxy
        offset = 0.06
        
        try:
            hx, hy = self.get_handles_world()[6] # Pega a alça 'top-center' (índice 6)
            cx, cy = self.x, self.y # Posição do centro do objeto
            vx, vy = hx - cx, hy - cy # Vetor do centro para a alça
            v_len = math.sqrt(vx*vx + vy*vy)
            
            # Normaliza e estende o vetor
            if v_len > 1e-6:
                nx, ny = vx / v_len, vy / v_len
                return (hx + nx * offset, hy + ny * offset)
            else:
                return (cx, top + offset) # Fallback
        except IndexError:
             minx, maxx, miny, maxy = self.bounding_box_world()
             cx = (minx + maxx) / 2
             return (cx, maxy + offset)


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