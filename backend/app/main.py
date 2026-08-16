from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.health import router as health_router
from backend.app.api.auth import router as auth_router
from backend.app.api.sales import router as sales_router
from backend.app.api.products import router as products_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.forecasts import router as forecasts_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set CORS middleware
origins = settings.CORS_ORIGINS
if isinstance(origins, str):
    origins = [origins]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root level health endpoint
app.include_router(health_router, tags=["Health"])

# API v1 endpoints
app.include_router(health_router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(sales_router, prefix=f"{settings.API_V1_STR}/sales", tags=["Sales"])
app.include_router(sales_router, prefix="/sales", tags=["Sales"])
app.include_router(products_router, prefix=f"{settings.API_V1_STR}/products", tags=["Products"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(analytics_router, prefix=f"{settings.API_V1_STR}/analytics", tags=["Analytics"])
app.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
app.include_router(forecasts_router, prefix=f"{settings.API_V1_STR}/forecasts", tags=["Forecasts"])
app.include_router(forecasts_router, prefix="/forecasts", tags=["Forecasts"])

@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": "/docs",
        "health": "/health"
    }
