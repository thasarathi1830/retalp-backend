from fastapi import APIRouter, HTTPException
from state import data_store
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse


router = APIRouter()

@router.get("/{file_id}")
async def download_cleaned_data(file_id: str):
    if file_id not in data_store:
        raise HTTPException(404, "File not found")
    
    df = data_store[file_id]["current_df"]
    output = BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Cleaned Data')
        
        metadata = pd.DataFrame({
            'Property': ['Original Filename', 'Processing Date', 'Actions Performed'],
            'Value': [
                data_store[file_id]['filename'],
                pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                '; '.join(data_store[file_id]['actions'])
            ]
        })
        metadata.to_excel(writer, index=False, sheet_name='Metadata')
    
    output.seek(0)
    filename = f"cleaned_{data_store[file_id]['filename']}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
