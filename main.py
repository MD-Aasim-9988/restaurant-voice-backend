from fastapi import FastAPI, Request
import gspread
from google.oauth2.service_account import Credentials
import os
import json
import uuid
from datetime import datetime

app = FastAPI()

# 1. Connect to Google Sheets securely
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds_json = os.environ.get("GOOGLE_CREDS_JSON")
creds = Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
client = gspread.authorize(creds)

# 2. Look for your exact document ("Restaurant Order") and the specific tab ("OrderData")
client.open_by_url("https://docs.google.com/spreadsheets/d/1dHFNayzoxXXO73rZr0l3FsnRvFOmV59xJA0d_qf3KO0/edit?gid=0#gid=0")

@app.post("/vapi-webhook")
async def handle_vapi_webhook(request: Request):
    payload = await request.json()
    
    # When the call hangs up, Vapi sends an "end-of-call-report"
    if payload.get("message", {}).get("type") == "end-of-call-report":
        data = payload["message"].get("call", {}).get("structuredData", {})
        
        # Grab the data Vapi extracted
        name = data.get("customer_name", "Unknown")
        item = data.get("item", "Unknown")
        qty = data.get("quantity", "1")
        
        # Auto-generate an Order ID and Timestamp
        order_id = str(uuid.uuid4())[:6].upper() 
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M") 
        status = "Pending"
        
        # Format the row perfectly to match your specific layout
        row_data = [order_id, current_date, name, item, qty, "", "", status]
        
        # Paste it starting at Row 7 (ignoring your top dashboard)
        sheet.append_row(row_data, table_range="A7")
        
        return {"status": "success", "order_id": order_id}

    return {"status": "ignored"}
