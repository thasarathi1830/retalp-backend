import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import pandas as pd
import numpy as np
import logging
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from state import data_store

router = APIRouter()
logger = logging.getLogger(__name__)

class VisualizationRequest(BaseModel):
    file_id: str
    chart_type: str
    x_col: str
    y_col: str = None
    hue_col: str = None

@router.post("/generate")
async def generate_chart(request: VisualizationRequest):
    try:
        # Validate file_id exists
        if request.file_id not in data_store:
            raise HTTPException(
                status_code=404,
                detail="File not found or failed to generate chart"
            )
        file_data = data_store[request.file_id]
        current_df = file_data["current_df"]

        # Ensure current_df is a DataFrame
        if isinstance(current_df, dict):
            current_df = pd.DataFrame(current_df)
            data_store[request.file_id]["current_df"] = current_df

        # Validate columns
        if request.x_col not in current_df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.x_col}' not found")
        if request.y_col and request.y_col not in current_df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.y_col}' not found")
        if request.hue_col and request.hue_col not in current_df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{request.hue_col}' not found")

        # Plot
        plt.figure(figsize=(10, 6))
        if request.chart_type == 'bar':
            sns.barplot(data=current_df, x=request.x_col, y=request.y_col, hue=request.hue_col)
        elif request.chart_type == 'line':
            sns.lineplot(data=current_df, x=request.x_col, y=request.y_col, hue=request.hue_col)
        elif request.chart_type == 'scatter':
            sns.scatterplot(data=current_df, x=request.x_col, y=request.y_col, hue=request.hue_col)
        elif request.chart_type == 'histogram':
            sns.histplot(data=current_df, x=request.x_col, hue=request.hue_col, kde=True)
        elif request.chart_type == 'box':
            sns.boxplot(data=current_df, x=request.x_col, y=request.y_col, hue=request.hue_col)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported chart type: {request.chart_type}")

        buf = BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=100)
        plt.close()
        buf.seek(0)
        return Response(content=buf.read(), media_type="image/png")

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Visualization error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chart generation failed: {str(e)}")
