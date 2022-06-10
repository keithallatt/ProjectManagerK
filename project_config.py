import json
import os

HOME_FOLDER = os.path.expanduser('~')
PROJECTS_FOLDERS = []
ORIGINAL_CWD = os.getcwd()

for fp in os.listdir(HOME_FOLDER + "/PycharmProjects"):
    if os.path.exists(HOME_FOLDER + f"/PycharmProjects/{fp}/.git"):
        PROJECTS_FOLDERS.append(HOME_FOLDER + f"/PycharmProjects/{fp}")


def check_activated(func):
    def wrapper(*args, **kwargs):
        assert len(args) >= 1, "Check activated has no self param."
        self = args[0]
        if not self.activated:
            raise Exception("Project has no config file.")
        return func(*args, **kwargs)
    return wrapper


class ProjectConfigObject:
    def __init__(self, project_fp: str):
        self.config_file = f"{os.path.abspath(project_fp)}/.project_config"
        self.activated = os.path.exists(self.config_file)
        self.config_data = "{}"
        self.json_data = {}

    @check_activated
    def open_data(self):
        with open(self.config_file, 'r') as config_file:
            self.config_data = config_file.read()
        with open(self.config_file, 'r') as config_file:
            try:
                self.json_data = json.load(config_file)
            except json.decoder.JSONDecodeError as error:
                print(error)
                self.json_data = {}

    def write_data(self):
        if self.json_data is None:
            self.json_data = {}
        with open(self.config_file, 'w') as config_file:
            json.dump(self.json_data, config_file)

    def __enter__(self):
        self.open_data()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.write_data()

    def __setitem__(self, key, value):
        self.json_data[key] = value

    def __getitem__(self, item):
        return self.json_data.get(item, None)

    def __delitem__(self, key):
        if key in self.json_data.keys():
            self.json_data.pop(key)


if __name__ == '__main__':
    proj_fp = PROJECTS_FOLDERS[0]
    print(proj_fp)

    with ProjectConfigObject(proj_fp) as pco:
        # pco['setting1'] = "hello world!"
        # pco['setting2'] = "hello world!"
        # pco['setting3'] = "hello world!"

        print(pco, pco.json_data)

    print('-'*30)
    print(open(proj_fp + "/.project_config", 'r').read())
