from fastapi import FastAPI, Request
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import uuid
from datetime import datetime

app = FastAPI()

# Connect to Google Sheets securely
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds_json = os.environ.get("GOOGLE_CREDS_JSON")
creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
client = gspread.authorize(creds)

# Your specific Google Sheet link
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1dHFNayzoxXXO73rZr0l3FsnRvFOmV59xJA0d_qf3KO0/edit").worksheet("OrderData")

# --- NEW: The God-Mode Search Function ---
# This scans the entire package recursively to find your variables no matter where Vapi hides them.
def find_data(payload, target_key):
    if isinstance(payload, dict):
        if target_key in payload:
            return payload[target_key]
        for key, value in payload.items():
            result = find_data(value, target_key)
            if result is not None:
                return result
    elif isinstance(payload, list):
        for item in payload:
            result = find_data(item, target_key)
            if result is not None:
                return result
    return None

@app.post("/vapi-webhook")
async def handle_vapi_webhook(request: Request):
    payload = await request.json()
    
    # X-Ray Logs
    print("===== VAPI PAYLOAD START =====", flush=True)
    print(json.dumps(payload, indent=2), flush=True)
    print("===== VAPI PAYLOAD END =====", flush=True)
    
    if payload.get("message", {}).get("type") == "end-of-call-report":
        
        # --- NEW: Use God-Mode to grab the data ---
        name = find_data(payload, "customer_name") or "Unknown"
        item = find_data(payload, "item") or "Unknown"
        qty = find_data(payload, "quantity") or "1"
        total = find_data(payload, "total_price") or ""
        
        # Auto-generate ID and Time
        order_id = str(uuid.uuid4())[:6].upper() 
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "Pending"
        
        # Format the row exactly for your sheet
        # Note: The empty string "" skips your Price column so 'total' lands exactly in your Total column!
        row_data = [order_id, current_date, name, item, qty, "", total, status]
        
        # Paste it perfectly and force a brand new row
        sheet.append_row(
            row_data, 
            value_input_option="USER_ENTERED", 
            insert_data_option="INSERT_ROWS", 
            table_range="B7"
        )
        
        return {"status": "success", "order_id": order_id}

    return {"status": "ignored"}
