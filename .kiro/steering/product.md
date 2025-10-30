# Product Context

Weather forecast web application displaying tomorrow's forecast for Oslo, Paris, London, and Barcelona.

## Architecture
- **Frontend**: Static site on S3 + CloudFront (15min cache, price class 100)
- **Backend**: Python Lambda + API Gateway + DynamoDB (1hr cache)
- **External API**: Norwegian Meteorological Institute (api.met.no)
- **Infrastructure**: Terraform modules, deployed to eu-west-1

## Key Constraints
- Must respect api.met.no Terms of Service (User-Agent required, 20 req/sec max)
- Cache-control: 60s on success, 0s on failure
- Mobile-responsive design required
- CloudFront: GET/HEAD/OPTIONS only, query param caching