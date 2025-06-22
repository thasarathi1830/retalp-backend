from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from io import BytesIO
import chardet
import uuid
import logging

# If you use a global data store (like a dict), import or define it:
try:
    from state import data_store
except ImportError:
    data_store = {}

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV or Excel file, auto-detect encoding, store in global data_store, and return file metadata.
    """
    try:
        contents = await file.read()

        # Detect encoding for text files
        if file.filename.lower().endswith(('.csv', '.txt')):
            encoding = chardet.detect(contents)['encoding'] or 'utf-8'
            try:
                decoded = contents.decode(encoding)
            except Exception:
                decoded = contents.decode('utf-8', errors='replace')
            file_like = BytesIO(decoded.encode('utf-8'))
            df = pd.read_csv(file_like)
        elif file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a CSV or Excel file.")

        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Store DataFrame and metadata in global data_store
        data_store[file_id] = {
            "original_df": df,
            "current_df": df.copy(),
            "actions": []
        }

        # Prepare response metadata
        response = {
            "file_id": file_id,
            "filename": file.filename,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head(10).to_dict(orient="records"),
            "shape": list(df.shape)
        }
        return response

    except pd.errors.ParserError as e:
        logger.exception("Pandas parser error")
        raise HTTPException(status_code=400, detail=f"File parsing error: {str(e)}")
    except Exception as e:
        logger.exception("File upload error")
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")
