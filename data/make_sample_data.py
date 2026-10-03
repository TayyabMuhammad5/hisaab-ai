import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

def generate_sample_data(out_dir: Path):
    np.random.seed(42)
    
    # 1. Sales Data
    num_sales = 3000
    dates = [datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365)) for _ in range(num_sales)]
    items = ["Atta 10kg", "Sugar 1kg", "Cooking Oil 1L", "Milk 1L", "Tea 200g", "Rice 1kg", "Soap", "Shampoo"]
    categories = ["grocery", "Grocery", "Dairy", "dairy", "beverages", "Personal Care"]
    customers = ["Ali", "Ahmed", "Fatima", "Zainab", "Usman", "Ayesha", "Walk-in"]
    payment_methods = ["cash", "easypaisa", "jazzcash", "udhaar"]
    
    sales_data = []
    for i in range(num_sales):
        item = np.random.choice(items)
        qty = np.random.randint(1, 5)
        price = np.random.randint(50, 1500)
        
        # Inject some messy values
        total_str = f"Rs {qty * price}" if np.random.rand() > 0.8 else qty * price
        if np.random.rand() > 0.95:
            total_str = None # blank cell
            
        sales_data.append({
            "Date": dates[i].strftime("%d/%m/%Y"), # day-first
            "invoice_id": f"INV-{1000 + i}",
            "Item": item,
            "Category": np.random.choice(categories),
            "Quantity": qty,
            "Unit_Price": price,
            "Total": total_str,
            "Customer": np.random.choice(customers),
            "Payment_Method": np.random.choice(payment_methods)
        })
        
    df_sales = pd.DataFrame(sales_data)
    
    # 2. Udhaar Ledger Data
    num_udhaar = 500
    udhaar_data = []
    for i in range(num_udhaar):
        udhaar_data.append({
            "Customer": np.random.choice([c for c in customers if c != "Walk-in"]),
            "Date": (datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 365))).strftime("%d-%m-%Y"), # Mixed date format day-first
            "Amount": f"Rs {np.random.randint(100, 5000)}" if np.random.rand() > 0.5 else np.random.randint(100, 5000),
            "Type": np.random.choice(["given", "paid"]),
            "Note": np.random.choice(["grocery", "milk", "cash", "", "last month pending"])
        })
        
    df_udhaar = pd.DataFrame(udhaar_data)
    
    # Save to Excel and CSVs
    out_dir.mkdir(parents=True, exist_ok=True)
    excel_path = out_dir / "sample_shop.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_sales.to_excel(writer, sheet_name="sales", index=False)
        df_udhaar.to_excel(writer, sheet_name="udhaar_ledger", index=False)
        
    df_sales.to_csv(out_dir / "sales.csv", index=False)
    df_udhaar.to_csv(out_dir / "udhaar_ledger.csv", index=False)
    
    print(f"Sample data generated at {excel_path}")

if __name__ == "__main__":
    generate_sample_data(Path(__file__).parent)
