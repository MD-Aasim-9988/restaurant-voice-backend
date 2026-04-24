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

# Your specific Google Sheet link is wired directly here
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1dHFNayzoxXXO73rZr0l3FsnRvFOmV59xJA0d_qf3KO0/edit").worksheet("OrderData")

@app.post("/vapi-webhook")
async def handle_vapi_webhook(request: Request):
    payload = await request.json()
    
    if payload.get("message", {}).get("type") == "end-of-call-report":
        data = payload["message"].get("call", {}).get("structuredData", {})
        
        # Grab all the data
        name = data.get("customer_name", "Unknown")
        item = data.get("item", "Unknown")
        qty = data.get("quantity", "1")
        total = data.get("total_price", "")
        
        # Auto-generate ID and Time
        order_id = str(uuid.uuid4())[:6].upper() 
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "Pending"
        
        # Format the row exactly for your sheet
        row_data = [order_id, current_date, name, item, qty, "", total, status]
        
        # Paste it starting at Row 7
        sheet.append_row(row_data, table_range="B7")
        
        return {"status": "success", "order_id": order_id}

    return {"status": "ignored"}
