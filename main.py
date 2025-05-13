from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="Domain API", description="API for interacting with Domain real estate data")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dactacreative.github.io", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Domain API Configuration
DOMAIN_AUTH_URL = "https://auth.domain.com.au/v1/connect/token"
DOMAIN_API_URL = "https://api.domain.com.au/v1"

def get_domain_access_token():
    client_id = os.getenv("DOMAIN_CLIENT_ID")
    client_secret = os.getenv("DOMAIN_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        logging.error("Missing Domain API credentials")
        raise HTTPException(status_code=500, detail="API credentials not configured")
    
    try:
        response = requests.post(
            DOMAIN_AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "scope": "api_agencies_read api_listings_read"
            },
            auth=(client_id, client_secret)
        )
        
        response.raise_for_status()
        return response.json()["access_token"]
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Auth error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "Welcome to Domain API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-05-13T11:13:16+10:00"}

@app.get("/test-domain")
async def test_domain_api():
    try:
        # Get access token
        access_token = get_domain_access_token()
        api_key = os.getenv("DOMAIN_API_KEY")
        
        if not api_key:
            logging.error("Missing Domain API key")
            return {"error": "API key not configured"}
        
        # Make a simple API call to get agencies
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Api-Key": api_key
        }
        
        try:
            response = requests.get(
                f"{DOMAIN_API_URL}/agencies",
                headers=headers,
                params={"pageNumber": 1, "pageSize": 1}
            )
            response.raise_for_status()
            
            return {"success": True, "data": response.json()}
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Domain API error: {str(e)}"
            logging.error(error_msg)
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}
