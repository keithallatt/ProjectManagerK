"""
Command line integration for SSH access.
"""
import shlex

from PyInquirer import prompt as prompt
from database_api import DatabaseObject, db_file
from prompt_toolkit.validation import Validator, ValidationError
import subprocess
import re
import os.path
import json
import pandas as pd

with DatabaseObject(db_file) as dbo:
    categories = dbo.get_categories()

# commands we can call from the CMD line tool
registered_functions = ["git", "status", "register", "remove", "update", "help"]
# valid exit commands:
exit_ = ['q', 'quit', 'exit']


def gst(location, raw=False):
    """ get the git status of a project """
    cwd = os.getcwd()
    os.chdir(location)
    res = subprocess.check_output(['git', 'status'])
    res = res.decode('utf-8')
    os.chdir(cwd)

    if raw:
        return res

    gst_bits = set()

    status_markers = ["modified:", "Untracked files", "Your branch is ahead of", "new file:", "renamed:", "deleted:"]
    for line in res.split("\n"):
        for key, grep in zip(list("!?*+>x"), status_markers):
            if grep in line:
                gst_bits.add(key)

    return "".join(gst_bits)


def git_func(location, function, flags=None, *args):
    # commit, pull, push
    assert function in ['commit', 'pull', 'push']
    args = list(map(lambda x: x.replace('"', '\"').replace('\\', '\\').join(["\"", "\""]), args))

    output_lst = ['git', function]
    if flags:
        output_lst.append(f"-{flags}")
    if args:
        output_lst += args

    cwd = os.getcwd()
    os.chdir(location)
    res = subprocess.check_output(output_lst)
    res = res.decode('utf-8')
    os.chdir(cwd)

    return res


class FilepathValidator(Validator):
    def validate(self, document):
        doc_text = document.text
        if not os.path.exists(doc_text):
            raise ValidationError(
                message="Please enter a filepath that exists.",
                cursor_position=len(doc_text)
            )


class ProjectValidator(Validator):
    def validate(self, document):
        doc_text = document.text
        with DatabaseObject(db_file) as _dbo:
            projects = _dbo.get_projects()
            for proj_row in projects:
                if proj_row['project_name'] == doc_text.strip():
                    break
            else:
                raise ValidationError(
                    message="Please enter a valid project name.",
                    cursor_position=len(doc_text)
                )


class MainloopValidator(Validator):
    @staticmethod
    def git_validate(document):
        """ validate on git commands. """
        tokens = document.text.strip().split(" ")

        assert tokens.pop(0) == 'git'
        if not tokens:
            raise ValidationError(message=f"git cannot be called on it's own", cursor_position=len(document.text))
        command = tokens.pop(0)
        post_command_argument = " ".join(tokens)

        valid_commands = ['commit', 'pull', 'push', 'status']
        if command not in valid_commands:
            raise ValidationError(message=f"unknown git command {repr(command)}", cursor_position=len(document.text))

        if post_command_argument.strip():
            MainloopValidator.project_collision(post_command_argument, document.text, needs_exist=True)

    @staticmethod
    def project_collision(project_name, doc_text, needs_exist):
        """
        Extra validation on a document, verifies that a project either exists or doesn't exist.

        :param project_name: The name of the project
        :param doc_text: the document text, used for validation errors.
        :param needs_exist: If True, raises ValidationError on the project not existing, and if False, the reverse.
        """
        # need to check if the argument is a project.
        with DatabaseObject(db_file) as _dbo:
            for row in _dbo.get_projects():
                if row['project_name'] == project_name:
                    if needs_exist:
                        break
                    else:
                        raise ValidationError(message="invalid project name: exists", cursor_position=len(doc_text))
            else:
                if needs_exist:
                    raise ValidationError(message="invalid project name: does not exist", cursor_position=len(doc_text))

    def validate(self, document):
        doc_text = document.text.strip()
        if not doc_text:
            return

        first_token = doc_text.split(" ")[0]

        if first_token in registered_functions:
            extra_validation = {
                'git': lambda doc: MainloopValidator.git_validate(doc)
            }.get(first_token, None)
            if extra_validation is None:
                return

            extra_validation(document)
            return

        if first_token in exit_:
            return

        raise ValidationError(message=f"unknown command {first_token}", cursor_position=len(document.text))


project_registration_questions = [
    {
        'type': 'input',
        'name': 'project_name',
        'message': 'Project Name:',
    },
    {
        'type': 'input',
        'name': 'project_location',
        'message': 'Project Location:',
        'validate': FilepathValidator
    },
    {
        'type': 'input',
        'name': 'vcs_upstream',
        'message': 'VCS Upstream:',
    },
    {
        'type': 'input',
        'name': 'project_board',
        'message': 'Project Board Location:',
    },
    {
        'type': 'list',
        'name': 'category',
        'message': 'Project Category',
        'choices': [None] + [categories[i] for i in sorted(categories.keys())]
    }
]
project_deletion_questions = [
    {
        'type': 'input',
        'name': 'project_name',
        'message': 'Project Name:',
        'validate': ProjectValidator
    },
    {
        'type': 'input',
        'name': 'project_name_confirmation',
        'message': 'Confirm Project Name:',
    }
]
main_loop_prompt = [
    {
        'type': 'input',
        'name': 'main_input',
        'message': '',
        'validate': MainloopValidator
    }
]


def mainloop_status(*_):
    with DatabaseObject(db_file) as _dbo:
        status_lines = []
        for project_row in _dbo.get_projects():
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
                pattern = re.compile(r"https://github.com/([^/]+/[^/]+\.git)")
                match = re.match(pattern, vcs_upstream)
                if match is not None:
                    vcs_upstream = "{" + f"{match.group(1)}" + "}"

            status_lines += [
                f"/----",
                f"| {categories.get(cat_id, '-')}: {name}",
                f"|   ~/{os.path.relpath(loc, os.path.expanduser('~'))}",
                f"|   Upstream: {vcs_upstream}{status}"
            ]
        status_lines.append("\\----")
        print("\n".join(status_lines))


def mainloop_git(tokens, *_):
    """ Ran a git command in mainloop. """
    command = tokens.pop(0)
    with DatabaseObject(db_file) as _dbo:
        projects = _dbo.get_projects()
        project_names = list(map(lambda x: x.get("project_name", None), projects))

    if tokens:
        # implies there was an additional argument
        project_names = [" ".join(tokens)]

    if command == "commit":
        result = []

        for project_row in projects:
            if tokens and " ".join(tokens) not in project_row.values():
                continue
            project_name = project_row['project_name']
            if project_name in project_names:
                project_loc = project_row['project_location']
                status = git_func(project_loc, "commit", "am", "Sample Commit Message")
                if not tokens:
                    result.append(f"{project_name}: {status}")
                else:
                    dashes = '-' * len(project_name)
                    result.append(f"{dashes}\n{project_name}\n{dashes}\n\n{status}\n")

        final = "\n".join(result)

        print(final)
    elif command == "push":
        pass
    elif command == "pull":
        pass
    elif command == "status":
        result = []

        for project_row in projects:
            if tokens and " ".join(tokens) not in project_row.values():
                continue
            project_name = project_row['project_name']
            if project_name in project_names:
                project_loc = project_row['project_location']
                status = gst(project_loc, raw=bool(tokens))
                if not tokens:
                    result.append(f"{project_name}: {status}")
                else:
                    dashes = '-' * len(project_name)
                    result.append(f"{dashes}\n{project_name}\n{dashes}\n\n{status}\n")

        final = "\n".join(result)

        print(final)


def cloc_text(by_file=False):
    cwd = os.getcwd()
    cmd_lst = ["cloc", "--exclude-dir=venv", "--json", "--include-ext=py"]

    if by_file:
        cmd_lst.append("--by_file")

    cmd_lst.append(cwd)

    cloc_res = subprocess.check_output(cmd_lst)
    cloc_res = json.loads(cloc_res)

    cloc_res = {k[len(cwd):] if k.startswith(cwd) else k: v for k, v in cloc_res.items() if k != "header"}

    files = list(cloc_res.keys())
    cloc_res = {cat: [cloc_res[k].get(cat, None) for k in files] for cat in ['blank', 'comment', 'code', 'language']}
    cloc_res = {'files': files, **cloc_res}

    cloc_res = pd.DataFrame(cloc_res)
    cloc_res.set_index('files')

    return cloc_res


# Subroutines.
mainloop_subroutines = {
    'status': mainloop_status,
    'git': mainloop_git
}


def main():
    startup_line = [r"__        _______ _     ____ ___  __  __ _____ ",
                    r"\ \      / / ____| |   / ___/ _ \|  \/  | ____|",
                    r" \ \ /\ / /|  _| | |  | |  | | | | |\/| |  _|  ",
                    r"  \ V  V / | |___| |__| |__| |_| | |  | | |___ ",
                    r"   \_/\_/  |_____|_____\____\___/|_|  |_|_____|",
                    r"           _  _______ ___ _____ _   _          ",
                    r"          | |/ / ____|_ _|_   _| | | |         ",
                    r"          | ' /|  _|  | |  | | | |_| |         ",
                    r"          | . \| |___ | |  | | |  _  |         ",
                    r"          |_|\_\_____|___| |_| |_| |_|         "]
    startup_line = "\n".join(startup_line)

    print(startup_line.strip(), end=("-"*47).join("\n\n"))

    _login = prompt([
        {
            'type': 'confirm',
            'message': '  Do you want to continue?',
            'name': 'continue',
            'default': True,
        },
    ])

    if not _login['continue']:
        return

    print(cloc_text(by_file=False))

    while True:
        answers = prompt(main_loop_prompt)
        token_str = answers['main_input']
        if not token_str.strip():
            continue
        tokens = token_str.split(" ")
        if answers['main_input'].lower() in exit_:
            break
        command = tokens.pop(0)

        mainloop_func = mainloop_subroutines.get(command, lambda x: None)
        mainloop_func(tokens)


if __name__ == '__main__':
    main()
