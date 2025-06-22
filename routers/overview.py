from fastapi import APIRouter, HTTPException
from state import data_store
import pandas as pd
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/{file_id}")
async def get_overview(file_id: str):
    try:
        if file_id not in data_store:
            raise HTTPException(status_code=404, detail="File not found")
        
        data = data_store[file_id]
        df = data["current_df"]
        
        # Basic statistics
        null_counts = df.isnull().sum().to_dict()
        dtypes = df.dtypes.astype(str).to_dict()
        
        return {
            "file_id": file_id,
            "filename": data["filename"],
            "columns": list(df.columns),
            "dtypes": dtypes,
            "null_counts": null_counts,
            "head": df.head().to_dict(orient="records"),
            "shape": list(df.shape)
        }
    except Exception as e:
        logger.error(f"Overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
