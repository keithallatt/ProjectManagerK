"""
Command line integration for SSH access.
"""
from PyInquirer import prompt
from database_api import DatabaseObject, db_file
from prompt_toolkit.validation import Validator, ValidationError
import subprocess
import re
import os.path


with DatabaseObject(db_file) as dbo:
    categories = dbo.get_categories()


registered_functions = ["git", "status", "register", "remove", "update"]
exit_ = ['q', 'quit', 'exit']


def gst(location):
    """ get the git status of a project """
    cwd = os.getcwd()
    os.chdir(location)
    res = subprocess.check_output(['git', 'status'])
    res = res.decode('utf-8')
    os.chdir(cwd)

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


class MainloopValidator(Validator):
    def validate(self, document):
        doc_text = document.text
        first_token = doc_text.split(" ")[0]

        if first_token in registered_functions:
            return
        if first_token in exit_:
            return
        raise ValidationError(message="command does not exist", cursor_position=len(doc_text))


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


def mainloop_status():
    with DatabaseObject(db_file) as _dbo:
        cats = _dbo.get_categories()
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
                pattern = re.compile(r"https://github.com/([^/]+)/([^/]+\.git)")
                match = re.match(pattern, vcs_upstream)
                if match is not None:
                    vcs_upstream = "{" + f"{match.group(2)}" + "}"

            status_lines.append("\n".join([
                cats.get(cat_id, "-") + ": " + name,
                f"  ~/{os.path.relpath(loc, os.path.expanduser('~'))}",
                f"  Upstream: {vcs_upstream}{status}"
            ]))
        return "\n-----\n".join(status_lines)


def main():
    flags = {
        'quit': False
    }

    while not flags['quit']:
        answers = prompt(main_loop_prompt)
        token_str = answers['main_input']
        tokens = token_str.split(" ")
        if answers['main_input'].lower() in exit_:
            break
        command = tokens.pop(0)

        if command == "status":
            print(mainloop_status())


if __name__ == '__main__':
    main()
