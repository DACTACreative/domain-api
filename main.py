from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import requests
import os
import logging
import base64
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/home")
async def home():
    with open('templates/home.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

# Load environment variables
load_dotenv()

# Domain API Configuration
DOMAIN_AUTH_URL = "https://auth.domain.com.au/v1/connect/token"
DOMAIN_API_URL = "https://api.domain.com.au/v1"

def get_domain_access_token():
    try:
        client_id = "client_c63716c5cb241d81584891715322f86c"
        client_secret = "secret_f3b548cc6093b65288efad68b44d62d9"
        
        if not client_id or not client_secret:
            logging.error("Missing Domain API credentials")
            raise ValueError("Missing Domain API credentials")
        
        # Create basic auth token
        auth_string = f"{client_id}:{client_secret}"
        auth_bytes = auth_string.encode('ascii')
        base64_auth = base64.b64encode(auth_bytes).decode('ascii')
        
        response = requests.post(
            "https://auth.domain.com.au/v1/connect/token",
            headers={
                "Authorization": f"Basic {base64_auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials",
                "scope": "api_agencies_read api_listings_read api_properties_read"
            }
        )
        
        response.raise_for_status()
        data = response.json()
        
        logging.info(f"Client ID: {client_id}")
        logging.info(f"Auth response: {data}")
        
        return data.get("access_token")
    except requests.exceptions.RequestException as e:
        logging.error(f"Auth error: {str(e)}")
        logging.error(f"Response content: {e.response.text if hasattr(e, 'response') else 'No response'}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logging.error(f"Error getting access token: {str(e)}")
        raise

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
        api_key = "key_d05406abc5556a22176546f7283736ac"
        
        if not api_key:
            logging.error("Missing Domain API key")
            return {"error": "API key not configured"}
        
        response = requests.post(
            f"{DOMAIN_API_URL}/listings/residential/_search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Api-Key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json={
                "listingType": "Sale",
                "propertyTypes": ["House"],
                "locations": [{"suburb": "Castlemaine", "state": "VIC"}],
                "pageSize": 1
            }
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

from datetime import datetime
from typing import Optional

@app.get("/search-listings/{suburb}")
async def search_listings(
    suburb: str,
    page: int = 1,
    pageSize: int = 10,
    dateFrom: Optional[str] = None,
    dateTo: Optional[str] = None
):
    try:
        # Get access token
        access_token = get_domain_access_token()
        api_key = "key_d05406abc5556a22176546f7283736ac"
        
        if not api_key:
            logging.error("Missing Domain API key")
            return {"error": "API key not configured"}
        
        # Convert date strings to proper format if provided
        search_json = {
            "listingType": "Sale",
            "propertyTypes": ["House"],
            "locations": [{"suburb": suburb, "state": "VIC"}],
            "page": page,
            "pageSize": min(pageSize, 20),  # Limit page size to 20
            "sort": {"sortKey": "DateListed", "direction": "Descending"}
        }

        if dateFrom:
            try:
                date_from = datetime.strptime(dateFrom, "%Y-%m-%d").strftime("%Y-%m-%d")
                search_json["dateFrom"] = date_from
            except ValueError:
                return {"error": "Invalid dateFrom format. Use YYYY-MM-DD"}

        if dateTo:
            try:
                date_to = datetime.strptime(dateTo, "%Y-%m-%d").strftime("%Y-%m-%d")
                search_json["dateTo"] = date_to
            except ValueError:
                return {"error": "Invalid dateTo format. Use YYYY-MM-DD"}

        response = requests.post(
            f"{DOMAIN_API_URL}/listings/residential/_search",
            headers={
                "Authorization": f"Bearer {access_token}",
                "X-Api-Key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            json=search_json
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
