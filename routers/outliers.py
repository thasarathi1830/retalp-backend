from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from state import data_store
import pandas as pd
import numpy as np
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

class DetectRequest(BaseModel):
    file_id: str
    column: str
    method: str

class HandleRequest(BaseModel):
    file_id: str
    action: str
    column: str
    outlier_indices: list

@router.post("/detect")
async def detect_outliers(request: DetectRequest):
    try:
        file_id = request.file_id
        column = request.column
        method = request.method
        
        if file_id not in data_store:
            raise HTTPException(404, "File not found")
        
        df = data_store[file_id]["current_df"]
        
        if method == 'iqr':
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
            outlier_indices = outliers.index.tolist()
            
            return {
                "outlier_count": len(outlier_indices),
                "outlier_indices": outlier_indices,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }
            
        elif method == 'zscore':
            z_scores = (df[column] - df[column].mean()) / df[column].std()
            outlier_indices = np.where(np.abs(z_scores) > 3)[0].tolist()
            
            return {
                "outlier_count": len(outlier_indices),
                "outlier_indices": outlier_indices,
                "z_scores": z_scores.tolist()
            }
            
        else:
            raise ValueError(f"Unsupported method: {method}")
            
    except Exception as e:
        logger.error(f"Outlier detection error: {str(e)}")
        raise HTTPException(500, f"Outlier detection failed: {str(e)}")

@router.post("/handle")
async def handle_outliers(request: HandleRequest):
    try:
        file_id = request.file_id
        action = request.action
        column = request.column
        outlier_indices = request.outlier_indices
        
        if file_id not in data_store:
            raise HTTPException(404, "File not found")
        
        df = data_store[file_id]["current_df"]
        
        if action == 'remove':
            df = df.drop(index=outlier_indices)
        elif action == 'cap':
            lower_bound = df[column].quantile(0.05)
            upper_bound = df[column].quantile(0.95)
            df.loc[df[column] < lower_bound, column] = lower_bound
            df.loc[df[column] > upper_bound, column] = upper_bound
        elif action == 'mark':
            df['is_outlier'] = 0
            df.loc[outlier_indices, 'is_outlier'] = 1
        else:
            raise ValueError(f"Unsupported action: {action}")
        
        data_store[file_id]["current_df"] = df
        data_store[file_id]["actions"].append(f"Handled outliers in {column} using {action}")
        
        return {
            "columns": list(df.columns),
            "head": df.head().to_dict(orient="records"),
            "action": f"Handled outliers in {column} using {action}"
        }
    except Exception as e:
        logger.error(f"Outlier handling error: {str(e)}")
        raise HTTPException(500, f"Outlier handling failed: {str(e)}")
