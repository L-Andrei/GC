# utils.py
# Funções utilitárias de geometria e matemática.

import math

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