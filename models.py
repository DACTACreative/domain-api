from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Junction table for listings and agents
listing_agents = Table(
    'listing_agents',
    Base.metadata,
    Column('listing_id', Integer, ForeignKey('listings.id'), primary_key=True),
    Column('agent_id', Integer, ForeignKey('agents.id'), primary_key=True),
    Column('is_primary_agent', Integer, default=False)
)

class Listing(Base):
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    domain_listing_id = Column(String, unique=True)
    listing_type = Column(String)  # Sale/Rent
    status = Column(String)  # Current/Sold
    date_listed = Column(DateTime)
    date_updated = Column(DateTime)
    price = Column(Float)
    price_display = Column(String)
    headline = Column(String)
    description = Column(String)
    url_slug = Column(String)
    inspection_times = Column(JSON)
    auction_date = Column(DateTime)
    property_type = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationships
    property_details = relationship("PropertyDetails", back_populates="listing", uselist=False)
    address = relationship("Address", back_populates="listing", uselist=False)
    agency = relationship("Agency", back_populates="listings")
    agents = relationship("Agent", secondary=listing_agents, back_populates="listings")
    sale_history = relationship("SaleHistory", back_populates="listing")

class PropertyDetails(Base):
    __tablename__ = "property_details"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), unique=True)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    parking_spaces = Column(Integer)
    land_area = Column(Float)
    area_unit = Column(String)
    year_built = Column(Integer)
    energy_rating = Column(Float)
    property_features = Column(JSON)  # Array of features
    floor_plans = Column(JSON)  # Array of URLs
    images = Column(JSON)  # Array of URLs
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationship
    listing = relationship("Listing", back_populates="property_details")

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'), unique=True)
    street = Column(String)
    street_number = Column(String)
    suburb = Column(String)
    state = Column(String)
    postcode = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationship
    listing = relationship("Listing", back_populates="address")

class Agency(Base):
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True)
    domain_agency_id = Column(String, unique=True)
    name = Column(String)
    logo_url = Column(String)
    website = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationship
    listings = relationship("Listing", back_populates="agency")

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True)
    domain_agent_id = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    mobile = Column(String)
    position = Column(String)
    profile_url = Column(String)
    image_url = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationship
    listings = relationship("Listing", secondary=listing_agents, back_populates="agents")

class SaleHistory(Base):
    __tablename__ = "sale_history"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey('listings.id'))
    sale_date = Column(DateTime)
    sale_price = Column(Float)
    sale_type = Column(String)
    source = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # Relationship
    listing = relationship("Listing", back_populates="sale_history")
