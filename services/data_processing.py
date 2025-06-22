import pandas as pd
import numpy as np
from scipy import stats
from sklearn.ensemble import IsolationForest
import math

# Sanitization functions for JSON compatibility
def sanitize_value(value):
    """Replace NaN/Inf values with None for JSON compatibility"""
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value

def sanitize_dict(data):
    """Recursively sanitize a dictionary or list"""
    if isinstance(data, dict):
        return {k: sanitize_dict(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict(item) for item in data]
    else:
        return sanitize_value(data)

# Data processing functions
def remove_columns(data_store, file_id: str, columns: list):
    if file_id not in data_store:
        return None
    
    data = data_store[file_id]
    df = data["current_df"].copy()
    
    # Check if columns exist
    missing_cols = [col for col in columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Columns not found: {', '.join(missing_cols)}")
    
    # Remove columns
    df = df.drop(columns=columns)
    
    # Update data store
    data["current_df"] = df
    data["actions"].append(f"Removed columns: {', '.join(columns)}")
    
    return sanitize_dict({
        "remaining_columns": list(df.columns),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "head": df.head(10).to_dict(orient="records"),
        "shape": list(df.shape)
    })

def fill_missing(data_store, file_id: str, column: str, method: str, custom_value: str = None):
    if file_id not in data_store:
        return None
    
    data = data_store[file_id]
    df = data["current_df"].copy()
    
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found")
    
    null_count = df[column].isnull().sum()
    if null_count == 0:
        return sanitize_dict({
            "message": "No missing values found",
            "action": f"No missing values in column '{column}'",
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head(10).to_dict(orient="records"),
            "shape": list(df.shape)
        })
    
    # Determine column type
    col_type = str(df[column].dtype)
    is_numeric = 'float' in col_type or 'int' in col_type
    
    try:
        # Apply fill method
        if method == 'mean' and is_numeric:
            fill_value = df[column].mean()
        elif method == 'median' and is_numeric:
            fill_value = df[column].median()
        elif method == 'mode':
            mode_vals = df[column].mode()
            if len(mode_vals) > 0:
                fill_value = mode_vals[0]
            else:
                raise ValueError("No mode value found")
        elif method == 'custom':
            if custom_value is None:
                raise ValueError("Custom value is required for custom method")
            fill_value = custom_value
            # Convert to appropriate type if numeric
            if is_numeric:
                try:
                    fill_value = float(custom_value) if 'float' in col_type else int(custom_value)
                except ValueError:
                    raise ValueError("Custom value must be numeric for numeric columns")
        else:
            raise ValueError(f"Invalid method '{method}' for column type")
        
        # Fill missing values
        df[column] = df[column].fillna(fill_value)
        action_msg = f"Filled {null_count} missing values in '{column}' with {method}"
        if method == 'custom':
            action_msg += f" (value: {fill_value})"
        
        # Update data store
        data["current_df"] = df
        data["actions"].append(action_msg)
        
        return sanitize_dict({
            "message": "Missing values filled successfully",
            "action": action_msg,
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head(10).to_dict(orient="records"),
            "shape": list(df.shape)
        })
        
    except Exception as e:
        raise ValueError(f"Error filling missing values: {str(e)}")

def detect_outliers(data_store, file_id: str, column: str, method: str):
    if file_id not in data_store:
        return None
        
    df = data_store[file_id]["current_df"]
    
    if column not in df.columns:
        raise ValueError("Column not found")
    
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise ValueError("Column must be numeric")
    
    try:
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
            return sanitize_dict({
                "outlier_count": len(outliers),
                "outlier_indices": outliers.index.tolist(),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            })
        
        elif method == 'zscore':
            z_scores = np.abs(stats.zscore(df[column]))
            outliers = df[z_scores > 3]
            return sanitize_dict({
                "outlier_count": len(outliers),
                "outlier_indices": outliers.index.tolist()
            })
        
        elif method == 'isolation_forest':
            clf = IsolationForest(contamination=0.05, random_state=42)
            preds = clf.fit_predict(df[[column]])
            outliers = df[preds == -1]
            return sanitize_dict({
                "outlier_count": len(outliers),
                "outlier_indices": outliers.index.tolist()
            })
        
        raise ValueError("Invalid detection method")
    except Exception as e:
        raise e

def handle_outliers(data_store, file_id: str, action: str, column: str, outlier_indices: list):
    if file_id not in data_store:
        return None
        
    data = data_store[file_id]
    df = data["current_df"].copy()
    
    if column not in df.columns:
        raise ValueError("Column not found")
    
    try:
        if action == 'remove':
            df = df.drop(index=outlier_indices)
            action_msg = f"Removed {len(outlier_indices)} outliers from '{column}'"
        
        elif action == 'cap':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            df.loc[outlier_indices, column] = df.loc[outlier_indices, column].clip(lower_bound, upper_bound)
            action_msg = f"Capped {len(outlier_indices)} outliers in '{column}'"
        
        elif action == 'mark':
            df['is_outlier'] = 0
            df.loc[outlier_indices, 'is_outlier'] = 1
            action_msg = f"Marked {len(outlier_indices)} outliers in '{column}'"
        
        else:
            raise ValueError("Invalid action")
        
        data["current_df"] = df
        data["actions"].append(action_msg)
        
        return sanitize_dict({
            "message": "Outliers handled successfully",
            "action": action_msg,
            "head": df.head(10).to_dict(orient="records"),
            "shape": list(df.shape)
        })
    except Exception as e:
        raise e
