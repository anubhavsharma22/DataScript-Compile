import pandas as pd
from lexer import Lexer
from parser import Parser
from utils.dsl_processor import DSLProcessor

def test_pipeline():
    # Sample CSV
    df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
    df.to_csv('test.csv', index=False)

    script = """
    LOAD 'test.csv';
    DROP 'b';
    SAVE 'out.csv';
    """

    lexer = Lexer(script)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    commands = parser.parse()
    df = pd.read_csv('test.csv')
    processor = DSLProcessor(df)
    result = processor.execute(commands)
    assert 'b' not in result.columns
    print("Test passed.")

if __name__ == "__main__":
    test_pipeline()
