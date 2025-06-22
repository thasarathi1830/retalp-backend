from fastapi import APIRouter, UploadFile, File
from state import data_store
import pandas as pd
import uuid
import io
import logging
import chardet

router = APIRouter()
logger = logging.getLogger(__name__)

def detect_encoding(contents):
    result = chardet.detect(contents)
    return result['encoding'] if result['confidence'] > 0.7 else 'utf-8'

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read file content
        contents = await file.read()
        logger.info(f"Processing file: {file.filename}, size: {len(contents)} bytes")
        
        # Process based on file type
        if file.filename.endswith('.csv'):
            # Try multiple encodings for CSV
            for encoding in ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']:
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding=encoding)
                    logger.info(f"Successfully read CSV with {encoding} encoding")
                    break
                except Exception as e:
                    logger.warning(f"Failed to read with {encoding}: {str(e)}")
            else:
                # Final fallback with error ignore
                df = pd.read_csv(io.BytesIO(contents), encoding='utf-8', errors='ignore')
                logger.warning("Using UTF-8 with errors='ignore' as fallback")
                
        elif file.filename.endswith(('.xlsx', '.xls')):
            # Handle Excel files
            try:
                df = pd.read_excel(io.BytesIO(contents))
                logger.info(f"Successfully read Excel file: {file.filename}")
            except Exception as e:
                logger.error(f"Excel read error: {str(e)}")
                raise ValueError(f"Could not read Excel file: {str(e)}")
        else:
            raise ValueError("Unsupported file format. Only CSV and Excel files are supported.")
        
        # Validate dataframe
        if df.empty:
            raise ValueError("The uploaded file is empty")
        
        if len(df.columns) == 0:
            raise ValueError("No columns found in the file")
        
        # Generate file ID
        file_id = str(uuid.uuid4())
        logger.info(f"Generated file_id: {file_id}")
        
        # Store in data_store
        data_store[file_id] = {
            "filename": file.filename,
            "original_df": df.copy(),
            "current_df": df.copy(),
            "actions": [f"Uploaded: {file.filename}"]
        }
        
        # Return success response
        return {
            "status": "success",
            "file_id": file_id,
            "filename": file.filename,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "head": df.head().to_dict(orient="records"),
            "shape": list(df.shape)
        }
        
    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": f"File processing error: {str(e)}"
        }
