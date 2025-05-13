# Domain API Documentation

Welcome to the Domain API documentation. This API provides integration with Domain.com.au's real estate data.

## Quick Start

### Authentication

```python
# Example authentication
import requests

response = requests.post(
    "https://auth.domain.com.au/v1/connect/token",
    data={
        "grant_type": "client_credentials",
        "scope": "api_agencies_read api_listings_read"
    },
    auth=(client_id, client_secret)
)
```

### Available Endpoints

- `GET /`: Welcome message
- `GET /health`: Health check endpoint
- `GET /test-domain`: Test Domain API connection

## API Reference

### Test Domain Connection

```http
GET /test-domain
```

Tests the connection to Domain API by fetching a sample agency.
