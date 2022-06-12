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
    @staticmethod
    def git_validate(document):
        """ validate on git commands. """
        tokens = document.text.strip().split(" ")
        assert tokens.pop(0) == 'git'

        command = tokens.pop(0)
        args = tokens

        valid_commands = ['commit', 'pull', 'status']
        if command not in valid_commands:
            raise ValidationError(message=f"unknown git command {repr(command)}", cursor_position=len(document.text))

        if len(args) == 1:
            MainloopValidator.project_collision(args[0], document.text, needs_exist=True)
        elif len(args) > 1:
            raise ValidationError(message="too many args (expected 1)", cursor_position=len(document.text))

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
                categories.get(cat_id, "-") + ": " + name,
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
