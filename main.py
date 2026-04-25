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

# --- THE VAPI-SPECIFIC PARSER ---
# This specifically hunts for Vapi's weird {"name": "variable", "result": "data"} structure
def extract_vapi_variable(payload, var_name):
    if isinstance(payload, dict):
        if payload.get("name") == var_name and "result" in payload:
            return payload["result"]
        for key, value in payload.items():
            res = extract_vapi_variable(value, var_name)
            if res is not None:
                return res
    elif isinstance(payload, list):
        for item in payload:
            res = extract_vapi_variable(item, var_name)
            if res is not None:
                return res
    return None

@app.post("/vapi-webhook")
async def handle_vapi_webhook(request: Request):
    payload = await request.json()
    
    if payload.get("message", {}).get("type") == "end-of-call-report":
        
        # Grab the data using the new specific parser
        name = extract_vapi_variable(payload, "customer_name") or "Unknown"
        item = extract_vapi_variable(payload, "item") or "Unknown"
        qty = extract_vapi_variable(payload, "quantity") or "1"
        total = extract_vapi_variable(payload, "total_price") or ""
        
        # Auto-generate ID and Time
        order_id = str(uuid.uuid4())[:6].upper() 
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "Pending"
        
        # Format the row perfectly
        row_data = [order_id, current_date, name, item, qty, "", total, status]
        
        # Paste cleanly below header
        sheet.append_row(
            row_data, 
            value_input_option="USER_ENTERED", 
            insert_data_option="INSERT_ROWS", 
            table_range="B8"
        )
        
        return {"status": "success", "order_id": order_id}

    return {"status": "ignored"}
