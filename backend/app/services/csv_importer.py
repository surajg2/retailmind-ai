import csv
import io
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import List, Dict, Tuple, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.models.models import Product, Sales, Inventory
from backend.app.schemas.schemas import CSVRowError, CSVImportResult

EXPECTED_HEADERS = {
    "date", "sku", "product_name", "category",
    "units_sold", "selling_price", "promotion", "holiday", "festival", "stock_available"
}

def parse_boolean(val: Any) -> Optional[bool]:
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    if s in ("1", "true", "yes", "t", "y"):
        return True
    if s in ("0", "false", "no", "f", "n"):
        return False
    return None

def normalize_festival(val: Optional[str]) -> Optional[str]:
    if not val:
        return None
    s = str(val).strip()
    if s.lower() in ("", "none", "null", "n/a", "nan"):
        return None
    return s

def validate_and_import_sales_csv(
    db: Session,
    business_id: int,
    file_content: str
) -> CSVImportResult:
    """
    Two-Phase Atomic CSV Validator & Importer:
    - Phase 1: Reads file (stripping # comments), validates row-by-row for date formats,
      numeric bounds, monetary values, duplicate records, and SKU metadata conflicts.
    - Phase 2: If 100% valid, commits all records atomically in a single DB transaction.
      If ANY error exists, inserts ZERO rows and returns all row-level errors.
    """
    errors: List[CSVRowError] = []
    
    # Pre-parse lines to ignore # comment headers
    raw_lines = file_content.splitlines()
    clean_lines = [line for line in raw_lines if line.strip() and not line.strip().startswith('#')]
    
    if not clean_lines:
        return CSVImportResult(
            success=False,
            total_rows_processed=0,
            successful_imports=0,
            errors=[CSVRowError(row_number=0, error="CSV file is empty or contains only comment header lines.")],
            message="Import failed: empty file."
        )

    csv_reader = csv.DictReader(clean_lines)
    if not csv_reader.fieldnames:
        return CSVImportResult(
            success=False,
            total_rows_processed=0,
            successful_imports=0,
            errors=[CSVRowError(row_number=0, error="CSV file missing headers.")],
            message="Import failed: missing headers."
        )

    # Normalize headers
    fieldnames_set = {fn.strip().lower() for fn in csv_reader.fieldnames if fn}
    missing_headers = EXPECTED_HEADERS - fieldnames_set
    if missing_headers:
        return CSVImportResult(
            success=False,
            total_rows_processed=0,
            successful_imports=0,
            errors=[CSVRowError(row_number=0, error=f"Missing required CSV columns: {', '.join(sorted(missing_headers))}")],
            message="Import failed: invalid column headers."
        )

    # Load existing products for this business into memory for fast lookup & conflict detection
    existing_products: Dict[str, Product] = {
        p.sku.upper(): p
        for p in db.query(Product).filter(Product.business_id == business_id).all()
    }

    # Load existing (product_id, sale_date) sales records for duplicate detection
    existing_sales_keys: set = {
        (s.product_id, s.sale_date)
        for s in db.query(Sales.product_id, Sales.sale_date).filter(Sales.business_id == business_id).all()
    }

    parsed_rows: List[Dict[str, Any]] = []
    file_seen_keys: set = set() # For checking duplicate records within the CSV file
    file_sku_metadata: Dict[str, Tuple[str, str]] = {} # SKU -> (name, category) in CSV file

    row_count = 0
    # Phase 1: Full Validation
    for idx, row in enumerate(csv_reader, start=2): # Line 1 is header
        row_count += 1
        
        # Clean row dictionary keys
        row_clean = {k.strip().lower(): (v.strip() if v else "") for k, v in row.items() if k}
        
        sku = row_clean.get("sku", "").upper()
        p_name = row_clean.get("product_name", "")
        cat = row_clean.get("category", "")
        raw_date = row_clean.get("date", "")
        raw_units = row_clean.get("units_sold", "")
        raw_price = row_clean.get("selling_price", "")
        raw_promo = row_clean.get("promotion", "0")
        raw_holiday = row_clean.get("holiday", "0")
        raw_fest = row_clean.get("festival", "")
        raw_stock = row_clean.get("stock_available", "0")

        # 1. Validate SKU
        if not sku:
            errors.append(CSVRowError(row_number=idx, column="sku", error="SKU cannot be empty."))
            continue

        # 2. Validate Product Name
        if not p_name:
            errors.append(CSVRowError(row_number=idx, column="product_name", error="Product name cannot be empty."))
            continue

        # 3. Check SKU Metadata Conflicts against existing DB product
        if sku in existing_products:
            existing_p = existing_products[sku]
            if existing_p.name.lower() != p_name.lower():
                errors.append(CSVRowError(
                    row_number=idx, column="product_name",
                    error=f"SKU metadata conflict for '{sku}': existing product name '{existing_p.name}' vs CSV '{p_name}'."
                ))
                continue
            if cat and existing_p.category and existing_p.category.lower() != cat.lower():
                errors.append(CSVRowError(
                    row_number=idx, column="category",
                    error=f"SKU metadata conflict for '{sku}': existing category '{existing_p.category}' vs CSV '{cat}'."
                ))
                continue

        # 4. Check SKU Metadata Consistency within the CSV file
        if sku in file_sku_metadata:
            prev_name, prev_cat = file_sku_metadata[sku]
            if prev_name.lower() != p_name.lower():
                errors.append(CSVRowError(
                    row_number=idx, column="product_name",
                    error=f"Conflicting product name for SKU '{sku}' within CSV: '{prev_name}' vs '{p_name}'."
                ))
                continue
        else:
            file_sku_metadata[sku] = (p_name, cat)

        # 5. Validate Sale Date (YYYY-MM-DD)
        sale_date_val: Optional[date] = None
        try:
            sale_date_val = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError:
            errors.append(CSVRowError(
                row_number=idx, column="date",
                error=f"Invalid date format '{raw_date}'. Expected format YYYY-MM-DD."
            ))
            continue

        # 6. Validate Units Sold (non-negative integer)
        try:
            units_sold_val = int(raw_units)
            if units_sold_val < 0:
                errors.append(CSVRowError(
                    row_number=idx, column="units_sold",
                    error=f"Units sold cannot be negative: '{raw_units}'."
                ))
                continue
        except ValueError:
            errors.append(CSVRowError(
                row_number=idx, column="units_sold",
                error=f"Invalid units_sold value '{raw_units}'. Must be an integer."
            ))
            continue

        # 7. Validate Selling Price (positive Decimal / Numeric(10,2))
        try:
            selling_price_val = Decimal(raw_price)
            if selling_price_val <= Decimal("0.00"):
                errors.append(CSVRowError(
                    row_number=idx, column="selling_price",
                    error=f"Invalid monetary value '{raw_price}'. Selling price must be greater than 0.00."
                ))
                continue
        except (InvalidOperation, TypeError):
            errors.append(CSVRowError(
                row_number=idx, column="selling_price",
                error=f"Invalid monetary value '{raw_price}'. Must be a valid numeric price."
            ))
            continue

        # 8. Validate Stock Available (non-negative integer)
        try:
            stock_avail_val = int(raw_stock)
            if stock_avail_val < 0:
                errors.append(CSVRowError(
                    row_number=idx, column="stock_available",
                    error=f"Stock available cannot be negative: '{raw_stock}'."
                ))
                continue
        except ValueError:
            errors.append(CSVRowError(
                row_number=idx, column="stock_available",
                error=f"Invalid stock_available value '{raw_stock}'. Must be an integer."
            ))
            continue

        # 9. Validate Promotion & Holiday booleans
        promo_val = parse_boolean(raw_promo)
        if promo_val is None:
            errors.append(CSVRowError(row_number=idx, column="promotion", error=f"Invalid promotion boolean value '{raw_promo}'."))
            continue

        holiday_val = parse_boolean(raw_holiday)
        if holiday_val is None:
            errors.append(CSVRowError(row_number=idx, column="holiday", error=f"Invalid holiday boolean value '{raw_holiday}'."))
            continue

        # 10. Check Intra-CSV Duplicates
        csv_key = (sku, sale_date_val)
        if csv_key in file_seen_keys:
            errors.append(CSVRowError(
                row_number=idx, column="date",
                error=f"Duplicate record in CSV for SKU '{sku}' on date '{sale_date_val}'."
            ))
            continue
        file_seen_keys.add(csv_key)

        # 11. Check Database Duplicates (business_id + product_id + sale_date)
        if sku in existing_products:
            p_id = existing_products[sku].id
            if (p_id, sale_date_val) in existing_sales_keys:
                errors.append(CSVRowError(
                    row_number=idx, column="date",
                    error=f"Sales record already exists for SKU '{sku}' on {sale_date_val}."
                ))
                continue

        # Normalize Festival (None if empty / "None" / "NULL")
        fest_val = normalize_festival(raw_fest)

        parsed_rows.append({
            "row_number": idx,
            "sku": sku,
            "product_name": p_name,
            "category": cat,
            "sale_date": sale_date_val,
            "units_sold": units_sold_val,
            "selling_price": selling_price_val,
            "promotion": promo_val,
            "holiday": holiday_val,
            "festival": fest_val,
            "stock_available": stock_avail_val,
        })

    # ATOMICITY GUARANTEE: If ANY validation errors exist, ZERO rows are written.
    if errors:
        return CSVImportResult(
            success=False,
            total_rows_processed=row_count,
            successful_imports=0,
            errors=errors,
            message=f"Import failed with {len(errors)} validation errors. Zero rows were inserted into the database."
        )

    # Phase 2: Atomic Execution
    try:
        inserted_count = 0
        new_products_cache: Dict[str, Product] = dict(existing_products)
        existing_inventory_cache: Dict[int, Inventory] = {
            inv.product_id: inv
            for inv in db.query(Inventory).filter(Inventory.business_id == business_id).all()
        }

        for data in parsed_rows:
            sku = data["sku"]
            
            # Lookup or create Product
            if sku in new_products_cache:
                product = new_products_cache[sku]
            else:
                product = Product(
                    business_id=business_id,
                    sku=sku,
                    name=data["product_name"],
                    category=data["category"],
                    unit="pcs",
                    cost_price=data["selling_price"] * Decimal("0.70"), # Estimated default cost
                    selling_price=data["selling_price"],
                    min_stock_level=10
                )
                db.add(product)
                db.flush() # Obtain product.id
                new_products_cache[sku] = product

            # Calculate total_amount = units_sold * selling_price
            total_amt = Decimal(data["units_sold"]) * data["selling_price"]

            # Create Sales Record
            sales_record = Sales(
                business_id=business_id,
                product_id=product.id,
                quantity=data["units_sold"],
                selling_price=data["selling_price"],
                total_amount=total_amt,
                promotion=data["promotion"],
                holiday=data["holiday"],
                festival=data["festival"],
                stock_available=data["stock_available"],
                is_stockout=None, # Historical CSV imports leave is_stockout as Nullable None unless verified
                sale_date=data["sale_date"]
            )
            db.add(sales_record)

            # Update or create Inventory current_stock via cache
            if product.id in existing_inventory_cache:
                existing_inventory_cache[product.id].current_stock = data["stock_available"]
            else:
                inv_item = Inventory(
                    business_id=business_id,
                    product_id=product.id,
                    current_stock=data["stock_available"],
                    reorder_point=15
                )
                db.add(inv_item)
                existing_inventory_cache[product.id] = inv_item

            inserted_count += 1

        db.commit() # Atomic commit

        return CSVImportResult(
            success=True,
            total_rows_processed=row_count,
            successful_imports=inserted_count,
            errors=[],
            message=f"Successfully imported {inserted_count} sales records into PostgreSQL database."
        )

    except Exception as e:
        db.rollback()
        return CSVImportResult(
            success=False,
            total_rows_processed=row_count,
            successful_imports=0,
            errors=[CSVRowError(row_number=0, error=f"Database execution error: {str(e)}")],
            message="Import failed due to a database error. Transaction was rolled back."
        )
