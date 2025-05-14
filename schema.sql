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
    floor_plans JSONB,        -- Array of URLs
    images JSONB,             -- Array of URLs
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Addresses (one-to-one with Listings)
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER UNIQUE REFERENCES listings(id) ON DELETE CASCADE,
    street VARCHAR(255),
    street_number VARCHAR(50),
    suburb VARCHAR(100),
    state VARCHAR(50),
    postcode VARCHAR(10),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agencies
CREATE TABLE agencies (
    id SERIAL PRIMARY KEY,
    domain_agency_id VARCHAR(50) UNIQUE,
    name VARCHAR(255),
    logo_url VARCHAR(255),
    website VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agents
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    domain_agent_id VARCHAR(50) UNIQUE,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    mobile VARCHAR(50),
    position VARCHAR(100),
    profile_url VARCHAR(255),
    image_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Junction table for Listings and Agents (many-to-many)
CREATE TABLE listing_agents (
    listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
    agent_id INTEGER REFERENCES agents(id) ON DELETE CASCADE,
    is_primary_agent BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (listing_id, agent_id)
);

-- Sale History (one-to-many with Listings)
CREATE TABLE sale_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER REFERENCES listings(id) ON DELETE CASCADE,
    sale_date TIMESTAMP,
    sale_price DECIMAL(12,2),
    sale_type VARCHAR(50),
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_listings_domain_id ON listings(domain_listing_id);
CREATE INDEX idx_listings_suburb ON addresses(suburb);
CREATE INDEX idx_listings_postcode ON addresses(postcode);
CREATE INDEX idx_listings_price ON listings(price);
CREATE INDEX idx_agents_name ON agents(first_name, last_name);
CREATE INDEX idx_agencies_name ON agencies(name);

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

CREATE TRIGGER update_property_details_updated_at
    BEFORE UPDATE ON property_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addresses_updated_at
    BEFORE UPDATE ON addresses
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

CREATE TRIGGER update_sale_history_updated_at
    BEFORE UPDATE ON sale_history
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
