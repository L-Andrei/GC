# main.py
# Ponto de entrada da aplicação.
# Inicializa o GLFW e executa o loop principal.

import sys
import glfw
import state
import callbacks
import rendering

def init_glfw():
    if not glfw.init():
        print('Erro ao iniciar GLFW')
        sys.exit(1)
    glfw.window_hint(glfw.RESIZABLE, glfw.FALSE)
    window = glfw.create_window(state.WINDOW_W, state.WINDOW_H, 'Canvas OpenGL - shapes', None, None)
    if not window:
        glfw.terminate()
        print('Erro ao criar janela')
        sys.exit(1)
    glfw.make_context_current(window)
    
    # Define os callbacks
    glfw.set_mouse_button_callback(window, callbacks.mouse_button_callback)
    glfw.set_cursor_pos_callback(window, callbacks.cursor_pos_callback)
    glfw.set_key_callback(window, callbacks.key_callback)
    glfw.set_scroll_callback(window, callbacks.scroll_callback)
    
    return window


def main():
    window = init_glfw()
    while not glfw.window_should_close(window):
        rendering.render(window)
        glfw.poll_events()
    glfw.terminate()


if __name__ == '__main__':
    main()