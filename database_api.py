import os
import sqlite3
import project_board.project_board as proboard
import pandas as pd
import time


version = "0_0_1a"

db_file = f"./dbfiles/{version}/cms.db"
table_rows = {
    "categories": [
        "category_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "category_name TEXT NOT NULL UNIQUE",
    ],
    "task_labels": [
        "label_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",
        "label TEXT NOT NULL",
        "color TEXT NOT NULL"
    ],
    "projects": [
        "project_id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL",  # project id: #
        "project_name TEXT NOT NULL UNIQUE",
        "project_location TEXT NOT NULL UNIQUE",
        "created DATETIME NOT NULL",
        "modified DATETIME NOT NULL",
        "project_board TEXT",  # project_board file.
        "vcs_url TEXT",  # url to any vcs service.
        "category_id INT",
        "FOREIGN KEY (category_id) REFERENCES categories (category_id)",
    ],
}


class DatabaseObject:
    def __init__(self, file, force_reset=False):
        self.file = file
        self.force_reset = force_reset

    def get_all_tables(self):
        self.conn.commit()
        cursor = self.conn.execute("SELECT name FROM sqlite_master WHERE "
                                   "type IN ('table','view') AND "
                                   "name NOT LIKE 'sqlite_%' ORDER BY 1;")
        table_tables = []
        for row in cursor:
            table_tables.append(row[0])
        return table_tables

    def get_table_cols(self, table_name):
        schema = self.get_table_schema(table_name)
        col_names = [s[1] for s in schema]
        return col_names

    def get_table_schema(self, table_name):
        query = f"PRAGMA table_info({table_name});"
        cursor = self.conn.execute(query)

        schema = []
        for row in cursor:
            schema.append(row)
        return schema

    def make_table(self, table_name, rows):
        if table_name in self.get_all_tables():
            print(f"Table {table_name} already registered.")
            return

        nl = ",\n"
        query = f'''CREATE TABLE {table_name}({nl.join(rows)});'''
        self.cursor.execute(query)

    def add_row(self, table_name, row: dict):
        cols = list(row.keys())
        vals = [row[x] for x in cols]

        col_s = str(tuple(cols))
        val_s = str(tuple(vals))

        if len(cols) == 1:
            col_s = f"({cols[0]})"
            val_s = f"({repr(vals[0])})"

        for char in ' \'"':
            col_s = col_s.replace(char, '')
        query = f'''INSERT INTO {table_name} {col_s} VALUES {val_s};'''
        self.cursor.execute(query)

    def add_rows(self, table, lst):
        for row in lst:
            self.add_row(table, row)

    def get_categories(self):
        query = "SELECT * FROM categories;"
        cursor = self.conn.execute(query)
        cols = self.get_table_cols("categories")
        rows = []
        for row in cursor:
            rows.append({k: v for k, v in zip(cols, row)})
        return {
            row['category_id']: row['category_name'] for row in rows
        }

    def add_category(self, category_name):
        query = f"INSERT INTO categories (category_name) VALUES ({category_name});"
        self.conn.execute(query)

    def get_projects(self):
        query = "SELECT * FROM projects;"
        cursor = self.conn.execute(query)
        cols = self.get_table_cols("projects")
        rows = []
        for row in cursor:
            rows.append({k: v for k, v in zip(cols, row)})
        return rows

    def register_project(self, project_name, project_location, project_board=None, category_id=None):
        strf_format = "%Y-%m-%d %H:%M:%S"
        ti_c = time.strftime(strf_format, time.gmtime(os.path.getctime(loc)))
        ti_m = time.strftime(strf_format, time.gmtime(os.path.getmtime(loc)))

        row_data = {
            'project_name': project_name,
            "project_location": project_location,
            "created": ti_c,
            "modified": ti_m,
        }

        if project_board is not None:
            row_data['project_board'] = project_board

        if category_id is not None:
            row_data['category_id'] = category_id

        self.add_row("projects", row_data)

    def register_category(self, category_name):
        self.add_row("categories", {"category_name": category_name})

    def update_project(self, project_name, project_location=None, project_board=None, category_id=None):
        update_clause = "UPDATE projects "
        set_clause = "SET " + ", ".join([f"{col} = {val}" for col, val in
                                         zip(["project_location", "project_board", "category_id"],
                                             [project_location, project_board, category_id]) if val is not None])
        where_clause = f"WHERE project_name=\"{project_name}\";"

        update_query = "\n".join([update_clause, set_clause, where_clause])

        self.conn.execute(update_query)

    def __enter__(self):
        file = self.file
        dir_name = file[:-len(file.split("/")[-1])]

        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        if os.path.exists(file) and self.force_reset:
            os.remove(file)

        self.conn = sqlite3.connect(self.file)
        self.cursor = self.conn.cursor()

        table_names = self.get_all_tables()
        for tname, trows in table_rows.items():
            if tname not in table_names:
                self.make_table(tname, trows)
        table_names = self.get_all_tables()

        if "task_labels" in table_names and not list(self.cursor.execute("SELECT * FROM task_labels")):
            self.add_rows("task_labels", proboard.ProjectLabels.rows())

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.commit()
        self.conn.close()

    def __str__(self):
        str_chunks = ["-[ DBO ]-"]
        for table in self.get_all_tables():
            chunk = f"--- {table} ---"
            cols = self.get_table_cols(table)
            df_dict = {key: [] for key in cols}

            for row in self.conn.execute(f"SELECT * FROM {table}"):
                for k, v in zip(cols, row):
                    df_dict[k].append(v)

            df = pd.DataFrame.from_dict(df_dict)
            df = df.set_index(cols[0])

            col_ind = df.columns
            col_lst = list(col_ind)

            for unwanted in ['project_location', 'project_board', 'category_id', 'color']:
                if unwanted in col_lst:
                    col_lst.remove(unwanted)

            col_ind = pd.Index(col_lst)

            chunk += "\n" + df.to_string(columns=col_ind)
            str_chunks.append(chunk)

        return "\n".join(str_chunks)


def get_dbo_str():
    # loc = os.getcwd()
    # proj_name = "Project Manager K"
    with DatabaseObject(db_file) as dbo:
        # dbo.register_project(proj_name, loc)
        return str(dbo)


if __name__ == '__main__':
    with DatabaseObject(db_file) as dbo:
        print(dbo)
