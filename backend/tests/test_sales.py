from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Tuple
from fastapi import status
from sqlalchemy.orm import Session

from backend.app.models.models import Business, Product, Sales, User
from backend.app.services.csv_importer import validate_and_import_sales_csv
from data.generate_synthetic_data import generate_dataset

def create_test_user_and_business(client, db, email_prefix: str = "sales") -> Tuple[User, str]:
    import random
    rand_id = random.randint(1000, 9999)
    email = f"{email_prefix}_{rand_id}_{date.today()}@example.com"
    pwd = "TestPassword123!"
    
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": "Sales Tester",
        "business_name": f"Test Store {rand_id}",
        "business_type": "Supermarket"
    })
    assert reg_resp.status_code == status.HTTP_201_CREATED
    
    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login_resp.json()["access_token"]
    
    user = db.query(User).filter(User.email == email).first()
    return user, token

def test_null_festival_normalization_and_normalized_relationships(client, db):
    user, token = create_test_user_and_business(client, db, "norm")
    
    valid_csv = """# RETAILMIND AI - SYNTHETIC DATASET
date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-01-01,SKU-NORM-001,Test Product 1,Grains,10,100.50,0,0,None,50
2025-01-02,SKU-NORM-001,Test Product 1,Grains,15,100.50,1,0,,40
2025-01-01,SKU-NORM-002,Test Product 2,Beverages,5,50.00,0,1,Diwali,20
"""

    result = validate_and_import_sales_csv(db, user.business_id, valid_csv)
    assert result.success is True
    assert result.successful_imports == 3
    assert len(result.errors) == 0

    # Verify Product created
    p1 = db.query(Product).filter(Product.business_id == user.business_id, Product.sku == "SKU-NORM-001").first()
    assert p1 is not None
    assert p1.name == "Test Product 1"
    assert p1.category == "Grains"
    assert p1.selling_price == Decimal("100.50")

    # Verify Sales Records & Festival NULL Normalization
    sales_list = db.query(Sales).filter(Sales.business_id == user.business_id, Sales.product_id == p1.id).order_by(Sales.sale_date).all()
    assert len(sales_list) == 2
    assert sales_list[0].festival is None # "None" normalized to None
    assert sales_list[1].festival is None # "" normalized to None
    assert sales_list[0].selling_price == Decimal("100.50")
    assert sales_list[0].total_amount == Decimal("1005.00") # 10 * 100.50

    p2_sales = db.query(Sales).filter(Sales.business_id == user.business_id).join(Product).filter(Product.sku == "SKU-NORM-002").first()
    assert p2_sales.festival == "Diwali"

def test_stockout_semantics(client, db):
    user, token = create_test_user_and_business(client, db, "stk")
    
    csv_data = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-02-01,SKU-STK-001,Stockout Product,Snacks,5,20.00,0,0,,0
"""
    result = validate_and_import_sales_csv(db, user.business_id, csv_data)
    assert result.success is True
    
    sales_rec = db.query(Sales).filter(Sales.business_id == user.business_id).join(Product).filter(Product.sku == "SKU-STK-001").first()
    assert sales_rec.stock_available == 0
    assert sales_rec.is_stockout is None # CSV imports leave is_stockout as Nullable None

def test_invalid_monetary_values(client, db):
    user, token = create_test_user_and_business(client, db, "money")
    
    invalid_price_csv = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-03-01,SKU-MONEY-001,Bad Price Item,Snacks,10,invalid_price_str,0,0,,15
2025-03-02,SKU-MONEY-001,Bad Price Item,Snacks,10,-25.00,0,0,,15
"""
    result = validate_and_import_sales_csv(db, user.business_id, invalid_price_csv)
    assert result.success is False
    assert result.successful_imports == 0
    assert len(result.errors) == 2
    assert any("Invalid monetary value" in e.error for e in result.errors)

def test_sku_metadata_conflict(client, db):
    user, token = create_test_user_and_business(client, db, "conf")
    
    # 1. Create initial product
    init_csv = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-04-01,SKU-CONF-001,Original Name,Original Category,10,10.00,0,0,,50
"""
    res1 = validate_and_import_sales_csv(db, user.business_id, init_csv)
    assert res1.success is True

    # 2. Upload CSV with SAME SKU but DIFFERENT product_name
    conflict_csv = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-04-02,SKU-CONF-001,Conflicting Name,Original Category,5,10.00,0,0,,45
"""
    res2 = validate_and_import_sales_csv(db, user.business_id, conflict_csv)
    assert res2.success is False
    assert res2.successful_imports == 0
    assert len(res2.errors) == 1
    assert "SKU metadata conflict" in res2.errors[0].error

def test_duplicate_csv_upload_and_partial_import_prevention(client, db):
    user, token = create_test_user_and_business(client, db, "dup")
    
    csv_data = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-05-01,SKU-DUP-001,Item DUP,Snacks,10,15.00,0,0,,50
2025-05-02,SKU-DUP-001,Item DUP,Snacks,12,15.00,0,0,,40
"""
    # First Import -> Success
    res1 = validate_and_import_sales_csv(db, user.business_id, csv_data)
    assert res1.success is True
    assert res1.successful_imports == 2

    # Re-upload exact same CSV -> Rejection due to duplicates, ZERO rows inserted
    res2 = validate_and_import_sales_csv(db, user.business_id, csv_data)
    assert res2.success is False
    assert res2.successful_imports == 0
    assert len(res2.errors) >= 1
    assert "Sales record already exists" in res2.errors[0].error

def test_failed_mixed_validity_csv_inserts_zero_rows(client, db):
    user, token = create_test_user_and_business(client, db, "mixed")
    
    # CSV containing 4 valid rows and 1 invalid row (negative units_sold at row 4)
    mixed_csv = """date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available
2025-06-01,SKU-MIX-001,Good Item 1,Snacks,10,15.00,0,0,,50
2025-06-02,SKU-MIX-001,Good Item 1,Snacks,12,15.00,0,0,,40
2025-06-01,SKU-MIX-002,Good Item 2,Grains,5,100.00,0,0,,20
2025-06-02,SKU-MIX-002,Good Item 2,Grains,-5,100.00,0,0,,15
2025-06-03,SKU-MIX-002,Good Item 2,Grains,8,100.00,0,0,,10
"""
    result = validate_and_import_sales_csv(db, user.business_id, mixed_csv)
    assert result.success is False
    assert result.successful_imports == 0
    assert len(result.errors) == 1
    assert result.errors[0].row_number == 5 # Row 5 in CSV (1-indexed header + data)
    
    # Confirm ZERO records written to database for this business
    sales_count = db.query(Sales).filter(Sales.business_id == user.business_id).count()
    assert sales_count == 0

def test_synthetic_dataset_generation_7300_records(tmp_path):
    output_csv = tmp_path / "test_synthetic.csv"
    count = generate_dataset(output_csv, days=365)
    
    assert count == 7300
    assert output_csv.exists()
    
    with open(output_csv, "r", encoding="utf-8") as f:
        first_line = f.readline().strip()
        assert first_line == "# RETAILMIND AI - SYNTHETIC DATASET"
        
        second_line = f.readline().strip()
        assert second_line == "date,sku,product_name,category,units_sold,selling_price,promotion,holiday,festival,stock_available"
        
        lines = f.readlines()
        assert len(lines) == 7300

def test_api_upload_and_generate_endpoints_and_tenant_isolation(client, db):
    user1, token1 = create_test_user_and_business(client, db, "user1")
    user2, token2 = create_test_user_and_business(client, db, "user2")
    
    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # User 1 imports synthetic data
    gen_resp1 = client.post("/api/v1/sales/generate-synthetic", headers=headers1)
    assert gen_resp1.status_code == status.HTTP_201_CREATED
    assert gen_resp1.json()["imported_count"] == 7300

    # User 1 queries sales -> Returns User 1 sales
    list_resp1 = client.get("/api/v1/sales?limit=10", headers=headers1)
    assert list_resp1.status_code == status.HTTP_200_OK
    sales1 = list_resp1.json()
    assert len(sales1) == 10
    assert sales1[0]["business_id"] == user1.business_id

    # User 2 queries sales -> Returns EMPTY list (Tenant Isolation verified)
    list_resp2 = client.get("/api/v1/sales?limit=10", headers=headers2)
    assert list_resp2.status_code == status.HTTP_200_OK
    sales2 = list_resp2.json()
    assert len(sales2) == 0 # User 2 cannot see User 1's sales data!
