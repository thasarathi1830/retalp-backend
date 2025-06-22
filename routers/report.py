from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from state import data_store
from services.report import generate_eda_report
import os
import logging
import uuid

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate/{file_id}")  # Changed endpoint path
async def generate_report(file_id: str, action_history: list):
    if file_id not in data_store:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        # Generate unique report name
        report_name = f"report_{uuid.uuid4().hex}.pdf"
        report_path = generate_eda_report(data_store, file_id, action_history, report_name)
        
        if not os.path.exists(report_path):
            raise HTTPException(status_code=500, detail="Report generation failed")
        
        return FileResponse(
            report_path,
            media_type="application/pdf",
            filename=report_name
        )
    except Exception as e:
        logger.error(f"Report generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
