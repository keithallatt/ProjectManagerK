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
from barcode_reader import get_barcode
import re


monitor = get_monitors()[0]
width = monitor.width
height = monitor.height - 50

path_to_font = "/home/kallatt/Documents/Fonts/PragmataPro_Mono_R_liga_0826.ttf"

with open("hackertyper.txt", "r") as hacker_typer:
    source = hacker_typer.read()
if not os.path.exists("hackertyper.txt"):
    source = "."


def gln(n):
    return f"{hex(n)[2:].rjust(6)}\t"


def gst(location):
    cwd = os.getcwd()
    os.chdir(location)
    res = subprocess.check_output(['git', 'status'])
    res = res.decode('utf-8')
    os.chdir(cwd)

    bits = {
        "dirty": False,
        "untracked": False,
        "ahead": False,
        "newfile": False,
        "renamed": False,
        "deleted": False
    }

    bit_chars = {
        "renamed": ">",
        "ahead": "*",
        "newfile": "+",
        "untracked": "?",
        "deleted": "x",
        "dirty": "!",
    }

    for line in res.split("\n"):
        for key, grep in zip(
            ["dirty", "untracked", "ahead", "newfile", "renamed", "deleted"],
            ["modified:", "Untracked files", "Your branch is ahead of", "new file:", "renamed:", "deleted:"]
        ):
            if grep in line:
                bits[key] = True

    bits_str = "".join([bit_chars[key] for key in bit_chars.keys() if bits[key]])
    return bits_str



def get_ram_usage():
    """
    Obtains the absolute number of RAM bytes currently in use by the system.
    :returns: System RAM usage in bytes.
    :rtype: int
    """
    return int(psutil.virtual_memory().total - psutil.virtual_memory().available)


contents = gln(1)
source_index = 0
source_speed = 32
line_number = 1
opened_state = True
metric_lines = [
    [] for _ in range(16)
]
metric_message, metric_index = " "*100 + get_barcode(), 0
git_activity = gitlog.plot_git_activity()
project_registration_sheet = None


def frame_commands():
    global contents, source, source_index, source_speed, line_number, metric_index, metric_message, git_activity, project_registration_sheet
    gl.glClearColor(0.1, 0.1, 0.1, 1)
    gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    io = imgui.get_io()

    if io.key_ctrl and io.keys_down[glfw.KEY_Q]:
        sys.exit(0)

    no_title_no_resize = imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_MOVE

    column_widths = [700, 1100, 600, 735, 400]
    x_positions = [50]
    for x in column_widths[:-1]:
        x_positions.append(x_positions[-1] + x + 50)
    x_positions[-1] = width - 50 - column_widths[-1]

    column_index = 0

    # column 1
    imgui.set_next_window_size(column_widths[column_index], height-100)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("Project List", flags=no_title_no_resize | imgui.WINDOW_ALWAYS_VERTICAL_SCROLLBAR)
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
                vcs_upstream = f"GitHub: {match.group(2)}"

            vcs_upstream = f"Git Upstream: {vcs_upstream}"
            button_text = [
                cats[cat_id] + ": " + name,
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
    for _ in range(source_speed):
        char_to_be_added = source[source_index]
        # if char_to_be_added == "\t":
        #     char_to_be_added = "|   "

        contents += char_to_be_added

        if char_to_be_added == "\n":
            line_number += 1
            contents += gln(line_number)
        source_index += 1
        source_index %= len(source)

    line_cutoff = 79
    if contents.count("\n") >= line_cutoff:
        contents = "\n".join(contents.split("\n")[-line_cutoff:])

    imgui.set_next_window_size(column_widths[column_index], height-100)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("", flags=no_title_no_resize)

    draw_list = imgui.get_window_draw_list()
    hacker_green = imgui.get_color_u32_rgba(0.12549019607843137, 0.7607843137254902, 0.054901960784313725, 1)
    draw_list.add_text(x_positions[column_index] + 20, 75, hacker_green, contents)
    imgui.end()

    # column 3
    column_index += 1
    imgui.set_next_window_size(column_widths[column_index], 600)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("ps aux", flags=no_title_no_resize)

    mem_bytes = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')  # e.g. 4015976448
    mem_gib = mem_bytes / (1024. ** 3)  # e.g. 3.74
    ram_usage = get_ram_usage() / (1024. ** 3)

    imgui.text(f"{ram_usage:.1f} / {mem_gib:.1f} GiB RAM Used.")

    cfo = psutil.cpu_freq()
    cpu_freq = cfo.current / 1000
    cpu_count = psutil.cpu_count()

    cpu_freq_text = f"ClkSpd {cpu_freq:.2f}GHz"
    cpu_count_text = f"CPUCores: {cpu_count}"

    num_lines = len(metric_lines)

    ram_index = int(num_lines * ram_usage / mem_gib)
    cpu_index = int(num_lines * (cpu_freq * 1000 - cfo.min) / (cfo.max - cfo.min))

    imgui.text(f"{cpu_freq_text}, {cpu_count_text}")
    line_len = len("".join(metric_lines[0])) if metric_lines[0] else 0
    metric_line_len = 50
    line_len = min(metric_line_len, line_len + 1)

    imgui.text("-"*line_len + "\\")

    for i in range(num_lines-1, -1, -1):
        if i == 0:
            four_bits = []
            for _ in range(4):
                four_bits.append(1 if metric_message[metric_index] == "#" else 0)
                metric_index = (metric_index + 1) % len(metric_message)
            hex_digit = sum([(1 << (3-i)) * four_bits[i] for i in range(4)])
            hex_digit ^= (((source_index >> 4) ^ 0b1010) & 0b1111)
            metric_lines[i].append('0123456789abcdef'[hex_digit])
        elif i == ram_index == cpu_index:
            metric_lines[i].append("X")
        elif i == ram_index:
            metric_lines[i].append(">")
        elif i == cpu_index:
            metric_lines[i].append("<")
        else:
            metric_lines[i].append(" ")
        if len(metric_lines[i]) > metric_line_len:
            metric_lines[i] = metric_lines[i][-metric_line_len:]

        imgui.text("".join(metric_lines[i]) + "|")
    imgui.text("-"*line_len + "/")
    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], height - 750)
    imgui.set_next_window_position(x_positions[column_index], 700)
    imgui.begin("code commit", flags=no_title_no_resize)

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

    imgui.text(" - Register Project - ")

    # imgui.same_line()

    json_obj = {
        "project_name": "",
        "project_location": str(os.path.expanduser("~")),
        "project_board": None,
        "vcs_upstream": None,
        "category_id": None
    }

    changed, json_format = imgui.input_text_multiline("label", json.dumps(json_obj, indent=2), 1024, 700, 250)

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


    """
        
{
  "project_name": "CustomIDE",
  "project_location": "/home/kallatt/PycharmProjects/CustomIDE",
  "project_board": null,
  "vcs_upstream": "https://github.com/keithallatt/CustomIDE.git",
  "category_id": 1
}
        
        """


    # column 4
    column_index += 1

    imgui.set_next_window_size(column_widths[column_index], height - 100)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("dbo_info", flags=no_title_no_resize)

    with DatabaseObject(db_file) as dbo:
        imgui.text(str(dbo))

    imgui.end()

    # column 5
    column_index += 1
    imgui.set_next_window_size(column_widths[column_index], 50)
    imgui.set_next_window_position(x_positions[column_index], 50)
    imgui.begin("clock", flags=no_title_no_resize)

    now = datetime.now()
    fmt = now.strftime("%y/%m/%d - %H:%M:%S")
    imgui.text(f"{fmt} -- {io.framerate:.2f}fps")
    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], height - 650)
    imgui.set_next_window_position(x_positions[column_index], 150)
    imgui.begin("filler 3", flags=no_title_no_resize)
    imgui.end()

    imgui.set_next_window_size(column_widths[column_index], 400)
    imgui.set_next_window_position(x_positions[column_index], height-450)

    imgui.begin("Git History", flags=no_title_no_resize)
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
