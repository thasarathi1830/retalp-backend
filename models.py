from pydantic import BaseModel
from typing import List, Optional, Dict

class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    columns: List[str]
    dtypes: Dict[str, str]
    shape: List[int]
    null_counts: Dict[str, int]

class RemoveColumnsRequest(BaseModel):
    file_id: str
    columns: List[str]

class FillMissingRequest(BaseModel):
    file_id: str
    column: str
    method: str
    custom_value: Optional[str] = None

class OutlierDetectRequest(BaseModel):
    file_id: str
    column: str
    method: str

class OutlierHandleRequest(BaseModel):
    file_id: str
    action: str
    column: str
    outlier_indices: List[int]

class VisualizationRequest(BaseModel):
    file_id: str
    chart_type: str
    x_col: str
    y_col: Optional[str] = None
    hue_col: Optional[str] = None
