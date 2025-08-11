# Frontend Retry Logic Implementation

## Problem Solved

The frontend was experiencing infinite retry loops when the backend returned 5xx server errors. This document explains the implemented solution that ensures a maximum of 5 retries with exponential backoff.

## Implementation

### HTTP Client Level Retry (Primary)

**Location**: `src/services/weatherApi.js`

**Configuration**:
```javascript
const API_CONFIG = {
  MAX_RETRIES: 5, // Maximum of 5 retries for 5xx errors
  RETRY_DELAY_BASE: 1000, // 1 second base delay
  TIMEOUT: 10000 // 10 seconds
};
```

**Retry Logic**:
```javascript
// Retries on:
// - Network errors (no status code)
// - 5xx server errors (status >= 500)  
// - 429 rate limiting errors

isRetryableError(error) {
  if (!error.status) return true; // Network error
  if (error.status >= 500) return true; // Server error
  if (error.status === 429) return true; // Rate limited
  return false;
}
```

**Exponential Backoff with Jitter**:
```javascript
getRetryDelay(attempt) {
  return API_CONFIG.RETRY_DELAY_BASE * Math.pow(2, attempt) + Math.random() * 1000;
}

// Retry delays:
// Attempt 0: 1000ms + 0-1000ms jitter = 1-2 seconds
// Attempt 1: 2000ms + 0-1000ms jitter = 2-3 seconds  
// Attempt 2: 4000ms + 0-1000ms jitter = 4-5 seconds
// Attempt 3: 8000ms + 0-1000ms jitter = 8-9 seconds
// Attempt 4: 16000ms + 0-1000ms jitter = 16-17 seconds
```

### Hook Level Retry (Secondary)

**Location**: `src/hooks/useWeatherData.js`

**Configuration**:
```javascript
const HOOK_CONFIG = {
  MAX_AUTO_RETRIES: 2, // Reduced since HTTP client already does 5 retries
  RETRY_INTERVALS: [2000, 5000] // Progressive retry delays
};
```

**Purpose**: Provides application-level retry after HTTP client exhausts all retries.

## Total Retry Behavior

### For 5xx Server Errors:

1. **HTTP Client Level**: Up to 5 immediate retries with exponential backoff
2. **Hook Level**: Up to 2 additional retries with progressive delays (if HTTP client fails)

**Maximum Total Attempts**: 1 initial + 5 HTTP retries + 2 hook retries = 8 attempts

### For 4xx Client Errors:

1. **HTTP Client Level**: No retries (fails immediately)
2. **Hook Level**: No retries (not considered retryable)

**Total Attempts**: 1 attempt only

### For Network Errors:

1. **HTTP Client Level**: Up to 5 retries with exponential backoff
2. **Hook Level**: Up to 2 additional retries with progressive delays

**Maximum Total Attempts**: 8 attempts

## Retry Timeline Example

For a persistent 5xx error, the retry timeline would be:

```
Initial request: 0s
├─ HTTP Retry 1: ~1-2s delay
├─ HTTP Retry 2: ~2-3s delay  
├─ HTTP Retry 3: ~4-5s delay
├─ HTTP Retry 4: ~8-9s delay
├─ HTTP Retry 5: ~16-17s delay
├─ HTTP client gives up: ~30s total
├─ Hook Retry 1: ~2s delay (32s total)
└─ Hook Retry 2: ~5s delay (37s total)
Final failure: ~37s total
```

## Error Handling

### Retryable Errors:
- Network connectivity issues
- DNS resolution failures
- Connection timeouts
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout
- 429 Too Many Requests

### Non-Retryable Errors:
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden
- 404 Not Found
- 422 Unprocessable Entity

## Logging

The retry logic includes comprehensive logging:

```javascript
// HTTP Client Level
console.warn(`Request failed, retrying in ${delay}ms:`, error.message);

// Hook Level  
console.log(`Auto-retrying in ${retryDelay}ms (attempt ${retryCount + 1}/${MAX_AUTO_RETRIES})`);
```

## Cache Interaction

The retry logic respects the caching layer:

- **Cache Hit**: No HTTP requests made, no retries needed
- **Cache Miss**: Full retry logic applies
- **Force Refresh**: Bypasses cache, full retry logic applies

## Testing

The retry logic can be tested by:

1. **Network Simulation**: Disconnect network to trigger network errors
2. **Backend Simulation**: Return 5xx errors from backend
3. **Rate Limiting**: Trigger 429 responses
4. **Manual Testing**: Use browser dev tools to simulate slow/failed requests

## Configuration

The retry behavior can be adjusted by modifying:

```javascript
// In weatherApi.js
const API_CONFIG = {
  MAX_RETRIES: 5,        // Adjust max HTTP retries
  RETRY_DELAY_BASE: 1000, // Adjust base delay
  TIMEOUT: 10000         // Adjust request timeout
};

// In useWeatherData.js  
const HOOK_CONFIG = {
  MAX_AUTO_RETRIES: 2,           // Adjust hook-level retries
  RETRY_INTERVALS: [2000, 5000]  // Adjust hook retry delays
};
```

## Benefits

1. **Prevents Infinite Loops**: Hard limit of 5 HTTP retries + 2 hook retries
2. **Exponential Backoff**: Reduces server load during outages
3. **Jitter**: Prevents thundering herd problems
4. **Smart Error Detection**: Only retries appropriate error types
5. **Comprehensive Logging**: Easy debugging and monitoring
6. **Cache Awareness**: Doesn't retry unnecessarily when data is cached

This implementation ensures robust error handling while preventing the infinite retry loops that were causing issues with 5xx server responses.
