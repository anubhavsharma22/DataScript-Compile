import pandas as pd
import re

class DSLProcessor:
    """
    Processes DSL commands on a pandas DataFrame.
    Easily extensible for new commands.
    """
    def __init__(self, df):
        self.df = df
        self.processed_filename = None
        # Register commands here
        self.commands = {
            "LOAD": self.cmd_load,
            "DROP": self.cmd_drop,
            "RENAME": self.cmd_rename,
            "FILTER": self.cmd_filter,
            "SORT": self.cmd_sort,
            "SAVE": self.cmd_save,
            # TODO: Add new commands here, e.g. "GROUPBY": self.cmd_groupby,
        }

    def process(self, script):
        for line in script.split(";"):
            line = line.strip()
            if not line:
                continue
            cmd = line.split()[0]
            handler = self.commands.get(cmd)
            if handler:
                handler(line)
            else:
                # TODO: Optionally raise error or log unknown command
                pass
        return self.df, self.processed_filename

    def cmd_load(self, line):
        pass  # LOAD is optional

    def cmd_drop(self, line):
        column_name = re.findall(r"'(.*?)'", line)[0]
        self.df.drop(columns=[column_name], errors='ignore', inplace=True)

    def cmd_rename(self, line):
        parts = re.findall(r"'(.*?)'", line)
        if len(parts) == 2:
            self.df.rename(columns={parts[0]: parts[1]}, inplace=True)

    def cmd_filter(self, line):
        condition = re.findall(r"'(.*?)'", line)[0]
        self.df = self.df.query(condition)

    def cmd_sort(self, line):
        match = re.match(r"SORT\s+'(.+?)'(?:\s+(ASC|DESC))?", line)
        if match:
            col, order = match.groups()
            ascending = (order != "DESC")
            self.df.sort_values(by=col, ascending=ascending, inplace=True)

    def cmd_save(self, line):
        self.processed_filename = re.findall(r"'(.*?)'", line)[0]

    # TODO: Add new command methods here, e.g.:
    # def cmd_groupby(self, line):
    #     ...

    # def cmd_join(self, line):
    #     ...

    # def cmd_pivot(self, line):
    #     ...
