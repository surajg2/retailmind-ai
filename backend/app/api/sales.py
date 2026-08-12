from pathlib import Path
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Query, status
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import Business, Sales, User
from backend.app.schemas.schemas import CSVImportResult, SalesOut, SyntheticGenResult
from backend.app.services.csv_importer import validate_and_import_sales_csv
from data.generate_synthetic_data import generate_dataset

router = APIRouter()

@router.post("/upload-csv", response_model=CSVImportResult, status_code=status.HTTP_200_OK)
async def upload_sales_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Atomic CSV Upload Endpoint:
    - Validates entire file before inserting any records.
    - If ANY validation error exists, returns row-level error list and inserts ZERO records.
    """
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user is not linked to a registered business store."
        )

    if not file.filename.endswith(".csv") and file.content_type != "text/csv":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file must be a valid CSV format (.csv)."
        )

    content_bytes = await file.read()
    try:
        content_str = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("latin-1")

    result = validate_and_import_sales_csv(
        db=db,
        business_id=current_user.business_id,
        file_content=content_str
    )
    return result


@router.post("/generate-synthetic", response_model=SyntheticGenResult, status_code=status.HTTP_201_CREATED)
def generate_and_ingest_synthetic_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Synthetic Data Generation & Ingestion Endpoint:
    - Generates 7,300 daily sales records (20 products x 365 days) with realistic dynamics.
    - Auto-ingests dataset into PostgreSQL for the current business.
    """
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user is not linked to a registered business store."
        )

    synthetic_file = Path(__file__).resolve().parent.parent.parent.parent / "data" / "synthetic_sales_data.csv"
    
    # Generate CSV if not existing or regenerate fresh
    num_generated = generate_dataset(synthetic_file, days=365)

    # Read and import CSV into database
    with open(synthetic_file, "r", encoding="utf-8") as f:
        file_content = f.read()

    result = validate_and_import_sales_csv(
        db=db,
        business_id=current_user.business_id,
        file_content=file_content
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Synthetic data ingestion failed: {result.message}"
        )

    return SyntheticGenResult(
        success=True,
        records_generated=num_generated,
        imported_count=result.successful_imports,
        message=f"Successfully generated and imported {result.successful_imports} synthetic daily sales records."
    )


@router.get("", response_model=List[SalesOut])
def list_sales(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sku: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Paginated Sales Listing Endpoint
    """
    if not current_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authenticated user is not linked to a business store."
        )

    query = db.query(Sales).options(joinedload(Sales.product)).filter(
        Sales.business_id == current_user.business_id
    )

    if sku:
        query = query.join(Sales.product).filter(Product.sku == sku.upper())

    sales = query.order_by(Sales.sale_date.desc(), Sales.id.desc()).offset(offset).limit(limit).all()
    return sales
