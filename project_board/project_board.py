from __future__ import annotations


class ProjectLabels:
    labels = {
        "Feature Request": "#22ff22",
        "Refactor": "#eeee22",
        "Hard Problem": "#ff8822",
        "Bug Fix": "#ff2222",
        "Documentation": "#2222ff"
    }

    def __init__(self, *labels):
        self.labels = {" ".join(map(str.capitalize, l.split(" ")))
                       for l in labels if l.lower() in map(str.lower, ProjectLabels.labels.keys())}

    def __or__(self, other: ProjectLabels):
        return ProjectLabels(self.labels.union(other.labels))

    def __and__(self, other: ProjectLabels):
        return ProjectLabels(self.labels.intersection(other.labels))

    def __str__(self):
        return str(self.labels)

    @staticmethod
    def rows():
        return [{"label": label, "color": color} for label, color in ProjectLabels.labels.items()]

    def code(self):
        return sum([(1 << i) * int(x in self.labels) for i, x in enumerate(ProjectLabels.labels.keys())])

    @classmethod
    def from_code(cls, code):
        return ProjectLabels(*{label for i, label in enumerate(ProjectLabels.labels.keys()) if code & (1 << i)})


class Card:
    def __init__(self, card_name, contents, labels):
        self.card_name = card_name
        self.contents = contents
        self.labels = labels


class ProjectBoard:
    def __init__(self, board_name):
        self.name = board_name
        self.lists = {
            "To Do": [],
            "Completed": []
        }

    def add_list(self, list_name):
        if list_name in self.lists.keys():
            return
        self.lists[list_name] = []

    def remove_list(self, list_name):
        if list_name in self.lists.keys():
            self.lists.pop(list_name)

    def add_card(self, list_name: str, card: Card):
        self.lists[list_name].append(card)

    def remove_card(self, list_name: str, card_index: int):
        if list_name not in self.lists.keys():
            return
        card = self.lists[list_name][card_index]
        self.lists[list_name].remove(card)

    def remove(self, list_name: str, card: Card):
        if list_name not in self.lists.keys():
            return
        self.lists[list_name].remove(card)

    def filter_by_label(self, label: ProjectLabels, exact: bool = True):
        label_filter = {
            True: lambda x: x.labels.code() == label.code(),
            False: lambda x: x.labels.code() & label.code()
        }[exact]
        return {ln: filter(label_filter, ls) for ln, ls in self.lists.items()}
