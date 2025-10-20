from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *

class Window:
    def __init__(self, width=640, height=480, title=b"GLUT Window"):
        self.left = -30
        self.right = 130
        self.bottom = -60
        self.top = 170
        self.w = width
        self.h = height
        self.title = title

    def create(self):
        glutInit()
        glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB)
        glutInitWindowSize(self.w, self.h)
        glutInitWindowPosition(100, 100)
        glutCreateWindow(self.title)

    def configure_visualization(self):
        glViewport(0, 0, self.w, self.h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.left, self.right, self.bottom, self.top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glClearColor(0.3, 0.3, 0.3, 1.0)  # fundo cinza

class Slider:
    def __init__(self, x, y, width, height, color):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.value = 0.5  # inicia no meio

    def draw(self):
        # gradiente
        glBegin(GL_QUADS)
        glColor3f(0, 0, 0)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x, self.y + self.height)
        glColor3f(*self.color)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x + self.width, self.y)
        glEnd()

        # contorno branco
        glColor3f(1, 1, 1)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()

        # indicador da posição
        px = self.x + self.value * self.width
        glColor3f(1, 1, 1)
        glBegin(GL_LINES)
        glVertex2f(px, self.y)
        glVertex2f(px, self.y + self.height)
        glEnd()

    def inside(self, mx, my):
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height

    def update_value(self, mx):
        self.value = max(0.0, min(1.0, (mx - self.x) / self.width))

class Button:
    """Botão simples retangular"""
    def __init__(self, x, y, width, height, label="Reset"):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label

    def draw(self):
        # fundo azul escuro
        glColor3f(0.1, 0.1, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()

        # contorno branco
        glColor3f(1, 1, 1)
        glLineWidth(1.5)
        glBegin(GL_LINE_LOOP)
        glVertex2f(self.x, self.y)
        glVertex2f(self.x + self.width, self.y)
        glVertex2f(self.x + self.width, self.y + self.height)
        glVertex2f(self.x, self.y + self.height)
        glEnd()

        # desenhar label (simples, usando bitmap)
        glColor3f(1, 1, 1)
        glRasterPos2f(self.x + 10, self.y + self.height / 2 - 4)
        for c in self.label:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(c))

    def inside(self, mx, my):
        return self.x <= mx <= self.x + self.width and self.y <= my <= self.y + self.height


# VARIÁVEIS GLOBAIS
sliders = []
current_slider = None
reset_button = None

def display():
    glClear(GL_COLOR_BUFFER_BIT)

    # desenha botão
    reset_button.draw()

    # desenha sliders
    for s in sliders:
        s.draw()

    # cor resultante
    r = sliders[0].value
    g = sliders[1].value
    b = sliders[2].value

    glColor3f(r, g, b)
    glBegin(GL_QUADS)
    glVertex2f(0, -40)
    glVertex2f(40, -40)
    glVertex2f(40, -10)
    glVertex2f(0, -10)
    glEnd()

    # contorno branco
    glColor3f(1, 1, 1)
    glBegin(GL_LINE_LOOP)
    glVertex2f(0, -40)
    glVertex2f(40, -40)
    glVertex2f(40, -10)
    glVertex2f(0, -10)
    glEnd()

    glutSwapBuffers()

def mouse(button, state, x, y):
    global current_slider
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        mx = x * (window.right - window.left) / window.w + window.left
        my = (window.h - y) * (window.top - window.bottom) / window.h + window.bottom

        # verificar clique no botão
        if reset_button.inside(mx, my):
            for s in sliders:
                s.value = 0.5
            glutPostRedisplay()
            return

        # verificar clique nos sliders
        for s in sliders:
            if s.inside(mx, my):
                current_slider = s
                s.update_value(mx)
                glutPostRedisplay()
                break

    if button == GLUT_LEFT_BUTTON and state == GLUT_UP:
        current_slider = None

def motion(x, y):
    global current_slider
    if current_slider:
        mx = x * (window.right - window.left) / window.w + window.left
        current_slider.update_value(mx)
        glutPostRedisplay()


if __name__ == "__main__":
    window = Window(800, 600, b"Sliders RGB com Reset")
    window.create()
    window.configure_visualization()

    sliders.append(Slider(0, 100, 100, 30, (1, 0, 0)))
    sliders.append(Slider(0, 50, 100, 30, (0, 1, 0)))
    sliders.append(Slider(0, 0, 100, 30, (0, 0, 1)))

    reset_button = Button(60, -40, 40, 30, "Reset")

    glutDisplayFunc(display)
    glutMouseFunc(mouse)
    glutMotionFunc(motion)
    glutMainLoop()
