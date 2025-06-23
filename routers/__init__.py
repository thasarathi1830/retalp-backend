from .file_upload import router as upload_router
from .overview import router as overview_router
from .cleaning import router as cleaning_router
from .outliers import router as outliers_router
from .visualization_routers import router as visualization_router
from .download import router as download_router
from .report import router as report_router

__all__ = [
    "upload_router",
    "overview_router",
    "cleaning_router",
    "outliers_router",
    "visualization_router",
    "download_router",
    "report_router"
]
