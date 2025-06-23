from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from io import BytesIO
import chardet
import uuid
import logging

# Import data store
try:
    from state import data_store
except ImportError:
    data_store = {}

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        contents = await file.read()
        
        # Detect encoding for text files
        if file.filename.lower().endswith(('.csv', '.txt')):
            result = chardet.detect(contents)
            encoding = result['encoding'] or 'utf-8'
            try:
                # Try decoding with detected encoding
                file_content = contents.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to replace errors
                file_content = contents.decode(encoding, errors='replace')
            file_like = BytesIO(file_content.encode('utf-8'))
        else:
            file_like = BytesIO(contents)

        # Read file into DataFrame
        if file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_like)
        elif file.filename.lower().endswith(('.csv', '.txt')):
            df = pd.read_csv(file_like)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Supported: CSV, Excel")

        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Store data
        data_store[file_id] = {
            "original_df": df,
            "current_df": df.copy(),
            "actions": []
        }

        return {
            "file_id": file_id,
            "filename": file.filename,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head().to_dict(orient="records"),
            "shape": list(df.shape)
        }
    except Exception as e:
        logger.exception(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")
