import csv
import math
import random
from datetime import date, timedelta
from pathlib import Path

# Header Comment required for explicit labeling
HEADER_COMMENT = "# RETAILMIND AI - SYNTHETIC DATASET"

PRODUCTS = [
    # 5 Fast-Moving FMCG / Staple Products
    {"sku": "SKU-GROC-001", "name": "Aashirvaad Whole Wheat Atta 5kg", "category": "Atta & Flours", "price": 245.00, "velocity": "fast", "base_demand": 40},
    {"sku": "SKU-GROC-002", "name": "Amul Taaza Toned Milk 1L", "category": "Dairy & Eggs", "price": 54.00, "velocity": "fast", "base_demand": 55},
    {"sku": "SKU-GROC-003", "name": "Fortune Sunlite Sunflower Oil 1L", "category": "Edible Oils", "price": 140.00, "velocity": "fast", "base_demand": 35},
    {"sku": "SKU-GROC-004", "name": "Tata Salt Iodized 1kg", "category": "Salt & Sugar", "price": 28.00, "velocity": "fast", "base_demand": 45},
    {"sku": "SKU-GROC-005", "name": "Maggi 2-Minute Masala Noodles 280g", "category": "Instant Food", "price": 48.00, "velocity": "fast", "base_demand": 50},

    # 5 Steady Household Staples
    {"sku": "SKU-GROC-006", "name": "Surf Excel Easy Wash Detergent 1kg", "category": "Laundry & Care", "price": 145.00, "velocity": "steady", "base_demand": 20},
    {"sku": "SKU-GROC-007", "name": "Colgate Strong Teeth Toothpaste 200g", "category": "Personal Care", "price": 98.00, "velocity": "steady", "base_demand": 18},
    {"sku": "SKU-GROC-008", "name": "Red Label Tea 500g", "category": "Beverages", "price": 260.00, "velocity": "steady", "base_demand": 22},
    {"sku": "SKU-GROC-009", "name": "Vim Dishwash Bar 300g", "category": "Household Care", "price": 32.00, "velocity": "steady", "base_demand": 25},
    {"sku": "SKU-GROC-010", "name": "Dettol Antiseptic Soap 125g", "category": "Personal Care", "price": 42.00, "velocity": "steady", "base_demand": 15},

    # 5 Slow-Moving Items (Intermittent / Low Velocity)
    {"sku": "SKU-GROC-011", "name": "Ferrero Rocher Chocolate 16 pcs", "category": "Confectionery", "price": 499.00, "velocity": "slow", "base_demand": 2.5},
    {"sku": "SKU-GROC-012", "name": "Organic Honey 500g Glass Jar", "category": "Health Food", "price": 380.00, "velocity": "slow", "base_demand": 1.8},
    {"sku": "SKU-GROC-013", "name": "Extra Virgin Olive Oil 500ml", "category": "Edible Oils", "price": 650.00, "velocity": "slow", "base_demand": 1.2},
    {"sku": "SKU-GROC-014", "name": "Stainless Steel Scourer 3-Pack", "category": "Household Items", "price": 75.00, "velocity": "slow", "base_demand": 3.0},
    {"sku": "SKU-GROC-015", "name": "Basmati Biryani Rice Premium 5kg", "category": "Rice & Grains", "price": 620.00, "velocity": "slow", "base_demand": 2.0},

    # 5 Declining Products (Negative trend)
    {"sku": "SKU-GROC-016", "name": "Classic Matchbox 10-Pack", "category": "Household Items", "price": 15.00, "velocity": "declining", "base_demand": 20},
    {"sku": "SKU-GROC-017", "name": "Traditional Mosquito Coils 10s", "category": "Pest Control", "price": 45.00, "velocity": "declining", "base_demand": 18},
    {"sku": "SKU-GROC-018", "name": "Plain White Incense Sticks 100g", "category": "Pooja Needs", "price": 35.00, "velocity": "declining", "base_demand": 16},
    {"sku": "SKU-GROC-019", "name": "Unbranded Washing Powder 1kg", "category": "Laundry & Care", "price": 60.00, "velocity": "declining", "base_demand": 22},
    {"sku": "SKU-GROC-020", "name": "Plastic Scrub Pad Pack of 2", "category": "Household Items", "price": 25.00, "velocity": "declining", "base_demand": 15},
]

# Major Indian Festivals in 2025
FESTIVALS_2025 = {
    date(2025, 3, 14): ("Holi", ["Atta & Flours", "Edible Oils", "Confectionery", "Instant Food"]),
    date(2025, 3, 15): ("Holi", ["Atta & Flours", "Edible Oils", "Confectionery", "Instant Food"]),
    date(2025, 3, 31): ("Eid al-Fitr", ["Atta & Flours", "Edible Oils", "Rice & Grains", "Confectionery"]),
    date(2025, 8, 9): ("Raksha Bandhan", ["Confectionery", "Health Food"]),
    date(2025, 10, 1): ("Durga Puja", ["Atta & Flours", "Edible Oils", "Rice & Grains", "Confectionery"]),
    date(2025, 10, 2): ("Durga Puja", ["Atta & Flours", "Edible Oils", "Rice & Grains", "Confectionery"]),
    date(2025, 10, 19): ("Diwali", ["Atta & Flours", "Edible Oils", "Confectionery", "Dry Fruits", "Pooja Needs"]),
    date(2025, 10, 20): ("Diwali", ["Atta & Flours", "Edible Oils", "Confectionery", "Dry Fruits", "Pooja Needs"]),
    date(2025, 12, 25): ("Christmas", ["Confectionery", "Beverages"]),
}

# National Holidays in 2025
HOLIDAYS_2025 = {
    date(2025, 1, 26), # Republic Day
    date(2025, 8, 15), # Independence Day
    date(2025, 10, 2), # Gandhi Jayanti
}

def generate_dataset(output_path: Path, days: int = 365) -> int:
    random.seed(42) # Reproducible realistic random generation
    start_date = date(2025, 1, 1)
    
    rows = []
    
    for p in PRODUCTS:
        sku = p["sku"]
        p_name = p["name"]
        cat = p["category"]
        base_price = p["price"]
        vel = p["velocity"]
        base_demand = p["base_demand"]
        
        # Track inventory state for simulated store replenishment
        current_inventory = int(base_demand * random.uniform(3.0, 5.0))
        reorder_threshold = int(base_demand * 1.5)
        restock_amount = int(base_demand * 4.0)
        
        # Promo schedule: 3 random promo periods during the year
        promo_days = set()
        for _ in range(3):
            promo_start = start_date + timedelta(days=random.randint(10, 340))
            promo_duration = random.randint(3, 6)
            for d in range(promo_duration):
                promo_days.add(promo_start + timedelta(days=d))

        for day_idx in range(days):
            current_date = start_date + timedelta(days=day_idx)
            
            # 1. Weekly seasonality: Friday (4), Saturday (5), Sunday (6) multiplier
            weekday = current_date.weekday()
            weekly_mult = 1.30 + random.uniform(-0.1, 0.1) if weekday >= 4 else 0.90 + random.uniform(-0.08, 0.08)
            
            # 2. Annual seasonality (Sine wave)
            month = current_date.month
            seasonal_mult = 1.0
            if "Beverages" in cat or "Dairy" in cat:
                seasonal_mult = 1.0 + 0.35 * math.sin(2 * math.pi * (day_idx - 80) / 365)
            elif "Personal Care" in cat:
                seasonal_mult = 1.0 + 0.20 * math.sin(2 * math.pi * (day_idx - 150) / 365)

            # 3. Declining product trend
            trend_mult = 1.0
            if vel == "declining":
                trend_mult = max(0.35, 1.0 - (0.0015 * day_idx) + random.uniform(-0.05, 0.05))

            # 4. Festival uplift
            fest_info = FESTIVALS_2025.get(current_date)
            fest_name = None
            fest_mult = 1.0
            if fest_info:
                fest_name, fest_cats = fest_info
                if cat in fest_cats:
                    fest_mult = random.uniform(1.5, 2.2)
                else:
                    fest_mult = random.uniform(1.1, 1.3)

            # 5. Promotion effect
            is_promo = current_date in promo_days
            promo_mult = random.uniform(1.35, 1.70) if is_promo else 1.0
            selling_price = round(base_price * (0.85 if is_promo else 1.00), 2)

            # 6. Holiday effect
            is_holiday = current_date in HOLIDAYS_2025

            # Calculate Latent Demand (True Unconstrained Demand)
            if vel == "slow":
                # Poisson distributed demand for slow-moving items
                mean_d = max(0.1, base_demand * weekly_mult * seasonal_mult * fest_mult * promo_mult)
                latent_demand = float(random.poisson(mean_d) if hasattr(random, 'poisson') else math.floor(random.expovariate(1.0 / mean_d) if mean_d > 0 else 0))
            else:
                expected_d = base_demand * weekly_mult * seasonal_mult * trend_mult * fest_mult * promo_mult
                noise = random.gauss(0, max(1.0, expected_d * 0.15))
                latent_demand = max(0.0, expected_d + noise)

            latent_demand_units = int(round(latent_demand))

            # 7. Inventory Restock Simulation & Stockout Censoring
            if current_inventory < reorder_threshold and random.random() < 0.8:
                # 80% chance restock arrives
                current_inventory += restock_amount

            # Check if stockout occurs on this day
            units_sold = min(current_inventory, latent_demand_units)
            stock_available = max(0, current_inventory - units_sold)
            
            # Simulated is_stockout boolean
            is_stockout_flag = (current_inventory < latent_demand_units)

            # Update inventory for next day
            current_inventory = stock_available

            # Represent NULL festival as empty string in CSV
            festival_str = fest_name if fest_name else ""

            rows.append([
                current_date.strftime("%Y-%m-%d"),
                sku,
                p_name,
                cat,
                units_sold,
                f"{selling_price:.2f}",
                1 if is_promo else 0,
                1 if is_holiday else 0,
                festival_str,
                stock_available
            ])

    # Write output CSV with Header Comment
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        f.write(f"{HEADER_COMMENT}\n")
        writer = csv.writer(f)
        writer.writerow([
            "date", "sku", "product_name", "category",
            "units_sold", "selling_price", "promotion", "holiday", "festival", "stock_available"
        ])
        writer.writerows(rows)

    print(f"Successfully generated synthetic dataset at: {output_path} ({len(rows)} records)")
    return len(rows)

if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent.parent / "data" / "synthetic_sales_data.csv"
    generate_dataset(out_file)
