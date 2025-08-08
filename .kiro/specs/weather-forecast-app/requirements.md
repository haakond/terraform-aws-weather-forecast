# Requirements Document

## Introduction

This specification will create a weather forecast application, to be deployed with Terraform on AWS serverless infrastructure.

### Requirement 1

**User Story:** As an end user, I will access a web site which compares the weather forecast for tomorrow for the European cities Oslo (Norway), Paris (France), London (United Kingdom) and Barcelona (Spain).

#### Acceptance Criteria

1. WHEN an end user is accessing the service THEN the system SHALL display a simple web site with a fancy design for the weather forecast for the cities as described in the User Story
2. WHEN an end user is accessing the service THEN the system SHALL be snappy and respond fast
3. WHEN an end user is accessing the service on a mobile device THEN the design SHALL be optimized for display on a small screen
4. WHEN static content is served to end users THEN the system SHALL set Cache-Control headers with Max-Age of 900 seconds (15 minutes) to optimize performance and reduce server load


### Requirement 2

**User Story:** As a developer, my application requirements are as follows:

#### Acceptance Criteria

1. WHEN the weather-forecast-app is generated THEN the system SHALL provide a modern front-end application
2. WHEN the weather-forecast-app is generated THEN the system SHALL look up weather forecasts from https://api.met.no/weatherapi/locationforecast/2.0/documentation and cache the results for 1 hour
3. WHEN the weather-forecast-app is generated THEN the system SHALL respect the Terms of Service defined at https://developer.yr.no/doc/TermsOfService/
4. WHEN the weather-forecast-app is generated THEN the system SHALL be tested


### Requirement 3

**User Story:** As a developer, my cloud infrastructure requirements are as follows:

#### Acceptance Criteria

1. WHEN the infrastructure is generated THEN the codebase SHALL be organized as one, self-contained Terraform module
2. WHEN the infrastructure is generated THEN the system SHALL require basic unit tests and infrastructure-as-code validation to be successful
3. WHEN the infrastructure is deployed THEN the system SHALL create AWS resources with appropriate tags like Service:weather-forecast-app.
4. WHEN the infrastructure is deployed THEN the system SHALL package and deploy the weather-forecast-app code
5. WHEN the infrastructure is deployed THEN the system SHALL provide accessible endpoints for testing
6. WHEN the infrastructure is deployed THEN the system SHALL include required IAM roles and permissions
7. WHEN the infrastructure is deployed THEN the system SHALL output relevant URLs or connection information
8. WHEN the infrastructure is deployed THEN the system SHALL be configured for high availability