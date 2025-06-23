from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# Import routers
from routers.file_upload import router as upload_router
from routers.overview import router as overview_router
from routers.cleaning import router as cleaning_router
from routers.outliers import router as outliers_router
from routers.visualization_routers import router as visualization_router
from routers.download import router as download_router
from routers.report import router as report_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app instance
app = FastAPI(
    title="EDA Dashboard API",
    description="Backend API for an Exploratory Data Analysis (EDA) Dashboard using FastAPI",
    version="1.0.0",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://my-eda-frontend.vercel.app",
        "https://my-eda-frontend-n5spl07dl-thasarathis-projects.vercel.app",
        "https://my-eda-frontend-6dnubtm9f-thasarrathis-projects.vercel.app"  # <--- ADD THIS
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(overview_router, prefix="/api/overview", tags=["Overview"])
app.include_router(cleaning_router, prefix="/api/cleaning", tags=["Cleaning"])
app.include_router(outliers_router, prefix="/api/outliers", tags=["Outliers"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["Visualization"])
app.include_router(download_router, prefix="/api/download", tags=["Download"])
app.include_router(report_router, prefix="/api/report", tags=["Report"])

# Root endpoint
@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the EDA Dashboard API"}

# Health check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": app.version}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
