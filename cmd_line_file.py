"""
Command line integration for SSH access.
"""
import base64

from numpy import base_repr as _gfb37
from PyInquirer import prompt
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

    for line in res.split("\n"):
        for key, grep in zip(list("!?*+>x"), ["modified:", "Untracked files", "Your branch is ahead of",
                                              "new file:", "renamed:", "deleted:"]):
            if grep in line:
                gst_bits.add(key)

    return "".join(gst_bits)


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

        valid_commands = ['commit', 'pull', 'status']
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
        project_names = [row['project_name'] for row in projects]

    if tokens:
        # implies there was an additional argument
        project_names = [" ".join(tokens)]

    if command == "commit":
        pass
    elif command == "pull":
        pass
    elif command == "status":
        result = []

        for project_row in projects:
            project_name = project_row['project_name']
            if project_name in project_names:
                project_loc = project_row['project_location']
                status = gst(project_loc, raw=True)
                result.append((project_name, '-'*len(project_name), status))

        final = "\n\n".join([
            f"{dashes}\n{name}\n{dashes}\n\n{g_stat}" for name, dashes, g_stat in result
        ])

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


def main():
    startup_line = r"""
__        _______ _     ____ ___  __  __ _____ 
\ \      / / ____| |   / ___/ _ \|  \/  | ____|
 \ \ /\ / /|  _| | |  | |  | | | | |\/| |  _|  
  \ V  V / | |___| |__| |__| |_| | |  | | |___ 
   \_/\_/  |_____|_____\____\___/|_|  |_|_____|
           _  _______ ___ _____ _   _ 
          | |/ / ____|_ _|_   _| | | |
          | ' /|  _|  | |  | | | |_| |
          | . \| |___ | |  | | |  _  |
          |_|\_\_____|___| |_| |_| |_|
    """
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

    _pass = prompt([
        {
            'type': 'password',
            'message': '  Enter your Project Manager password',
            'name': 'password'
        }
    ])

    if _gfb37(13*37*61*(5*37*(2*3*5*5*5*(2*3*3*3*3*3+1)+1)+2), 7*2+2*11).lower() != _pass['password']:
        print("Invalid password")
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

        mainloop_func = {
            'status': mainloop_status,
            'git': mainloop_git
        }.get(command, lambda x: None)
        mainloop_func(tokens)


if __name__ == '__main__':
    main()
