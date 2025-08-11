# Unit Tests for Weather Forecast App

This directory contains comprehensive unit tests for the simplified Lambda handler implementation.

## Test Coverage

The tests cover all major functionality of the embedded Lambda handler:

### Main Lambda Handler (`TestLambdaHandler`)
- Request routing to different endpoints (`/weather`, `/health`, `/`)
- HTTP method handling (GET, OPTIONS, POST)
- CORS preflight request handling
- Error handling for unknown paths and unsupported methods
- Critical error fallback responses

### Response Helpers (`TestResponseHelpers`)
- Standard response creation with JSON serialization
- Custom header handling
- Error response formatting with timestamps and request IDs

### Weather Data Fetching (`TestWeatherDataFetching`)
- Successful API calls to met.no weather service
- Network error handling and timeout scenarios
- Proper User-Agent header configuration

### Weather Data Processing (`TestWeatherDataProcessing`)
- Tomorrow's forecast extraction from API responses
- Weather condition mapping from symbol codes
- Error handling for invalid or missing data
- Edge cases with empty timeseries

### DynamoDB Caching (`TestDynamoDBCaching`)
- Successful data caching with TTL
- Cache retrieval with hit/miss scenarios
- Expired data handling
- Configuration validation (missing table names)
- Error handling for DynamoDB operations

### City Weather Processing (`TestCityWeatherProcessing`)
- Cache-first processing workflow
- API fallback when cache misses
- Error handling with graceful degradation
- Proper integration between caching and API calls

### Weather Summary (`TestWeatherSummary`)
- Multi-city weather data aggregation
- Error handling for individual city failures
- Rate limiting between API calls (mocked)

### Cities Configuration (`TestCitiesConfiguration`)
- Default city configuration loading
- Custom configuration from environment variables
- JSON parsing error handling and fallback to defaults

### Request Handlers (`TestRequestHandlers`)
- Weather endpoint request processing
- Health check endpoint functionality
- Service error handling and proper HTTP status codes
- Environment variable integration

## Test Architecture

- **Mocking Strategy**: Uses `unittest.mock` to isolate units under test
- **DynamoDB Testing**: Mocks the boto3 DynamoDB client to avoid real AWS calls
- **Environment Variables**: Uses `patch.dict` to test different configurations
- **Error Scenarios**: Comprehensive error handling and edge case coverage
- **Integration Points**: Tests the interaction between different components

## Running Tests

```bash
# Run all unit tests
python -m pytest tests/unit/ -v

# Run specific test class
python -m pytest tests/unit/test_lambda_handler.py::TestDynamoDBCaching -v

# Run with coverage
python -m pytest tests/unit/ --cov=src --cov-report=html
```

## Test Requirements

The tests verify compliance with requirements:
- **2.4**: System testing and validation
- **3.2**: Infrastructure-as-code validation and unit testing

All tests pass and provide comprehensive coverage of the simplified Lambda implementation.