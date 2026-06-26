import re


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def parse(self):
        commands = []
        while self.pos < len(self.tokens):
            token_type, token_value = self.tokens[self.pos]
            method = getattr(self, f"_parse_{token_type.lower()}", None)
            if not method:
                raise NotImplementedError(f"{token_type} is not supported yet.")
            commands.append(method(token_value))
            self.pos += 1
        return commands

    @staticmethod
    def _quoted_values(token):
        return re.findall(r"'([^']*)'", token)

    def _require_quoted_values(self, token, count, command_name):
        values = self._quoted_values(token)
        if len(values) < count:
            raise ValueError(f"Malformed {command_name} command: {token}")
        return values

    @staticmethod
    def _require_match(pattern, token, command_name):
        match = re.search(pattern, token)
        if not match:
            raise ValueError(f"Malformed {command_name} command: {token}")
        return match

    @staticmethod
    def _stat_result(operation, column):
        return (
            f"result = {{'operation': {operation!r}, 'column': {column!r}, "
            f"'value': df[{column!r}].{operation}()}}"
        )

    @staticmethod
    def _normalize_condition(condition):
        condition = re.sub(r'(?<![<>=!])=(?!=)', '==', condition)
        condition = re.sub(r'\bAND\b', ' and ', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\bOR\b', ' or ', condition, flags=re.IGNORECASE)
        condition = re.sub(r'\bNOT\b', ' not ', condition, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', condition).strip()

    def _parse_fetch(self, token):
        match = self._require_match(
            r"FETCH\s+(.+?)(?:\s+WHERE\s+(.+?))?\s*;?$",
            token,
            "FETCH",
        )
        columns_part = match.group(1).strip()
        condition = match.group(2)
        lines = []
        normalized_condition = self._normalize_condition(condition) if condition else None
        columns = ["*"]
        if columns_part != "*":
            columns = [column.strip() for column in columns_part.split(",") if column.strip()]
            if not columns:
                raise ValueError(f"Malformed FETCH command: {token}")

        lines.append(
            f"fetch_result = run_fetch_query(df, {columns!r}, {normalized_condition!r})"
        )
        lines.append("df = fetch_result.copy()")
        lines.append("result = fetch_result.copy()")
        return "\n".join(lines)

    def _parse_load(self, token):
        match = self._require_match(r"LOAD(?:\s+'([^']+)')?\s*;", token, "LOAD")
        file_name = match.group(1)
        if not file_name:
            return "# LOAD command without filename ignored"
        return f"df = pd.read_csv({file_name!r})"

    def _parse_save(self, token):
        file_name = self._require_quoted_values(token, 1, "SAVE")[0]
        return f"output_filename = {file_name!r}"

    def _parse_drop(self, token):
        column_name = self._require_quoted_values(token, 1, "DROP")[0]
        return f"df = df.drop(columns=[{column_name!r}])"

    def _parse_dropna(self, token):
        return "df = df.dropna()"

    def _parse_fillna(self, token):
        col, val = self._require_quoted_values(token, 2, "FILLNA")[:2]
        return f"df[{col!r}] = df[{col!r}].fillna({val!r})"

    def _parse_rename(self, token):
        old_name, new_name = self._require_quoted_values(token, 2, "RENAME")[:2]
        return f"df = df.rename(columns={{{old_name!r}: {new_name!r}}})"

    def _parse_duplicates(self, token):
        return "df = df.drop_duplicates()"

    def _parse_unique(self, token):
        col = self._require_quoted_values(token, 1, "UNIQUE")[0]
        return f"result = df[{col!r}].drop_duplicates().tolist()"

    def _parse_head(self, token):
        match = self._require_match(r"HEAD\s+(\d+)\s*;", token, "HEAD")
        return f"df = df.head({int(match.group(1))})"

    def _parse_tail(self, token):
        match = self._require_match(r"TAIL\s+(\d+)\s*;", token, "TAIL")
        return f"df = df.tail({int(match.group(1))})"

    def _parse_sort(self, token):
        match = self._require_match(r"SORT\s+'([^']+)'\s*(ASC|DESC)?\s*;", token, "SORT")
        col = match.group(1)
        order = match.group(2) or "ASC"
        ascending = order != "DESC"
        return f"df = df.sort_values(by={col!r}, ascending={ascending})"

    def _parse_reset_index(self, token):
        return "df = df.reset_index(drop=True)"

    def _parse_set_index(self, token):
        col = self._require_quoted_values(token, 1, "SET_INDEX")[0]
        return f"df = df.set_index({col!r})"

    def _parse_filter(self, token):
        condition = self._require_quoted_values(token, 1, "FILTER")[0]
        return f"df = df.query({condition!r})"

    def _parse_query(self, token):
        condition = self._require_quoted_values(token, 1, "QUERY")[0]
        return f"df = df.query({condition!r})"

    def _parse_describe(self, token):
        return "result = df.describe(include='all').reset_index()"

    def _parse_info(self, token):
        return "\n".join([
            "buffer = io.StringIO()",
            "df.info(buf=buffer)",
            "result = buffer.getvalue()",
        ])

    def _parse_shape(self, token):
        return "result = {'rows': int(df.shape[0]), 'columns': int(df.shape[1])}"

    def _parse_columns(self, token):
        return "result = df.columns.tolist()"

    def _parse_duplicate_rows(self, token):
        return "result = df[df.duplicated()].copy()"

    def _parse_isnull(self, token):
        return "result = df.isnull()"

    def _parse_notnull(self, token):
        return "result = df.notnull()"

    def _parse_value_counts(self, token):
        col = self._require_quoted_values(token, 1, "VALUE_COUNTS")[0]
        return (
            f"result = df[{col!r}].value_counts(dropna=False)"
            ".rename_axis('value').reset_index(name='count')"
        )

    def _parse_apply(self, token):
        col, func = self._require_quoted_values(token, 2, "APPLY")[:2]
        return f"df[{col!r}] = df[{col!r}].apply({func})"

    def _parse_map(self, token):
        col, func = self._require_quoted_values(token, 2, "MAP")[:2]
        return f"df[{col!r}] = df[{col!r}].map({func})"

    def _parse_replace(self, token):
        old, new, col = self._require_quoted_values(token, 3, "REPLACE")[:3]
        return f"df[{col!r}] = df[{col!r}].replace({old!r}, {new!r})"

    def _parse_strip(self, token):
        col = self._require_quoted_values(token, 1, "STRIP")[0]
        return f"df[{col!r}] = df[{col!r}].astype(str).str.strip()"

    def _parse_lower(self, token):
        col = self._require_quoted_values(token, 1, "LOWER")[0]
        return f"df[{col!r}] = df[{col!r}].astype(str).str.lower()"

    def _parse_upper(self, token):
        col = self._require_quoted_values(token, 1, "UPPER")[0]
        return f"df[{col!r}] = df[{col!r}].astype(str).str.upper()"

    def _parse_concat(self, token):
        col1, col2, newcol = self._require_quoted_values(token, 3, "CONCAT")[:3]
        return (
            f"df[{newcol!r}] = df[{col1!r}].astype(str) + "
            f"df[{col2!r}].astype(str)"
        )

    def _parse_split(self, token):
        col, sep = self._require_quoted_values(token, 2, "SPLIT")[:2]
        return f"df[{col!r}] = df[{col!r}].astype(str).str.split({sep!r})"

    def _parse_merge(self, token):
        raise NotImplementedError("MERGE is not supported yet in this compiler build.")

    def _parse_join(self, token):
        raise NotImplementedError("JOIN is not supported yet in this compiler build.")

    def _parse_groupby(self, token):
        col, agg = self._require_quoted_values(token, 2, "GROUPBY")[:2]
        return f"df = df.groupby({col!r}).agg({agg!r}).reset_index()"

    def _parse_pivot(self, token):
        raise NotImplementedError("PIVOT is not supported yet in this compiler build.")

    def _parse_melt(self, token):
        raise NotImplementedError("MELT is not supported yet in this compiler build.")

    def _parse_aggregate(self, token):
        col, by, func = self._require_quoted_values(token, 3, "AGGREGATE")[:3]
        return (
            f"df = df.groupby({by!r})[{col!r}]"
            f".agg({func!r}).reset_index(name={col!r})"
        )

    def _parse_sum(self, token):
        col = self._require_quoted_values(token, 1, "SUM")[0]
        return self._stat_result("sum", col)

    def _parse_mean(self, token):
        col = self._require_quoted_values(token, 1, "MEAN")[0]
        return self._stat_result("mean", col)

    def _parse_median(self, token):
        col = self._require_quoted_values(token, 1, "MEDIAN")[0]
        return self._stat_result("median", col)

    def _parse_min(self, token):
        col = self._require_quoted_values(token, 1, "MIN")[0]
        return self._stat_result("min", col)

    def _parse_max(self, token):
        col = self._require_quoted_values(token, 1, "MAX")[0]
        return self._stat_result("max", col)

    def _parse_count(self, token):
        col = self._require_quoted_values(token, 1, "COUNT")[0]
        return self._stat_result("count", col)

    def _parse_std(self, token):
        col = self._require_quoted_values(token, 1, "STD")[0]
        return self._stat_result("std", col)

    def _parse_var(self, token):
        col = self._require_quoted_values(token, 1, "VAR")[0]
        return self._stat_result("var", col)

    def _parse_cumsum(self, token):
        col = self._require_quoted_values(token, 1, "CUMSUM")[0]
        return f"df[{col!r}] = df[{col!r}].cumsum()"

    def _parse_cumprod(self, token):
        col = self._require_quoted_values(token, 1, "CUMPROD")[0]
        return f"df[{col!r}] = df[{col!r}].cumprod()"

    def _parse_shift(self, token):
        match = self._require_match(
            r"SHIFT\s+'([^']+)'\s+PERIODS\s+(\d+)\s*;",
            token,
            "SHIFT",
        )
        col, periods = match.group(1), int(match.group(2))
        return f"df[{col!r}] = df[{col!r}].shift({periods})"

    def _parse_rolling(self, token):
        match = self._require_match(
            r"ROLLING\s+WINDOW\s+(\d+)\s+ON\s+'([^']+)'\s+FUNC\s+'([^']+)'\s*;",
            token,
            "ROLLING",
        )
        window, col, func = int(match.group(1)), match.group(2), match.group(3)
        return f"df[{col!r}] = df[{col!r}].rolling(window={window}).agg({func!r})"

    def _parse_percentile(self, token):
        match = self._require_match(
            r"PERCENTILE\s+'([^']+)'\s+Q\s+(\d+)\s*;",
            token,
            "PERCENTILE",
        )
        col, percentile = match.group(1), int(match.group(2))
        quantile = percentile / 100
        return (
            f"result = {{'operation': 'percentile', 'column': {col!r}, "
            f"'percentile': {percentile}, 'value': df[{col!r}].quantile({quantile})}}"
        )

    def _parse_corr(self, token):
        col1, col2 = self._require_quoted_values(token, 2, "CORR")[:2]
        return (
            f"result = {{'operation': 'corr', 'columns': [{col1!r}, {col2!r}], "
            f"'value': df[{col1!r}].corr(df[{col2!r}])}}"
        )

    def _parse_cov(self, token):
        col1, col2 = self._require_quoted_values(token, 2, "COV")[:2]
        return (
            f"result = {{'operation': 'cov', 'columns': [{col1!r}, {col2!r}], "
            f"'value': df[{col1!r}].cov(df[{col2!r}])}}"
        )

    def _parse_sample(self, token):
        match = self._require_match(r"SAMPLE\s+(\d+)\s*;", token, "SAMPLE")
        return f"df = df.sample({int(match.group(1))})"

    def _parse_drop_duplicates(self, token):
        return "df = df.drop_duplicates()"

    def _parse_reindex(self, token):
        col = self._require_quoted_values(token, 1, "REINDEX")[0]
        return f"df = df.reindex(columns=[{col!r}])"

    def _parse_transpose(self, token):
        return "df = df.transpose()"

    def _parse_explode(self, token):
        col = self._require_quoted_values(token, 1, "EXPLODE")[0]
        return f"df = df.explode({col!r})"
