from fastapi import APIRouter, UploadFile, File, HTTPException
import pandas as pd
from io import BytesIO
import chardet
import uuid

# Import data store
try:
    from state import data_store
except ImportError:
    data_store = {}

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if file.filename.lower().endswith(('.csv', '.txt')):
            encoding = chardet.detect(contents)['encoding'] or 'utf-8'
            try:
                file_content = contents.decode(encoding)
            except Exception:
                file_content = contents.decode('utf-8', errors='replace')
            file_like = BytesIO(file_content.encode('utf-8'))
        else:
            file_like = BytesIO(contents)

        # Read into DataFrame
        if file.filename.lower().endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file_like)
        elif file.filename.lower().endswith(('.csv', '.txt')):
            df = pd.read_csv(file_like)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Supported: CSV, Excel")

        # Generate file ID and store
        file_id = str(uuid.uuid4())
        data_store[file_id] = {
            "original_df": df,
            "current_df": df.copy(),
            "filename": file.filename,  # ✅ Add filename here
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
        raise HTTPException(status_code=500, detail=f"File processing error: {str(e)}")
