# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from database_api import version as app_version
from database_api import get_dbo_str, db_file, DatabaseObject
# For Linux/Wayland users.
if os.getenv("XDG_SESSION_TYPE") == "wayland":
    os.environ["XDG_SESSION_TYPE"] = "x11"

import glfw
import OpenGL.GL as gl
import imgui
from imgui.integrations.glfw import GlfwRenderer
import gitlog
from screeninfo import get_monitors

monitor = get_monitors()[0]
width = monitor.width - 400
height = monitor.height - 400

path_to_font = "/home/kallatt/Documents/Fonts/PragmataPro_Mono_R_liga_0826.ttf"

opened_state = True


def frame_commands():
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    io = imgui.get_io()

    if io.key_ctrl and io.keys_down[glfw.KEY_Q]:
        sys.exit(0)

    result = gitlog.plot_git_activity()

    no_title_no_resize = imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE

    imgui.set_next_window_size(400, 400)
    imgui.set_next_window_position(width-450, height-450)

    imgui.begin("Git History", flags=no_title_no_resize)
    imgui.text(result)
    imgui.end()

    imgui.set_next_window_size(500, height-100)
    imgui.set_next_window_position(50, 50)
    imgui.begin("Project List", flags=no_title_no_resize | imgui.WINDOW_ALWAYS_VERTICAL_SCROLLBAR)
    imgui.text("Open Project...\n---------------")
    with DatabaseObject(db_file) as dbo:
        # dbo.register_project(proj_name, loc)
        cats = dbo.get_categories()
        for project_row in dbo.get_projects():
            name = project_row['project_name']
            loc = project_row['project_location']
            cat_id = project_row['category_id']
            if imgui.button(cats[cat_id] + ": " + name):
                subprocess.Popen(['xdg-open', loc])
            imgui.text("\t~/"+os.path.relpath(loc, os.path.expanduser('~')))
    imgui.end()


def render_frame(impl, window, font):
    glfw.poll_events()
    impl.process_inputs()
    imgui.new_frame()

    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    if font is not None:
        imgui.push_font(font)
    frame_commands()
    if font is not None:
        imgui.pop_font()

    imgui.render()
    impl.render(imgui.get_draw_data())
    glfw.swap_buffers(window)


def impl_glfw_init():
    # print(str(width) + 'x' + str(height))

    window_name = f"Project Manager K - {app_version.replace('_', '.')}"

    if not glfw.init():
        print("Could not initialize OpenGL context")
        sys.exit(1)

    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, gl.GL_TRUE)

    window = glfw.create_window(int(width), int(height), window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        print("Could not initialize Window")
        sys.exit(1)

    return window


def main():
    imgui.create_context()
    window = impl_glfw_init()

    impl = GlfwRenderer(window)

    io = imgui.get_io()
    jb = io.fonts.add_font_from_file_ttf(path_to_font, 25) if path_to_font is not None else None
    impl.refresh_font_texture()

    while not glfw.window_should_close(window):
        render_frame(impl, window, jb)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()