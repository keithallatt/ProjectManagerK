"""
Tool for organizational purposes.

Features I want:
 - Setting up tasks and time frames for completion and checkpoints.
 - Assigning priority to tasks
 - Label task dependencies
"""
from datetime import date
from dataclasses import dataclass


@dataclass
class Task:
    name: str
    description: str
    start: date
    end: date = None

    def __str__(self):
        lines = [
            self.name,
            self.start.strftime("%Y / %m / %d"),
            "-" * len(self.name)
        ]
        if self.end is not None:
            lines[1] += " --- " + self.end.strftime("%Y / %m / %d")

        desc_width = 40
        description = self.description.split(" ")

        line = []

        while description:
            word = description.pop(0)
            if len(" ".join(line)) + len(word) + 1 > desc_width:
                if len(" ".join(line)) < desc_width - 3:
                    # hyphenate
                    ll = desc_width - len(" ".join(line)) - 1
                    line.append(word[:ll] + "-")
                    word = word[ll:]

                lines.append(" ".join(line))
                line = [word]
            else:
                line += [word]

        lines.append(" ".join(line))

        return "\n".join(lines)


class TaskScheduler:
    def __init__(self):
        self.tasks = []

    def schedule_task(self, task: Task) -> bool:
        self.tasks.append(task)


if __name__ == '__main__':
    task_scheduler = TaskScheduler()
    print(Task('Sample Task', 'YERTT', date(1999, 3, 16), date(1999, 3, 18)))
