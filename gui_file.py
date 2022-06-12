# -*- coding: utf-8 -*-

"""
---
git log --pretty=format:"%h %s" --graph
---

makes graph of commits, looks nice, is in plain text.


"""

import json
import os
import subprocess
import sys

import pandas as pd

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
from datetime import datetime
import psutil
import re


monitor = get_monitors()[0]
width = monitor.width
height = monitor.height - 50

path_to_font = "/home/kallatt/Documents/Fonts/PragmataPro_Mono_R_liga_0826.ttf"


def gst(location):
    cwd = os.getcwd()
    os.chdir(location)
    res = subprocess.check_output(['git', 'status'])
    res = res.decode('utf-8')
    os.chdir(cwd)

    gst_bits = {k: False for k in "!?*+>x"}

    for line in res.split("\n"):
        for key, grep in zip(list("!?*+>x"), ["modified:", "Untracked files", "Your branch is ahead of",
                                              "new file:", "renamed:", "deleted:"]):
            if grep in line:
                gst_bits[key] = True

    return "".join([k for k, v in gst_bits.items() if v])


def get_ram_usage():
    """
    Obtains the absolute number of RAM bytes currently in use by the system.
    :returns: System RAM usage in bytes.
    :rtype: int
    """
    return int(psutil.virtual_memory().total - psutil.virtual_memory().available)


opened_state = True
git_activity = gitlog.plot_git_activity()
project_registration_sheet = None
project_removal_verification = None
cloc_res = None

cwd = os.getcwd()
cloc_res = subprocess.check_output(["cloc", "--exclude-dir=venv", "--json", "--include-ext=py", "--by-file", cwd])
cloc_res = json.loads(cloc_res)

cloc_res = {k[len(cwd):] if k.startswith(cwd) else k: v for k, v in cloc_res.items() if k != "header"}
# sum_line = cloc_res.pop("SUM")
files = list(cloc_res.keys())
cloc_res = {cat: [cloc_res[k].get(cat, None) for k in files] for cat in ['blank', 'comment', 'code', 'language']}
cloc_res = {'files': files, **cloc_res}

cloc_res = pd.DataFrame(cloc_res)
cloc_res.set_index('files')


def frame_commands():
    global git_activity, project_registration_sheet, project_removal_verification, cloc_res
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    io = imgui.get_io()

    if io.key_ctrl and io.keys_down[glfw.KEY_Q]:
        sys.exit(0)

    restricted_flags = imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE
    restricted_with_scroll = restricted_flags | imgui.WINDOW_ALWAYS_VERTICAL_SCROLLBAR

    column_widths = [700, 750, 700, 850, 400]
    x_positions = [50]
    for x in column_widths[:-1]:
        x_positions.append(x_positions[-1] + x + 50)
    x_positions[-1] = width - 50 - column_widths[-1]

    column_index = 0

    # column 1
    imgui.set_next_window_size(column_widths[column_index], height-100)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("Project List", flags=restricted_with_scroll)
    imgui.text("Open Project...\n---------------")
    with DatabaseObject(db_file) as dbo:
        cats = dbo.get_categories()
        for project_row in dbo.get_projects():
            name = project_row['project_name']
            loc = project_row['project_location']
            cat_id = project_row['category_id']
            vcs_upstream = project_row['vcs_upstream']

            status = gst(loc)
            if status:
                status = f" ({status})"

            if vcs_upstream is None:
                vcs_upstream = "Local"
            else:
                pattern = re.compile(r"https://github.com/([^/]+)/([^/]+)\.git")
                match = re.match(pattern, vcs_upstream)
                if match is not None:
                    vcs_upstream = "{"+f"GitHub->{match.group(2)}"+"}"

            vcs_upstream = f"Upstream: {vcs_upstream}"
            button_text = [
                cats.get(cat_id, "-") + ": " + name,
                f"\t~/{os.path.relpath(loc, os.path.expanduser('~'))}",
                f"\t{vcs_upstream}{status}"
            ]
            if imgui.button("\n".join(button_text)):
                cwd = os.getcwd()
                os.chdir(loc)
                os.system(f"gnome-terminal")
                os.chdir(cwd)

    imgui.end()

    # column 2
    column_index += 1
    imgui.set_next_window_size(column_widths[column_index], 80)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("ps aux", flags=restricted_flags)

    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # e.g. 4015976448
    mem_gib = mem_bytes / (1024. ** 3)  # e.g. 3.74
    ram_usage = get_ram_usage() / (1024. ** 3)

    cfo = psutil.cpu_freq()
    cpu_freq = cfo.current / 1000
    cpu_count = psutil.cpu_count()

    cpu_freq_text = f"ClkSpd {cpu_freq:.2f}GHz"
    cpu_count_text = f"CPUCores: {cpu_count}"

    bar_len = 25

    ram_index = int(bar_len * ram_usage / mem_gib)
    cpu_index = int(bar_len * (cpu_freq * 1000 - cfo.min) / (cfo.max - cfo.min))

    imgui.text(f"RAM |{('#' * ram_index).ljust(bar_len)}| {ram_usage:.1f} / {mem_gib:.1f} GiB RAM Used.")
    imgui.text(f"CPU |{('#' * cpu_index).ljust(bar_len)}| {cpu_freq_text}, {cpu_count_text}")

    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], 300)
    imgui.set_next_window_position(x_positions[column_index], 180)
    imgui.begin("code commit", flags=restricted_flags)

    if imgui.button(" - Commit Code - "):
        cwd = os.getcwd()
        now = datetime.now().strftime("%y/%m/%d - %H:%M:%S")
        with DatabaseObject(db_file) as dbo:
            for project_row in dbo.get_projects():
                loc = project_row['project_location']
                vcs_upstream = project_row['vcs_upstream']
                os.chdir(loc)
                os.system(f"git add --all; git commit -m \"autocompile {now}\"")

                if vcs_upstream is not None:
                    os.system("git push")

        os.chdir(cwd)

    if imgui.button(" - Pull Code - "):
        cwd = os.getcwd()
        with DatabaseObject(db_file) as dbo:
            for project_row in dbo.get_projects():
                loc = project_row['project_location']
                vcs_upstream = project_row['vcs_upstream']
                if vcs_upstream is not None:
                    os.chdir(loc)
                    os.system("git pull")

        os.chdir(cwd)

    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], 300)
    imgui.set_next_window_position(x_positions[column_index], 530)
    imgui.begin("project registration", flags=restricted_flags)

    imgui.text(" - Register Project - ")

    json_obj = {
        "project_name": "",
        "project_location": str(os.path.expanduser("~")),
        "project_board": None,
        "vcs_upstream": None,
        "category_id": None
    }

    changed, json_format = imgui.input_text_multiline("", json.dumps(json_obj, indent=2), 1024,
                                                      column_widths[column_index]-10, 210)

    if changed:
        project_registration_sheet = json_format

    if imgui.button("Register"):
        successful = True
        if project_registration_sheet is None:
            successful = False
        else:
            try:
                json_obj = json.loads(project_registration_sheet)
            except json.JSONDecodeError:
                successful = False

        if successful:
            with DatabaseObject(db_file) as dbo:
                dbo.register_project(**json_obj)

        project_registration_sheet = None

    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], height - 980)
    imgui.set_next_window_position(x_positions[column_index], 880)
    imgui.begin("project removal", flags=restricted_flags)

    changed, removal_format = imgui.input_text("", "", 256)

    if changed:
        project_removal_verification = removal_format

    if imgui.button("Remove Project"):
        with DatabaseObject(db_file) as dbo:
            dbo.remove_project(project_removal_verification)

    imgui.end()

    # column 3
    column_index += 1

    imgui.set_next_window_size(column_widths[column_index], height - 100)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("dbo_info", flags=restricted_with_scroll)

    with DatabaseObject(db_file) as dbo:
        imgui.text(str(dbo))

    imgui.end()

    # column 4
    column_index += 1

    imgui.set_next_window_size(column_widths[column_index], 400)
    imgui.set_next_window_position(x_positions[column_index], height-450)
    imgui.begin("cloc", flags=restricted_flags)

    imgui.text(str(cloc_res))

    imgui.end()

    # column 5
    column_index += 1
    imgui.set_next_window_size(column_widths[column_index], 50)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("clock", flags=restricted_flags)

    now = datetime.now()
    fmt = now.strftime("%y/%m/%d - %H:%M:%S")
    imgui.text(f"{fmt} -- {io.framerate:.2f}fps")
    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], 700)
    imgui.set_next_window_position(x_positions[column_index], height-750)

    imgui.begin("Git History", flags=restricted_flags)
    imgui.text(git_activity)
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
