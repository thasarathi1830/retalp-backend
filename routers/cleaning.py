from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from state import data_store
import pandas as pd
import logging
from typing import List, Optional

router = APIRouter()
logger = logging.getLogger(__name__)

# Define Pydantic models for request validation
class RemoveColumnsRequest(BaseModel):
    file_id: str
    columns: List[str]

class FillMissingRequest(BaseModel):
    file_id: str
    column: str
    method: str
    custom_value: Optional[str] = None

@router.post("/remove_columns")
async def remove_columns(request: RemoveColumnsRequest):
    try:
        file_id = request.file_id
        columns = request.columns
        
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="File not found")
        
        df = data_store[file_id]["current_df"]
        
        # Validate columns exist in dataframe
        missing_cols = [col for col in columns if col not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Columns not found: {', '.join(missing_cols)}")
        
        # Remove columns
        df = df.drop(columns=columns)
        data_store[file_id]["current_df"] = df
        
        # Log action
        action = f"Removed columns: {', '.join(columns)}"
        data_store[file_id]["actions"].append(action)
        
        return {
            "status": "success",
            "remaining_columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head().to_dict(orient="records"),
            "shape": list(df.shape),
            "action": action
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Column removal error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Column removal failed: {str(e)}")

@router.post("/fill_missing")
async def fill_missing(request: FillMissingRequest):
    try:
        file_id = request.file_id
        column = request.column
        method = request.method
        custom_value = request.custom_value
        
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="File not found")
        
        df = data_store[file_id]["current_df"]
        
        # Validate column exists
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' not found")
        
        # Fill missing values with validation
        if method == 'mean':
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise HTTPException(status_code=400, detail=f"Column '{column}' must be numeric for mean imputation")
            df[column] = df[column].fillna(df[column].mean())
            
        elif method == 'median':
            if not pd.api.types.is_numeric_dtype(df[column]):
                raise HTTPException(status_code=400, detail=f"Column '{column}' must be numeric for median imputation")
            df[column] = df[column].fillna(df[column].median())
            
        elif method == 'mode':
            mode_series = df[column].mode()
            if len(mode_series) == 0:
                raise HTTPException(status_code=400, detail=f"Column '{column}' has no mode value")
            df[column] = df[column].fillna(mode_series[0])
            
        elif method == 'custom':
            if custom_value is None:
                raise HTTPException(status_code=400, detail="Custom value required for custom imputation")
            df[column] = df[column].fillna(custom_value)
            
        else:
            raise HTTPException(status_code=400, detail=f"Invalid method: {method}")
        
        # Log action
        action = f"Filled missing values in {column} using {method}"
        data_store[file_id]["actions"].append(action)
        
        return {
            "status": "success",
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head().to_dict(orient="records"),
            "shape": list(df.shape),
            "action": action
        }
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"Fill missing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Fill missing failed: {str(e)}")
