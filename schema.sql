-- Create tables for Domain API Database

-- Listings table (main table)
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    domain_listing_id VARCHAR(50) UNIQUE,
    listing_type VARCHAR(20),  -- Sale/Rent
    status VARCHAR(20),        -- Current/Sold
    date_listed TIMESTAMP,
    date_updated TIMESTAMP,
    price DECIMAL(12,2),
    price_display VARCHAR(100),
    headline VARCHAR(255),
    description TEXT,
    url_slug VARCHAR(255),
    inspection_times JSONB,    -- Array of inspection times
    auction_date TIMESTAMP,
    property_type VARCHAR(50), -- House/Apartment/etc
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property Details (one-to-one with Listings)
CREATE TABLE property_details (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER UNIQUE REFERENCES listings(id) ON DELETE CASCADE,
    bedrooms INTEGER,
    bathrooms INTEGER,
    parking_spaces INTEGER,
    land_area DECIMAL(10,2),
    area_unit VARCHAR(20),
    year_built INTEGER,
    energy_rating DECIMAL(3,1),
    property_features JSONB,   -- Array of features
    street_number VARCHAR(50),
    unit_number VARCHAR(50),
    street VARCHAR(255),
    suburb VARCHAR(100),
    suburb_id INTEGER,
    postcode VARCHAR(10),
    display_address TEXT,
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Property Details
CREATE TABLE property_details (
    id SERIAL PRIMARY KEY,
    listing_id BIGINT UNIQUE REFERENCES listings(id) ON DELETE CASCADE,
    bathrooms DECIMAL(3,1),
    bedrooms DECIMAL(3,1),
    carspaces DECIMAL(3,1),
    features JSONB,         -- Array of features
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agencies
CREATE TABLE agencies (
    id BIGINT PRIMARY KEY,  -- This is the Domain agency ID
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50),
    website TEXT,
    logo_url TEXT,
    preferred_color_hex VARCHAR(7),
    banner_url TEXT,
    address TEXT,
    suburb VARCHAR(100),
    postcode VARCHAR(10),
    state VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agents
CREATE TABLE agents (
    id BIGINT PRIMARY KEY,  -- This is the Domain agent ID
    agency_id BIGINT REFERENCES agencies(id) ON DELETE CASCADE,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    mobile VARCHAR(50),
    phone VARCHAR(50),
    photo_url TEXT,
    secondary_email VARCHAR(255),
    facebook_url TEXT,
    twitter_url TEXT,
    agent_video TEXT,
    profile_text TEXT,
    google_plus_url TEXT,
    personal_website_url TEXT,
    linkedin_url TEXT,
    profile_url TEXT,
    contact_type_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for Listings and Agents
CREATE TABLE listing_agents (
    listing_id BIGINT REFERENCES listings(id) ON DELETE CASCADE,
    agent_id BIGINT REFERENCES agents(id) ON DELETE CASCADE,
    PRIMARY KEY (listing_id, agent_id)
);

-- Create indexes for better performance
CREATE INDEX idx_listings_suburb ON address_details(suburb);
CREATE INDEX idx_listings_postcode ON address_details(postcode);
CREATE INDEX idx_agencies_name ON agencies(name);
CREATE INDEX idx_agents_name ON agents(first_name, last_name);
CREATE INDEX idx_listing_status ON listings(status);
CREATE INDEX idx_listing_sale_mode ON listings(sale_mode);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to all tables
CREATE TRIGGER update_listings_updated_at
    BEFORE UPDATE ON listings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_address_details_updated_at
    BEFORE UPDATE ON address_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_property_details_updated_at
    BEFORE UPDATE ON property_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agencies_updated_at
    BEFORE UPDATE ON agencies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_agents_updated_at
    BEFORE UPDATE ON agents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
