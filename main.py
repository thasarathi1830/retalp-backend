from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from routers.upload import router as upload_router
from routers.overview import router as overview_router
from routers.cleaning import router as cleaning_router
from routers.outliers import router as outliers_router
from routers.visualization_routers import router as visualization_router
from routers.download import router as download_router
from routers.report import router as report_router

app = FastAPI(
    title="EDA Dashboard API",
    description="Backend API for an Exploratory Data Analysis (EDA) Dashboard using FastAPI",
    version="1.0.0"
)

# CORS configuration - critical fix
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Local development
        "https://my-eda-frontend-r9ws8b9y4-thasarrathis-projects.vercel.app",  # Your Vercel frontend
        "https://my-eda-frontend.vercel.app"  # Your main Vercel domain
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include all routers with /api prefix
app.include_router(upload_router, prefix="/api/upload", tags=["Upload"])
app.include_router(overview_router, prefix="/api/overview", tags=["Overview"])
app.include_router(cleaning_router, prefix="/api/cleaning", tags=["Cleaning"])
app.include_router(outliers_router, prefix="/api/outliers", tags=["Outliers"])
app.include_router(visualization_router, prefix="/api/visualization", tags=["Visualization"])
app.include_router(download_router, prefix="/api/download", tags=["Download"])
app.include_router(report_router, prefix="/api/report", tags=["Report"])

@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to the EDA Dashboard API"}
