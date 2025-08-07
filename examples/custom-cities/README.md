# Custom Cities Example

This example demonstrates how to customize the cities displayed in the Weather Forecast App. Instead of the default European cities (Oslo, Paris, London, Barcelona), this example shows Nordic cities.

## Features

- ✅ Custom city selection (5 Nordic cities in this example)
- ✅ Precise GPS coordinates for accurate weather data
- ✅ Unique city IDs for proper caching
- ✅ Support for 1-10 cities total
- ✅ Automatic coordinate validation

## Configured Cities

This example includes the following Nordic cities:

| City | Country | Coordinates |
|------|---------|-------------|
| Reykjavik | Iceland | 64.1466°N, 21.9426°W |
| Stockholm | Sweden | 59.3293°N, 18.0686°E |
| Copenhagen | Denmark | 55.6761°N, 12.5683°E |
| Helsinki | Finland | 60.1699°N, 24.9384°E |
| Oslo | Norway | 59.9139°N, 10.7522°E |

## Usage

### 1. Quick Deployment

Deploy with the pre-configured Nordic cities:

```bash
# Clone the example
cp -r examples/custom-cities my-nordic-weather-app
cd my-nordic-weather-app

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### 2. Customize Cities

Create your own `terraform.tfvars` file to customize the cities:

```hcl
# terraform.tfvars
project_name = "my-weather-app"
environment  = "demo"
aws_region   = "eu-west-1"

cities_config = [
  {
    id      = "tokyo"
    name    = "Tokyo"
    country = "Japan"
    coordinates = {
      latitude  = 35.6762
      longitude = 139.6503
    }
  },
  {
    id      = "new-york"
    name    = "New York"
    country = "United States"
    coordinates = {
      latitude  = 40.7128
      longitude = -74.0060
    }
  },
  {
    id      = "london"
    name    = "London"
    country = "United Kingdom"
    coordinates = {
      latitude  = 51.5074
      longitude = -0.1278
    }
  }
]
```

### 3. Deploy with Custom Configuration

```bash
terraform plan -var-file="terraform.tfvars"
terraform apply -var-file="terraform.tfvars"
```

## Configuration Guidelines

### City Requirements

Each city must include:
- **id**: Unique identifier (lowercase, alphanumeric, hyphens allowed)
- **name**: Display name for the city
- **country**: Country name
- **coordinates**: Precise GPS coordinates
  - **latitude**: -90 to 90 degrees
  - **longitude**: -180 to 180 degrees

### Best Practices

1. **Unique IDs**: Ensure each city has a unique ID for proper caching
2. **Precise Coordinates**: Use accurate GPS coordinates for best weather data
3. **Reasonable Limits**: Support for 1-10 cities (more cities = longer load times)
4. **Geographic Distribution**: Consider time zones and user locations

### Example City Configurations

#### Major World Cities
```hcl
cities_config = [
  {
    id = "tokyo", name = "Tokyo", country = "Japan"
    coordinates = { latitude = 35.6762, longitude = 139.6503 }
  },
  {
    id = "london", name = "London", country = "United Kingdom"
    coordinates = { latitude = 51.5074, longitude = -0.1278 }
  },
  {
    id = "new-york", name = "New York", country = "United States"
    coordinates = { latitude = 40.7128, longitude = -74.0060 }
  },
  {
    id = "sydney", name = "Sydney", country = "Australia"
    coordinates = { latitude = -33.8688, longitude = 151.2093 }
  }
]
```

#### European Capitals
```hcl
cities_config = [
  {
    id = "berlin", name = "Berlin", country = "Germany"
    coordinates = { latitude = 52.5200, longitude = 13.4050 }
  },
  {
    id = "madrid", name = "Madrid", country = "Spain"
    coordinates = { latitude = 40.4168, longitude = -3.7038 }
  },
  {
    id = "rome", name = "Rome", country = "Italy"
    coordinates = { latitude = 41.9028, longitude = 12.4964 }
  }
]
```

#### US Cities
```hcl
cities_config = [
  {
    id = "san-francisco", name = "San Francisco", country = "United States"
    coordinates = { latitude = 37.7749, longitude = -122.4194 }
  },
  {
    id = "chicago", name = "Chicago", country = "United States"
    coordinates = { latitude = 41.8781, longitude = -87.6298 }
  },
  {
    id = "miami", name = "Miami", country = "United States"
    coordinates = { latitude = 25.7617, longitude = -80.1918 }
  }
]
```

## Validation

The configuration includes automatic validation:

- **Coordinate Ranges**: Latitude (-90 to 90), Longitude (-180 to 180)
- **Unique IDs**: All city IDs must be unique
- **City Count**: Between 1 and 10 cities supported
- **Required Fields**: All fields (id, name, country, coordinates) are required

## Outputs

After deployment, you'll get:

```bash
# View deployment information
terraform output

# Example output:
website_url = "https://d1234567890.cloudfront.net"
api_url = "https://abcd1234.execute-api.eu-west-1.amazonaws.com/prod"
configured_cities = [
  {
    "id" = "reykjavik"
    "name" = "Reykjavik"
    "country" = "Iceland"
  },
  # ... more cities
]
```

## Weather Data Source

All weather data comes from the Norwegian Meteorological Institute (met.no) API:
- **Free and Open**: No API key required
- **High Quality**: Professional meteorological data
- **Global Coverage**: Worldwide weather forecasts
- **Reliable**: Government-operated service

## Cost Considerations

Adding more cities affects costs:
- **Lambda Execution**: More cities = longer processing time
- **DynamoDB Storage**: Each city cached separately
- **API Gateway Requests**: Same cost regardless of city count
- **CloudFront**: Same cost regardless of city count

**Estimated monthly cost for 5 cities**: ~$2-5 USD (depending on traffic)

## Troubleshooting

### Invalid Coordinates
```
Error: All city latitudes must be between -90 and 90 degrees
```
**Solution**: Check your latitude/longitude values are within valid ranges.

### Duplicate City IDs
```
Error: All city IDs must be unique
```
**Solution**: Ensure each city has a unique `id` field.

### Weather Data Issues
If weather data isn't loading for custom cities:
1. Verify coordinates are accurate
2. Check met.no API supports the location
3. Review Lambda logs for API errors

### Performance Issues
If the app loads slowly with many cities:
1. Reduce the number of cities
2. Increase Lambda memory allocation
3. Check DynamoDB caching is working

## Clean Up

```bash
terraform destroy
```

## Next Steps

- Try different city combinations
- Experiment with global city selections
- Monitor costs with different city counts
- Implement additional weather data sources
- Add city-specific customizations