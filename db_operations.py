from sqlalchemy.orm import Session
from database import SessionLocal, engine
from datetime import datetime
import json
import logging

def save_listing_to_db(listing_data: dict):
    """Save listing to database with duplicate checking"""
    db = SessionLocal()
    try:
        # Check if listing already exists
        existing_listing = db.execute(
            text("SELECT id FROM listings WHERE domain_listing_id = :listing_id"),
            {"listing_id": str(listing_data.get('id'))}
        ).scalar()
        
        if existing_listing:
            logging.info(f"Listing {listing_data.get('id')} already exists, skipping...")
            return None
            
        # Extract main listing data
        listing = {
            'domain_listing_id': str(listing_data.get('id')),
            'listing_type': listing_data.get('listingType'),
            'status': listing_data.get('status'),
            'date_listed': listing_data.get('dateListed'),
            'date_updated': listing_data.get('dateUpdated'),
            'price': float(listing_data.get('price', 0)),
            'price_display': listing_data.get('priceDetails', {}).get('displayPrice'),
            'headline': listing_data.get('headline'),
            'description': listing_data.get('description'),
            'url_slug': listing_data.get('listingSlug'),
            'inspection_times': json.dumps(listing_data.get('inspectionSchedule', [])),
            'auction_date': listing_data.get('auctionDate'),
            'property_type': listing_data.get('propertyTypes', [{}])[0].get('name')
        }

        # Create or update listing
        result = db.execute("""
            INSERT INTO listings (
                domain_listing_id, listing_type, status, date_listed, date_updated,
                price, price_display, headline, description, url_slug,
                inspection_times, auction_date, property_type
            ) VALUES (
                :domain_listing_id, :listing_type, :status, :date_listed, :date_updated,
                :price, :price_display, :headline, :description, :url_slug,
                :inspection_times::jsonb, :auction_date, :property_type
            )
            ON CONFLICT (domain_listing_id) DO UPDATE SET
                status = EXCLUDED.status,
                date_updated = EXCLUDED.date_updated,
                price = EXCLUDED.price,
                price_display = EXCLUDED.price_display,
                headline = EXCLUDED.headline,
                description = EXCLUDED.description,
                inspection_times = EXCLUDED.inspection_times,
                auction_date = EXCLUDED.auction_date
            RETURNING id
        """, listing)
        listing_id = result.fetchone()[0]

        # Save property details
        property_details = {
            'listing_id': listing_id,
            'bedrooms': listing_data.get('propertyDetails', {}).get('bedrooms'),
            'bathrooms': listing_data.get('propertyDetails', {}).get('bathrooms'),
            'parking_spaces': listing_data.get('propertyDetails', {}).get('parkingSpaces'),
            'land_area': listing_data.get('propertyDetails', {}).get('landArea'),
            'area_unit': listing_data.get('propertyDetails', {}).get('areaUnit'),
            'year_built': listing_data.get('propertyDetails', {}).get('yearBuilt'),
            'energy_rating': listing_data.get('propertyDetails', {}).get('energyRating'),
            'property_features': json.dumps(listing_data.get('propertyFeatures', [])),
            'floor_plans': json.dumps(listing_data.get('floorplans', [])),
            'images': json.dumps(listing_data.get('images', []))
        }

        db.execute("""
            INSERT INTO property_details (
                listing_id, bedrooms, bathrooms, parking_spaces, land_area,
                area_unit, year_built, energy_rating, property_features,
                floor_plans, images
            ) VALUES (
                :listing_id, :bedrooms, :bathrooms, :parking_spaces, :land_area,
                :area_unit, :year_built, :energy_rating, :property_features::jsonb,
                :floor_plans::jsonb, :images::jsonb
            )
            ON CONFLICT (listing_id) DO UPDATE SET
                bedrooms = EXCLUDED.bedrooms,
                bathrooms = EXCLUDED.bathrooms,
                parking_spaces = EXCLUDED.parking_spaces,
                land_area = EXCLUDED.land_area,
                area_unit = EXCLUDED.area_unit,
                year_built = EXCLUDED.year_built,
                energy_rating = EXCLUDED.energy_rating,
                property_features = EXCLUDED.property_features,
                floor_plans = EXCLUDED.floor_plans,
                images = EXCLUDED.images
        """, property_details)

        # Save address
        address = {
            'listing_id': listing_id,
            'street': listing_data.get('addressParts', {}).get('street'),
            'street_number': listing_data.get('addressParts', {}).get('streetNumber'),
            'suburb': listing_data.get('addressParts', {}).get('suburb'),
            'state': listing_data.get('addressParts', {}).get('state'),
            'postcode': listing_data.get('addressParts', {}).get('postcode'),
            'latitude': listing_data.get('geoLocation', {}).get('latitude'),
            'longitude': listing_data.get('geoLocation', {}).get('longitude')
        }

        db.execute("""
            INSERT INTO addresses (
                listing_id, street, street_number, suburb, state,
                postcode, latitude, longitude
            ) VALUES (
                :listing_id, :street, :street_number, :suburb, :state,
                :postcode, :latitude, :longitude
            )
            ON CONFLICT (listing_id) DO UPDATE SET
                street = EXCLUDED.street,
                street_number = EXCLUDED.street_number,
                suburb = EXCLUDED.suburb,
                state = EXCLUDED.state,
                postcode = EXCLUDED.postcode,
                latitude = EXCLUDED.latitude,
                longitude = EXCLUDED.longitude
        """, address)

        # Save agency
        if agency_data := listing_data.get('advertiser', {}):
            agency = {
                'domain_agency_id': str(agency_data.get('id')),
                'name': agency_data.get('name'),
                'logo_url': agency_data.get('logoUrl'),
                'website': agency_data.get('website'),
                'phone': agency_data.get('phone'),
                'email': agency_data.get('email'),
                'address': agency_data.get('address')
            }

            result = db.execute("""
                INSERT INTO agencies (
                    domain_agency_id, name, logo_url, website, phone,
                    email, address
                ) VALUES (
                    :domain_agency_id, :name, :logo_url, :website, :phone,
                    :email, :address
                )
                ON CONFLICT (domain_agency_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    logo_url = EXCLUDED.logo_url,
                    website = EXCLUDED.website,
                    phone = EXCLUDED.phone,
                    email = EXCLUDED.email,
                    address = EXCLUDED.address
                RETURNING id
            """, agency)
            agency_id = result.fetchone()[0]

            # Update listing with agency_id
            db.execute("""
                UPDATE listings SET agency_id = :agency_id
                WHERE id = :listing_id
            """, {'agency_id': agency_id, 'listing_id': listing_id})

        # Save agents
        for agent_data in listing_data.get('agents', []):
            agent = {
                'domain_agent_id': str(agent_data.get('id')),
                'first_name': agent_data.get('firstName'),
                'last_name': agent_data.get('lastName'),
                'email': agent_data.get('email'),
                'mobile': agent_data.get('mobile'),
                'position': agent_data.get('position'),
                'profile_url': agent_data.get('profileUrl'),
                'image_url': agent_data.get('imageUrl')
            }

            result = db.execute("""
                INSERT INTO agents (
                    domain_agent_id, first_name, last_name, email, mobile,
                    position, profile_url, image_url
                ) VALUES (
                    :domain_agent_id, :first_name, :last_name, :email, :mobile,
                    :position, :profile_url, :image_url
                )
                ON CONFLICT (domain_agent_id) DO UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    mobile = EXCLUDED.mobile,
                    position = EXCLUDED.position,
                    profile_url = EXCLUDED.profile_url,
                    image_url = EXCLUDED.image_url
                RETURNING id
            """, agent)
            agent_id = result.fetchone()[0]

            # Link agent to listing
            db.execute("""
                INSERT INTO listing_agents (listing_id, agent_id, is_primary_agent)
                VALUES (:listing_id, :agent_id, :is_primary_agent)
                ON CONFLICT (listing_id, agent_id) DO UPDATE SET
                    is_primary_agent = EXCLUDED.is_primary_agent
            """, {
                'listing_id': listing_id,
                'agent_id': agent_id,
                'is_primary_agent': agent_data.get('isPrimary', False)
            })

        db.commit()
        return listing_id

    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_listings_by_suburb(suburb: str, limit: int = None):
    """Get all listings for a given suburb"""
    db = SessionLocal()
    try:
        query = """
            SELECT 
                l.*,
                pd.*,
                a.*,
                ag.name as agency_name,
                string_agg(CONCAT(agt.first_name, ' ', agt.last_name), '; ') as agent_names
            FROM listings l
            LEFT JOIN property_details pd ON l.id = pd.listing_id
            LEFT JOIN addresses a ON l.id = a.listing_id
            LEFT JOIN agencies ag ON l.agency_id = ag.id
            LEFT JOIN listing_agents la ON l.id = la.listing_id
            LEFT JOIN agents agt ON la.agent_id = agt.id
            WHERE a.suburb = :suburb
            GROUP BY l.id, pd.id, a.id, ag.name
            ORDER BY l.date_updated DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        result = db.execute(query, {'suburb': suburb})
        return result.fetchall()
    finally:
        db.close()
