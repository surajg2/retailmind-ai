from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.models import Product, User
from backend.app.schemas.schemas import ProductCreate, ProductOut, ProductUpdate

router = APIRouter()

@router.get("", response_model=List[ProductOut])
def list_products(
    include_inactive: bool = Query(False, description="Include soft-deactivated products"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    search: Optional[str] = Query(None, description="Search by SKU or Product Name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    List products for authenticated user's business. Strictly tenant-scoped.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    query = db.query(Product).filter(Product.business_id == current_user.business_id)

    if not include_inactive:
        query = query.filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))

    if search:
        search_term = f"%{search.strip()}%"
        query = query.filter(or_(Product.sku.ilike(search_term), Product.name.ilike(search_term)))

    products = query.order_by(Product.name).offset(offset).limit(limit).all()
    return products


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Manually create a new product for the authenticated user's business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    sku_upper = product_in.sku.strip().upper()
    existing = db.query(Product).filter(
        Product.business_id == current_user.business_id,
        Product.sku == sku_upper
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{sku_upper}' already exists in your store catalog."
        )

    product = Product(
        business_id=current_user.business_id,
        sku=sku_upper,
        name=product_in.name.strip(),
        category=product_in.category.strip() if product_in.category else "General",
        unit=product_in.unit or "pcs",
        cost_price=product_in.cost_price,
        selling_price=product_in.selling_price,
        min_stock_level=product_in.min_stock_level,
        is_active=True
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Retrieve single product details. Returns 404 if product does not exist or belongs to another business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in your store catalog."
        )
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Update product profile. Returns 404 if product belongs to another business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in your store catalog."
        )

    if product_in.name is not None:
        product.name = product_in.name.strip()
    if product_in.category is not None:
        product.category = product_in.category.strip()
    if product_in.unit is not None:
        product.unit = product_in.unit.strip()
    if product_in.cost_price is not None:
        product.cost_price = product_in.cost_price
    if product_in.selling_price is not None:
        product.selling_price = product_in.selling_price
    if product_in.min_stock_level is not None:
        product.min_stock_level = product_in.min_stock_level
    if product_in.is_active is not None:
        product.is_active = product_in.is_active

    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def deactivate_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Any:
    """
    Soft-deactivate product (is_active = False). Preserves all historical sales records.
    Returns 404 if product belongs to another business.
    """
    if not current_user.business_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User not linked to a business.")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == current_user.business_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product ID {product_id} not found in your store catalog."
        )

    product.is_active = False
    db.commit()

    return {
        "success": True,
        "product_id": product_id,
        "is_active": False,
        "message": f"Product '{product.name}' (SKU: {product.sku}) soft-deactivated successfully. Historical sales preserved."
    }
