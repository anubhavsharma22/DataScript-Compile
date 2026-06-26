import pandas as pd
from utils.dsl_parser import DSLProcessor

def test_drop_column():
    df = pd.DataFrame({'a': [1,2], 'b': [3,4]})
    script = "DROP 'b'; SAVE 'out.csv';"
    processor = DSLProcessor(df)
    out_df, fname = processor.process(script)
    assert 'b' not in out_df.columns
    assert fname == 'out.csv'

def test_rename_column():
    df = pd.DataFrame({'x': [1], 'y': [2]})
    script = "RENAME 'x' TO 'z'; SAVE 'out.csv';"
    processor = DSLProcessor(df)
    out_df, fname = processor.process(script)
    assert 'z' in out_df.columns
    assert fname == 'out.csv'

def test_filter_rows():
    df = pd.DataFrame({'age': [20, 40]})
    script = "FILTER 'age > 30'; SAVE 'out.csv';"
    processor = DSLProcessor(df)
    out_df, fname = processor.process(script)
    assert len(out_df) == 1
    assert out_df.iloc[0]['age'] == 40

def test_sort():
    df = pd.DataFrame({'val': [2,1]})
    script = "SORT 'val' ASC; SAVE 'out.csv';"
    processor = DSLProcessor(df)
    out_df, fname = processor.process(script)
    assert list(out_df['val']) == [1,2]

def test_save_json():
    df = pd.DataFrame({'a': [1]})
    script = "SAVE 'out.json';"
    processor = DSLProcessor(df)
    out_df, fname = processor.process(script)
    assert fname == 'out.json'
