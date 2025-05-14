from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from pydantic import BaseModel
import requests
import os
import logging
import base64
from dotenv import load_dotenv
from db_operations import save_listing_to_db, get_listings_by_suburb
from database import engine
from pathlib import Path
import csv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Create data directory if it doesn't exist
data_dir = Path("data")
data_dir.mkdir(exist_ok=True)

app = FastAPI(title="Domain API", description="API for interacting with Domain real estate data")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the data directory
app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

@app.get("/home")
async def home():
    with open('templates/home.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get('/databaseviewer')
async def database_viewer():
    """Show database viewer page"""
    with open('templates/database.html', 'r') as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get('/test-db-connection')
async def test_db_connection():
    """Test database connection"""
    try:
        # Try to connect and execute a simple query
        with engine.connect() as conn:
            result = conn.execute(text('SELECT 1')).scalar()
            if result == 1:
                return JSONResponse({
                    'success': True,
                    'message': 'Successfully connected to database!'
                })
    except Exception as e:
        logging.error(f'Database connection error: {str(e)}')
        return JSONResponse({
            'success': False,
            'message': f'Failed to connect to database: {str(e)}'
        })

@app.get('/api/listings')
async def get_listings():
    """Get all listings from database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT l.*, pd.*, a.* 
                FROM listings l
                LEFT JOIN property_details pd ON l.id = pd.listing_id
                LEFT JOIN addresses a ON l.id = a.listing_id
                ORDER BY l.created_at DESC
                LIMIT 100
            """))
            columns = result.keys()
            listings = [dict(zip(columns, row)) for row in result.fetchall()]
            return JSONResponse({
                'success': True,
                'listings': listings
            })
    except Exception as e:
        logging.error(f'Error fetching listings: {str(e)}')
        return JSONResponse({
            'success': False,
            'message': f'Failed to fetch listings: {str(e)}'
        })

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

@app.get("/search-listings/{suburb}")
async def search_listings(suburb: str, pageSize: int = 100):
    """Search listings and save to database"""
    try:
        # Get access token
        access_token = get_domain_access_token()
        api_key = "key_d05406abc5556a22176546f7283736ac"
        
        if not api_key:
            logging.error("Missing Domain API key")
            return {"error": "API key not configured"}
        
        all_listings = []
        current_page = 1
        total_pages = 1  # Will be updated after first request
        
        while current_page <= total_pages:
            search_json = {
                "locations": [{
                    "suburb": suburb,
                    "state": "VIC",
                    "postCode": "3450"
                }],
                "page": current_page,
                "pageSize": pageSize
            }

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
            
            response_data = response.json()
            if not response_data:  # No more results
                break
                
            all_listings.extend(response_data.get('data', []))

            # Save listings to database
            for listing in response_data.get('data', []):
                try:
                    save_listing_to_db(listing)
                except Exception as e:
                    logging.error(f"Error saving listing {listing.get('id')}: {str(e)}")
            
            # Update total pages based on results
            if current_page == 1:
                # Estimate total pages based on API limit of 1000 results
                total_pages = min(10, (1000 + pageSize - 1) // pageSize)
                
            current_page += 1
            
            # Break if we hit the API limit
            if len(all_listings) >= 1000:
                break

        # Extract available fields from first listing (if any)
        available_fields = []
        if all_listings and len(all_listings) > 0:
            first_listing = all_listings[0].get('listing', {})
            available_fields = [
                {"field": field, "type": str(type(value).__name__)} 
                for field, value in first_listing.items()
            ]
        
        # Save to CSV
        filename = f'{suburb.lower()}_listings.csv'
        csv_path = Path(f'data/{filename}')
        csv_path.parent.mkdir(exist_ok=True)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write headers
            if all_listings:
                first_listing = all_listings[0]['listing']
                headers = [
                    'Price',
                    'Address',
                    'Agent Names',
                    'Agency',
                    'Bedrooms',
                    'Bathrooms',
                    'Car Spaces',
                    'Land Size',
                    'URL'
                ]
                writer.writerow(headers)
                
                # Write data
                for item in all_listings:
                    listing = item['listing']
                    property_details = listing.get('propertyDetails', {})
                    price_details = listing.get('priceDetails', {})
                    advertiser = listing.get('advertiser', {})
                    
                    row = [
                        price_details.get('displayPrice', ''),
                        property_details.get('displayableAddress', ''),
                        '; '.join(c.get('name', '') for c in advertiser.get('contacts', [])),  # Agent names
                        advertiser.get('name', ''),  # Agency name
                        property_details.get('bedrooms', ''),
                        property_details.get('bathrooms', ''),
                        property_details.get('carspaces', ''),
                        f"{property_details.get('landArea', '')} {property_details.get('areaUnit', '')}".strip(),
                        f"https://www.domain.com.au/{listing.get('listingSlug', '')}"
                    ]
                    writer.writerow(row)
        
        return {
            "success": True, 
            "total_listings": len(all_listings),
            "available_fields": available_fields,
            "data": all_listings,  # Return all listings
            "csv_url": f"/data/{filename}"
        }
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Domain API error: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logging.error(error_msg)
        return {"error": error_msg}
