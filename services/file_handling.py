import pandas as pd
import chardet
import re
import os

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'csv', 'xlsx', 'xls', 'txt'}

def robust_read_csv(file_path: str) -> pd.DataFrame:
    encodings = ['utf-8', 'latin1', 'windows-1252', 'iso-8859-1']
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)
        detected = chardet.detect(raw_data)
        if detected['confidence'] > 0.7 and detected['encoding']:
            encodings.insert(0, detected['encoding'])
    for encoding in encodings:
        try:
            for sep in [',', ';', '\t']:
                try:
                    return pd.read_csv(file_path, encoding=encoding, sep=sep, on_bad_lines='skip')
                except:
                    continue
        except:
            continue
    return pd.read_csv(file_path, encoding='utf-8', errors='replace', on_bad_lines='skip')

def read_file(file_path: str, filename: str) -> pd.DataFrame:
    ext = filename.lower().split('.')[-1]
    if ext in ['csv', 'txt']:
        return robust_read_csv(file_path)
    elif ext in ['xlsx', 'xls']:
        return pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported file format")

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [re.sub(r'[^a-zA-Z0-9_]', '', col) for col in df.columns]
    df.columns = [col.strip().replace(' ', '_') for col in df.columns]
    return df
