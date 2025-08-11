# API Documentation

## Weather Forecast API

### Base URL
The API base URL will be provided after deployment via Terraform outputs.

### Endpoints

#### GET /weather
Returns weather forecast data for all configured cities.

**Response:**
```json
{
  "cities": [
    {
      "id": "oslo",
      "name": "Oslo",
      "country": "Norway",
      "forecast": {
        "temperature": -2,
        "condition": "partly_cloudy",
        "description": "Partly cloudy",
        "icon": "partly_cloudy_day"
      }
    }
  ]
}
```

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-14T10:30:00Z"
}
```

## Error Handling

All API endpoints return appropriate HTTP status codes:
- 200: Success
- 400: Bad Request
- 500: Internal Server Error
- 503: Service Unavailable

Error responses include a message field with details about the error.