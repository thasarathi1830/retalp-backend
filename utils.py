# You can add any shared utility functions here
import math
import pandas as pd
from typing import Any, Union, Dict, List

def sanitize_value(value: Any) -> Any:
    """Replace NaN/Inf values with None for JSON compatibility"""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value

def sanitize_dict(data: Union[Dict, List]) -> Union[Dict, List]:
    """Recursively sanitize a dictionary or list"""
    if isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    else:
        return sanitize_value(data)

def safe_convert_df(df: pd.DataFrame) -> Dict:
    """Safely convert DataFrame to JSON-serializable format"""
    return {
        "columns": list(df.columns),
        "dtypes": sanitize_dict(df.dtypes.astype(str).to_dict()),
        "null_counts": sanitize_dict(df.isnull().sum().to_dict()),
        "head": sanitize_dict(df.head(20).to_dict(orient="records")),
        "shape": list(df.shape)
    }
