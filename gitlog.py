import math
import json
import os
import subprocess
import re
from datetime import datetime, date, timedelta
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from database_api import DatabaseObject, db_file

HOME_FOLDER = os.path.expanduser('~')
PROJECTS_FOLDERS = []
ORIGINAL_CWD = os.getcwd()

with DatabaseObject(db_file) as dbo:
    for project_row in dbo.get_projects():
        location = project_row['project_location']
        if os.path.exists(f"{location}/.git"):
            PROJECTS_FOLDERS.append(location)

DITHERING_BLOCKS = list("_*:#")


def get_git_log(project_index):
    project = PROJECTS_FOLDERS[project_index]

    os.chdir(project)
    res = subprocess.check_output(['git', 'log'])
    res = res.decode('utf-8')

    os.chdir(ORIGINAL_CWD)

    pattern = re.compile(r"commit ([0-9a-f]+)\nAuthor: (.+)(<.+>)\nDate:(.+)\n")
    re_res = re.finditer(pattern, res)

    starts = []
    ends = []

    commit_ids = []
    authors = []
    author_emails = []
    dates = []

    for match in re_res:
        starts.append(match.span()[0])
        ends.append(match.span()[1])

        commit_ids.append(match.group(1).strip())
        authors.append(match.group(2).strip())
        author_emails.append(match.group(3).strip())
        dates.append(match.group(4).strip())

    log = {
        commit_id: (author, email, date)
        for commit_id, author, email, date in zip(commit_ids, authors, author_emails, dates)
    }

    starts.append(len(res))
    commits = []

    for s, m, e in zip(starts[:-1], ends, starts[1:]):
        commits.append((res[s:m], res[m:e]))

    # for commit in commits:
    #     print("----***----")
    #     print(commit[0].strip())
    #     print("----")
    #     print(commit[1])

    return log


def organize_by_date(log):
    strptime_format = "%a %b %d %H:%M:%S %Y %z"
    organized = {}
    for commit_id, tup in log.items():
        auth, email, date = tup
        date_obj = datetime.strptime(date, strptime_format)

        org_by = date_obj.date()

        key = str(org_by)

        lst = organized.get(key, [])
        lst.append((commit_id, auth, email, date, date_obj))
        organized[key] = lst

    return organized


def daterange(sd, ed):
    for n in range(int((ed - sd).days) + 1):
        yield sd + timedelta(n)


def clamp(n, mi, ma):
    return min(max(n, mi), ma)


def get_git_log_summary(start_date=None, end_date=None):
    all_orgd = {}
    for i in range(len(PROJECTS_FOLDERS)):
        lg = get_git_log(i)
        # print(json.dumps(lg, indent=2))
        orgd = organize_by_date(lg)

        for key in orgd.keys():
            lst = all_orgd.get(key, [])
            lst += orgd[key]
            all_orgd[key] = lst

    orgd = all_orgd

    days = sum([
        [x[4].date() for x in v] for k, v in orgd.items()
    ], [])

    commits_by_days = []

    if start_date is None:
        start_date = min(days)
    if end_date is None:
        end_date = max(days)

    # start_of_year = date(start_date.year, 1, 1)
    # end_of_year = date(end_date.year, 12, 31)

    # print(start_of_year, '-', end_of_year)
    # print(start_date, '-', end_date)

    # for single_date in daterange(start_of_year, end_of_year):
    for single_date in daterange(start_date, end_date):
        key = single_date.strftime("%Y-%m-%d")
        num_commits = len(orgd.get(key, []))
        commits_by_days.append(num_commits)

    return commits_by_days, (start_date, end_date)


def plot_git_activity():
    today = date.today()
    one_year_ago = date(today.year - 1, today.month, today.day)

    cbd, dr = get_git_log_summary(start_date=one_year_ago, end_date=today)
    sd, ed = dr
    dates = [d for d in daterange(sd, ed)]

    # x = dates
    # y = cbd

    # fig, ax = plt.subplots()

    # plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
    # plt.gca().xaxis.set_major_locator(mdates.DayLocator())
    # plt.plot(x, y)
    # plt.gcf().autofmt_xdate()

    num_ticks = 5
    spacing = len(dates) // num_ticks

    # ax.set_xticks([dates[0], *[dates[i] for i in range(spacing, len(dates) - spacing, spacing)], dates[-1]])

    # plt.show()

    max_comms = max(cbd + [1])
    num_blocks = len(DITHERING_BLOCKS)
    dithering_indices = list(map(lambda x: clamp(math.ceil(x * (num_blocks - 1) / max_comms), 0, num_blocks-1), cbd))
    dithering_blocks = list(map(lambda di: DITHERING_BLOCKS[di], dithering_indices))

    by_month = {}
    for d, nc in zip(dates, dithering_blocks):
        dn = d.year * 12 + d.month
        ls = by_month.get(dn, [" " for _ in range(d.day - 1)])
        ls.append(nc)
        by_month[dn] = ls

    sorted_by_month = [(k, v) for k, v in by_month.items()]
    sorted_by_month.sort(key=lambda t: t[0])
    sorted_by_month = ["".join(t[1]) for t in sorted_by_month]

    return "\n".join(sorted_by_month)


if __name__ == '__main__':
    plot_git_activity()
