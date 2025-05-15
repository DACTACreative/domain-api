from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import text
from pydantic import BaseModel
import requests
import os
import logging
import base64
import json
from dotenv import load_dotenv
from db_operations import save_listing_to_db, get_listings_by_suburb
from database import engine
from pathlib import Path
import csv
from datetime import datetime, date

# Set logging to show full response
logging.basicConfig(level=logging.INFO, format='%(message)s')

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

# Configure templates
templates = Jinja2Templates(directory="templates")

# Mount the data directory
app.mount("/data", StaticFiles(directory=str(data_dir)), name="data")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse("home.html", {"request": request})
    except Exception as e:
        logging.error(f"Error serving home page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/database", response_class=HTMLResponse)
async def database_viewer(request: Request):
    try:
        return templates.TemplateResponse("database.html", {"request": request})
    except Exception as e:
        logging.error(f"Error serving database page: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/test-db-connection")
def test_db_connection():
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Test database connection
            db.execute(text('SELECT 1'))
            return {"success": True, "message": "Successfully connected to database"}
        except Exception as e:
            logging.error(f"Database connection error: {str(e)}")
            return {"success": False, "message": f"Database connection error: {str(e)}"}
        finally:
            db.close()
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/stats")
def get_listing_stats():
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Get various counts
            result = db.execute(text("""
                SELECT
                    COUNT(*) as total_listings,
                    COUNT(CASE WHEN price IS NOT NULL THEN 1 END) as listings_with_price,
                    COUNT(CASE WHEN pd.bedrooms IS NOT NULL THEN 1 END) as listings_with_bedrooms,
                    COUNT(CASE WHEN a.suburb IS NOT NULL THEN 1 END) as listings_with_location,
                    AVG(CASE WHEN price IS NOT NULL THEN price END) as avg_price,
                    MIN(CASE WHEN price IS NOT NULL THEN price END) as min_price,
                    MAX(CASE WHEN price IS NOT NULL THEN price END) as max_price
                FROM listings l
                LEFT JOIN property_details pd ON pd.listing_id = l.id
                LEFT JOIN addresses a ON a.listing_id = l.id
            """))
            
            stats = dict(result.fetchone())
            
            # Format currency values
            for key in ['avg_price', 'min_price', 'max_price']:
                if stats[key] is not None:
                    stats[key] = round(float(stats[key]), 2)
            
            return {
                "success": True,
                "stats": stats
            }
                
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

@app.get("/api/listings")
def get_listings():
    try:
        from database import SessionLocal
        db = SessionLocal()
        try:
            # Get all listings
            result = db.execute(text("""
                SELECT 
                    l.id,
                    l.price,
                    a.suburb,
                    a.state,
                    a.postcode,
                    pd.bedrooms,
                    pd.bathrooms,
                    pd.parking_spaces,
                    l.property_type,
                    l.created_at
                FROM listings l
                LEFT JOIN addresses a ON a.listing_id = l.id
                LEFT JOIN property_details pd ON pd.listing_id = l.id
                ORDER BY l.created_at DESC
            """))
            
            # Convert SQLAlchemy result rows to dictionaries
            listings = [{
                'id': row.id,
                'price': row.price,
                'suburb': row.suburb,
                'state': row.state,
                'postcode': row.postcode,
                'bedrooms': row.bedrooms,
                'bathrooms': row.bathrooms,
                'parking_spaces': row.parking_spaces,
                'property_type': row.property_type,
                'created_at': row.created_at.isoformat() if row.created_at else None
            } for row in result]
            
            return {
                "success": True,
                "listings": listings
            }
                
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}


@app.get("/api/check-tables")
def check_tables():
    """Check if all required tables exist"""
    try:
        from sqlalchemy import text
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # Test database connection
            db.execute(text('SELECT 1'))
            logging.info("Database connection successful")
            
            # Get list of tables
            result = db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            
            required_tables = [
                'listings',
                'property_details',
                'addresses',
                'agencies',
                'agents',
                'listing_agents',
                'sale_history'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                return {
                    "error": "Missing tables",
                    "missing": missing_tables,
                    "existing": tables
                }
            else:
                return {
                    "success": True,
                    "message": "All required tables exist",
                    "tables": tables
                }
                
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"error": f"Error: {str(e)}"}

@app.get("/api/test-query")
def test_query():
    """Test a simple database query"""
    try:
        from sqlalchemy import text
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # Test a simple query
            result = db.execute(text("SELECT COUNT(*) FROM listings"))
            count = result.scalar()
            
            return {
                "success": True,
                "message": "Query successful",
                "listings_count": count
            }
                
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return {"error": f"Database error: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"error": f"Error: {str(e)}"}

@app.get("/api/test-save")
def test_save():
    """Test saving a fake listing"""
    try:
        import traceback
        from sqlalchemy import text
        from database import SessionLocal
        
        # First test database connection
        db = SessionLocal()
        try:
            db.execute(text('SELECT 1'))
            logging.info("Database connection successful")
        except Exception as e:
            logging.error(f"Database connection failed: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Database connection failed: {str(e)}"}
        finally:
            db.close()
            
        fake_listing = {
            'type': 'PropertyListing',
            'listing': {
                'id': '123456789',
                'listingType': 'Sale',
                'status': 'current',
                'dateListed': '2025-05-14T00:00:00',
                'dateUpdated': '2025-05-14T00:00:00',
                'priceDetails': {
                    'displayPrice': '$850,000'
                },
                'headline': 'Test Listing',
                'summaryDescription': 'Test description',
                'listingSlug': 'test-123',
                'propertyDetails': {
                    'propertyType': 'House',
                    'bedrooms': 3,
                    'bathrooms': 2
                },
                'addressParts': {
                    'displayAddress': '123 Test Street',
                    'streetNumber': '123',
                    'street': 'Test Street',
                    'suburb': 'Richmond',
                    'state': 'VIC',
                    'postcode': '3121'
                }
            }
        }
        
        logging.info("Attempting to save fake listing...")
        logging.info(f"Fake listing data: {json.dumps(fake_listing, indent=2)}")
        
        # Try to save the listing
        logging.info("Attempting to save listing to database...")
        try:
            result = save_listing_to_db(fake_listing)
            logging.info(f"Save result: {result}")
            
            if result:
                return {"success": True, "message": f"Successfully saved fake listing with ID {result}"}
            else:
                logging.error("save_listing_to_db returned None")
                return {"error": "Failed to save fake listing - no ID returned"}
                
        except Exception as e:
            logging.error(f"Error in save_listing_to_db: {str(e)}")
            logging.error(f"Error type: {type(e).__name__}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return {"error": f"Database save failed: {type(e).__name__}: {str(e)}"}
            
    except Exception as e:
        logging.error(f"Error in test_save: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return {"error": f"Error: {type(e).__name__}: {str(e)}"}

@app.get('/databaseviewer')
async def database_viewer(request: Request):
    """Show database viewer page"""
    return templates.TemplateResponse("database.html", {"request": request})

@app.get('/api/test-db-connection')
async def test_db_connection():
    """Test database connection"""
    try:
        from sqlalchemy import text
        from database import SessionLocal
        
        db = SessionLocal()
        try:
            # Test database connection
            db.execute(text('SELECT 1'))
            return {"success": True, "message": "Database connection successful"}
        except Exception as e:
            logging.error(f"Database error: {str(e)}")
            return {"success": False, "message": f"Database error: {str(e)}"}
        finally:
            db.close()
            
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return {"success": False, "message": f"Error: {str(e)}"}

def serialize_db_value(value):
    """Serialize database values for JSON response.
    
    Args:
        value: Any database value that needs serialization
        
    Returns:
        JSON serializable value
    """
    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, Decimal):
        return float(value)
    return value

@app.get('/api/test-listings')
async def test_listings():
    """Test endpoint to verify listing serialization"""
    try:
        from decimal import Decimal
        
        # Create a test row with various data types
        test_data = {
            'id': 1,
            'price': Decimal('850000.00'),
            'created_at': datetime.now(),
            'description': 'Test listing',
            'bedrooms': 3,
            'null_value': None
        }
        
        # Test serialization
        serialized = {k: serialize_db_value(v) for k, v in test_data.items()}
        
        logging.info(f"Original test data: {test_data}")
        logging.info(f"Serialized data: {serialized}")
        
        return JSONResponse({
            'success': True,
            'test_data': serialized
        })
        
    except Exception as e:
        logging.error(f"Error in test listings: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse({
            'success': False,
            'message': f"Error: {type(e).__name__}: {str(e)}"
        })

@app.get('/api/listings')
async def get_listings():
    """Get all listings from database with proper serialization."""
    try:
        from decimal import Decimal
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT l.*, pd.*, a.* 
                FROM listings l
                LEFT JOIN property_details pd ON l.id = pd.listing_id
                LEFT JOIN addresses a ON l.id = a.listing_id
                ORDER BY l.created_at DESC
                LIMIT 100
            """))
            
            # Get column names
            columns = result.keys()
            logging.info(f"Columns in result: {columns}")
            
            listings = []
            for row in result.fetchall():
                # Create dict and serialize values
                listing = {col: serialize_db_value(val) for col, val in zip(columns, row)}
                listings.append(listing)
                
            logging.info(f"Successfully fetched {len(listings)} listings")
            return JSONResponse({
                'success': True,
                'listings': listings
            })
            
    except Exception as e:
        logging.error(f"Error fetching listings: {str(e)}")
        logging.error(f"Error type: {type(e).__name__}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        return JSONResponse({
            'success': False,
            'message': f"Error: {type(e).__name__}: {str(e)}"
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

@app.get('/api/test-search/{suburb}')
async def test_search_listings(suburb: str):
    """Test endpoint to show raw Domain API response"""
    try:
        # Get access token
        access_token = get_domain_access_token()
        
        # Log request details
        logging.info("\nRequest Details:")
        logging.info(f"Endpoint: {DOMAIN_API_URL}/properties/_suggest")
        logging.info(f"Headers: Authorization: Bearer {access_token}")
        
        # Make API request
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        params = {
            'terms': suburb,
            'pageSize': 20
        }
        
        response = requests.get(
            f"{DOMAIN_API_URL}/properties/_suggest",
            headers=headers,
            params=params
        )
        
        # Log response details
        logging.info("\nResponse Details:")
        logging.info(f"Status Code: {response.status_code}")
        logging.info("Headers:")
        for key, value in response.headers.items():
            logging.info(f"{key}: {value}")
        
        # Log response body
        logging.info("\nResponse Body:")
        response_data = response.json()
        logging.info(json.dumps(response_data, indent=2))
        
        return response_data
        
    except Exception as e:
        logging.error(f"Error in test search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_listing(raw_listing: dict) -> dict:
    """Process a raw Domain API listing into our schema format"""
    try:
        listing = raw_listing.get('listing', {})
        if not listing:
            return None

        # Extract price details
        price_details = listing.get('priceDetails', {})
        display_price = price_details.get('displayPrice', '')
        
        # Try to extract numeric price
        try:
            price_text = display_price.replace('$', '').replace(',', '').split('-')[0].strip()
            price = float(price_text) if price_text.replace('.', '').isdigit() else None
        except (ValueError, IndexError):
            price = None

        # Get property details
        property_details = listing.get('propertyDetails', {})
        
        # Get address details
        address = {
            'unit_number': property_details.get('unitNumber', ''),
            'street_number': property_details.get('streetNumber', ''),
            'street_name': property_details.get('street', ''),
            'suburb': property_details.get('suburb', ''),
            'state': property_details.get('state', ''),
            'postcode': property_details.get('postcode', ''),
            'display_address': property_details.get('displayableAddress', ''),
            'latitude': property_details.get('latitude'),
            'longitude': property_details.get('longitude')
        }

        # Format the listing according to our schema
        processed = {
            'domain_listing_id': str(listing.get('id', '')),
            'listing_type': listing.get('listingType'),
            'current_status': listing.get('status', 'live').lower(),
            'date_listed': listing.get('dateListed'),
            'date_updated': listing.get('dateUpdated') or listing.get('dateListed'),
            
            # Price information
            'price_details': price_details,
            'display_price': display_price,
            'price': price,
            
            # Property details
            'property_types': property_details.get('allPropertyTypes', []),
            'bedrooms': property_details.get('bedrooms'),
            'bathrooms': property_details.get('bathrooms'),
            'parking_spaces': property_details.get('carspaces'),
            'property_size': property_details.get('buildingArea'),
            'land_area': property_details.get('landArea'),
            'property_features': property_details.get('features', []),
            
            # Content
            'headline': listing.get('headline', ''),
            'description': listing.get('summaryDescription', ''),
            'url_slug': listing.get('listingSlug', ''),
            
            # Media
            'media': listing.get('media', []),
            'has_floorplan': listing.get('hasFloorplan', False),
            'has_video': listing.get('hasVideo', False),
            
            # Address
            'address': address,
            
            # Inspection times
            'inspection_schedule': listing.get('inspectionSchedule', {}),
            
            # Metadata
            'raw_data': raw_listing  # Keep the original data for reference
        }

        return processed

    except Exception as e:
        logging.error(f"Error processing listing: {e}")
        return None

@app.get("/api/search-listings/{suburb}")
async def search_listings(suburb: str):
    """Search both active and sold listings by suburb"""
    try:
        # Get access token
        access_token = get_domain_access_token()
        if not access_token:
            return {"error": "Failed to get access token"}

        # API configuration
        url = "https://api.domain.com.au/v1/listings/residential/_search"
        api_key = "key_d05406abc5556a22176546f7283736ac"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }

        async def fetch_listings(status: str) -> list:
            search_criteria = {
                "listingType": "Sale",
                "propertyTypes": ["House", "NewApartments", "ApartmentUnitFlat", "Villa", "Townhouse"],
                "locations": [{
                    "state": "VIC",
                    "suburb": suburb,
                }],
                "pageSize": 100,
                "pageNumber": 1,
                "status": status
            }
            
            # Add date filter for sold properties
            if status == "sold":
                search_criteria["soldDateMin"] = "2025-01-01T00:00:00"
            
            listings = []
            
            while True:
                response = requests.post(url, headers=headers, json=search_criteria)
                
                if response.status_code == 200:
                    data = response.json()
                    if not data:  # No more listings
                        break
                        
                    listings.extend(data)
                    logging.info(f"Fetched {len(data)} {status} listings from page {search_criteria['pageNumber']}")
                    
                    if len(data) < search_criteria['pageSize']:  # Last page
                        break
                        
                    search_criteria['pageNumber'] += 1  # Get next page
                else:
                    error_text = response.text
                    logging.error(f"Domain API error for {status} listings: {error_text}")
                    break
            
            return listings

        # Fetch both active and sold listings in parallel
        active_listings = await fetch_listings("live")
        sold_listings = await fetch_listings("sold")

        # Process and categorize listings
        result = {
            "active_listings": [],
            "sold_listings": [],
            "metadata": {
                "total_active": len(active_listings),
                "total_sold": len(sold_listings),
                "suburb": suburb,
                "state": "VIC",
                "timestamp": datetime.now().isoformat()
            }
        }

        # Process active listings
        for listing in active_listings:
            processed_listing = process_listing(listing)
            if processed_listing:
                result["active_listings"].append(processed_listing)

        # Process sold listings
        for listing in sold_listings:
            processed_listing = process_listing(listing)
            if processed_listing:
                result["sold_listings"].append(processed_listing)

        logging.info(f"Found {len(result['active_listings'])} active and {len(result['sold_listings'])} sold listings in {suburb}")
        return result

    except Exception as e:
        logging.error(f"Error searching listings: {e}")
        return {"error": str(e)}

    except Exception as e:
        logging.error(f"Error searching listings: {e}")
        return {"error": str(e)}

@app.post("/api/save-listings")
async def save_listings(request: Request):
    """Save listings to database"""
    try:
        # Get the listings data from request body
        data = await request.json()
        listings = data.get('listings', [])
        
        if not listings:
            return JSONResponse({"error": "No listings provided"}, status_code=400)
        
        logging.info(f"Received {len(listings)} listings to save")
        
        # Save each listing to database
        saved_count = 0
        for listing in listings:
            try:
                # Transform listing data to match expected structure
                transformed = {
                    'type': 'PropertyListing',
                    'listing': {
                        'id': listing.get('id'),
                        'listingType': listing.get('type'),
                        'status': listing.get('status'),
                        'dateListed': listing.get('dateListed'),
                        'dateUpdated': listing.get('dateUpdated'),
                        'priceDetails': listing.get('priceDetails', {}),
                        'headline': listing.get('headline'),
                        'summaryDescription': listing.get('description'),
                        'listingSlug': listing.get('listingSlug'),
                        'inspectionSchedule': listing.get('inspectionSchedule', []),
                        'propertyDetails': {
                            'propertyType': listing.get('propertyType'),
                            'bedrooms': listing.get('propertyDetails', {}).get('bedrooms'),
                            'bathrooms': listing.get('propertyDetails', {}).get('bathrooms'),
                            'carspaces': listing.get('propertyDetails', {}).get('carspaces'),
                            'landArea': listing.get('propertyDetails', {}).get('landArea'),
                            'features': listing.get('propertyFeatures', [])
                        },
                        'media': listing.get('images', []),
                        'agents': listing.get('agents', []),
                        'advertiser': listing.get('advertiser', {})
                    }
                }
                
                listing_id = listing.get('id')
                logging.info(f"Saving listing {listing_id}")
                
                # Save transformed listing
                save_listing_to_db(transformed)
                saved_count += 1
                logging.info(f"Successfully saved listing {listing_id} to database")
                
            except Exception as e:
                logging.error(f"Error saving listing {listing.get('id')}: {e}")
                continue
        
        success_message = f"Successfully saved {saved_count} listings to database"
        logging.info(success_message)
        
        return JSONResponse({
            "success": True,
            "message": success_message,
            "saved_count": saved_count
        })
        
    except Exception as e:
        error_message = f"Error saving listings: {str(e)}"
        logging.error(error_message)
        return JSONResponse({"error": error_message}, status_code=500)
