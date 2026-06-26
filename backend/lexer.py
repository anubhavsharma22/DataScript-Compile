import re

# Define the token patterns for our DSL (50+ operations)
TOKEN_SPECIFICATION = [
    # Basic file/data operations
    ('FETCH', r'FETCH\s+(\*|[A-Za-z_][A-Za-z0-9_]*(?:\s*,\s*[A-Za-z_][A-Za-z0-9_]*)*)(?:\s+WHERE\s+[^;]+)?\s*;?'),
    ('LOAD', r'LOAD(\s+\'[^\']+\')?\s*;'),
    ('SAVE', r'SAVE\s+\'[^\']+\';'),
    ('DROP', r'DROP\s+\'[^\']+\';'),
    ('DROPNA', r'DROPNA\s*;'),
    ('FILLNA', r'FILLNA\s+\'[^\']+\'\s+WITH\s+\'[^\']+\';'),
    ('RENAME', r'RENAME\s+\'[^\']+\'\s+TO\s+\'[^\']+\';'),
    ('DUPLICATES', r'DROP_DUPLICATES\s*;'),
    ('UNIQUE', r'UNIQUE\s+\'[^\']+\';'),
    ('HEAD', r'HEAD\s+\d+\s*;'),
    ('TAIL', r'TAIL\s+\d+\s*;'),
    ('SORT', r'SORT\s+\'[^\']+\'(\s+(ASC|DESC))?\s*;'),
    ('RESET_INDEX', r'RESET_INDEX\s*;'),
    ('SET_INDEX', r'SET_INDEX\s+\'[^\']+\';'),
    ('FILTER', r'FILTER\s+\'[^\']+\';'),
    ('QUERY', r'QUERY\s+\'[^\']+\';'),
    ('DESCRIBE', r'DESCRIBE\s*;'),
    ('INFO', r'INFO\s*;'),
    ('SHAPE', r'SHAPE\s*;'),
    ('COLUMNS', r'COLUMNS\s*;'),
    ('DUPLICATE_ROWS', r'DUPLICATE_ROWS\s*;'),
    ('ISNULL', r'ISNULL\s*;'),
    ('NOTNULL', r'NOTNULL\s*;'),
    ('VALUE_COUNTS', r'VALUE_COUNTS\s+\'[^\']+\';'),
    ('APPLY', r'APPLY\s+\'[^\']+\'\s+WITH\s+\'[^\']+\';'),
    ('MAP', r'MAP\s+\'[^\']+\'\s+WITH\s+\'[^\']+\';'),
    ('REPLACE', r'REPLACE\s+\'[^\']+\'\s+WITH\s+\'[^\']+\'\s+IN\s+\'[^\']+\';'),
    ('STRIP', r'STRIP\s+\'[^\']+\';'),
    ('LOWER', r'LOWER\s+\'[^\']+\';'),
    ('UPPER', r'UPPER\s+\'[^\']+\';'),
    ('CONCAT', r'CONCAT\s+\'[^\']+\'\s+AND\s+\'[^\']+\'\s+AS\s+\'[^\']+\';'),
    ('SPLIT', r'SPLIT\s+\'[^\']+\'\s+BY\s+\'[^\']+\';'),
    ('MERGE', r'MERGE\s+\'[^\']+\'\s+ON\s+\'[^\']+\';'),
    ('JOIN', r'JOIN\s+\'[^\']+\'\s+ON\s+\'[^\']+\';'),
    ('GROUPBY', r'GROUPBY\s+\'[^\']+\'\s+AGG\s+\'[^\']+\';'),
    ('PIVOT', r'PIVOT\s+INDEX\s+\'[^\']+\'\s+COLUMNS\s+\'[^\']+\'\s+VALUES\s+\'[^\']+\';'),
    ('MELT', r'MELT\s+ID_VARS\s+\'[^\']+\'\s+VALUE_VARS\s+\'[^\']+\';'),
    ('AGGREGATE', r'AGGREGATE\s+\'[^\']+\'\s+BY\s+\'[^\']+\'\s+FUNC\s+\'[^\']+\';'),
    ('SUM', r'SUM\s+\'[^\']+\';'),
    ('MEAN', r'MEAN\s+\'[^\']+\';'),
    ('MEDIAN', r'MEDIAN\s+\'[^\']+\';'),
    ('MIN', r'MIN\s+\'[^\']+\';'),
    ('MAX', r'MAX\s+\'[^\']+\';'),
    ('COUNT', r'COUNT\s+\'[^\']+\';'),
    ('STD', r'STD\s+\'[^\']+\';'),
    ('VAR', r'VAR\s+\'[^\']+\';'),
    ('CUMSUM', r'CUMSUM\s+\'[^\']+\';'),
    ('CUMPROD', r'CUMPROD\s+\'[^\']+\';'),
    ('SHIFT', r'SHIFT\s+\'[^\']+\'\s+PERIODS\s+\d+\s*;'),
    ('ROLLING', r'ROLLING\s+WINDOW\s+\d+\s+ON\s+\'[^\']+\'\s+FUNC\s+\'[^\']+\';'),
    ('PERCENTILE', r'PERCENTILE\s+\'[^\']+\'\s+Q\s+\d+\s*;'),
    ('CORR', r'CORR\s+\'[^\']+\'\s+AND\s+\'[^\']+\';'),
    ('COV', r'COV\s+\'[^\']+\'\s+AND\s+\'[^\']+\';'),
    ('SAMPLE', r'SAMPLE\s+\d+\s*;'),
    ('DROP_DUPLICATES', r'DROP_DUPLICATES\s*;'),
    ('REINDEX', r'REINDEX\s+\'[^\']+\';'),
    ('TRANSPOSE', r'TRANSPOSE\s*;'),
    ('EXPLODE', r'EXPLODE\s+\'[^\']+\';'),
    ('SKIP', r'[ \t\r\n]+'),  # Ignore whitespace and newlines
    ('SEMICOLON', r';'),      # Explicitly match semicolons
    ('MISMATCH', r'.'),       # Any other character
]

# Compile the regex
TOKENS = [(name, re.compile(pattern)) for name, pattern in TOKEN_SPECIFICATION]

class Lexer:
    def __init__(self, text):
        self.text = text

    def tokenize(self):
        text = self.text.strip()
        if text and not text.endswith(';'):
            text = f"{text};"
        pos = 0
        tokens = []
        while pos < len(text):
            match = None
            for token_name, token_regex in TOKENS:
                match = token_regex.match(text, pos)
                if match:
                    if token_name == 'MISMATCH':
                        raise SyntaxError(f"Unexpected token near: {text[pos:pos + 20]!r}")
                    if token_name not in ('SKIP', 'SEMICOLON'):  # Skip whitespace and semicolons
                        tokens.append((token_name, match.group()))
                    pos = match.end(0)
                    break
            if not match:
                raise SyntaxError(f"Unexpected character: {text[pos]}")
        return tokens
