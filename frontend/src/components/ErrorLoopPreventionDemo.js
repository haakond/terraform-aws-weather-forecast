/**
 * Error Loop Prevention Demo Component
 *
 * This component demonstrates the circuit breaker and error loop prevention
 * safeguards implemented in the useWeatherData hook.
 */

import React, { useState } from 'react';
import { useWeatherData } from '../hooks/useWeatherData';

const ErrorLoopPreventionDemo = () => {
  const [demoMode, setDemoMode] = useState('normal');

  const {
    weatherData,
    loading,
    error,
    retry,
    refresh,
    resetCircuitBreaker,
    resetRateLimit,
    circuitState,
    isCircuitOpen,
    failureCount,
    isRateLimited,
    consecutiveErrors,
    autoRetryDisabled,
    getErrorMessage
  } = useWeatherData();

  const handleDemoModeChange = (mode) => {
    setDemoMode(mode);
    // Reset all safeguards when changing demo mode
    resetCircuitBreaker();
    resetRateLimit();
  };

  const triggerRapidRequests = async () => {
    // Trigger multiple rapid requests to demonstrate rate limiting
    for (let i = 0; i < 5; i++) {
      setTimeout(() => refresh(), i * 100);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h2>Error Loop Prevention Demo</h2>

      <div style={{ marginBottom: '20px' }}>
        <h3>Demo Mode</h3>
        <button
          onClick={() => handleDemoModeChange('normal')}
          style={{
            margin: '5px',
            padding: '10px',
            backgroundColor: demoMode === 'normal' ? '#007bff' : '#f8f9fa',
            color: demoMode === 'normal' ? 'white' : 'black',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        >
          Normal Mode
        </button>
        <button
          onClick={() => handleDemoModeChange('rate-limit')}
          style={{
            margin: '5px',
            padding: '10px',
            backgroundColor: demoMode === 'rate-limit' ? '#007bff' : '#f8f9fa',
            color: demoMode === 'rate-limit' ? 'white' : 'black',
            border: '1px solid #ccc',
            borderRadius: '4px'
          }}
        >
          Rate Limiting Demo
        </button>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Current Status</h3>
        <div style={{
          padding: '15px',
          backgroundColor: '#f8f9fa',
          border: '1px solid #dee2e6',
          borderRadius: '4px',
          fontFamily: 'monospace'
        }}>
          <div><strong>Circuit State:</strong> {circuitState}</div>
          <div><strong>Circuit Open:</strong> {isCircuitOpen ? 'Yes' : 'No'}</div>
          <div><strong>Failure Count:</strong> {failureCount}</div>
          <div><strong>Rate Limited:</strong> {isRateLimited ? 'Yes' : 'No'}</div>
          <div><strong>Consecutive Errors:</strong> {consecutiveErrors}</div>
          <div><strong>Auto-retry Disabled:</strong> {autoRetryDisabled ? 'Yes' : 'No'}</div>
          <div><strong>Loading:</strong> {loading ? 'Yes' : 'No'}</div>
        </div>
      </div>

      {error && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Error Information</h3>
          <div style={{
            padding: '15px',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24'
          }}>
            <div><strong>Error Type:</strong> {error.type}</div>
            <div><strong>Error Message:</strong> {getErrorMessage}</div>
          </div>
        </div>
      )}

      <div style={{ marginBottom: '20px' }}>
        <h3>Actions</h3>
        <button
          onClick={retry}
          disabled={loading}
          style={{
            margin: '5px',
            padding: '10px 15px',
            backgroundColor: '#28a745',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          Manual Retry (Bypasses Safeguards)
        </button>

        <button
          onClick={() => refresh(true)}
          disabled={loading}
          style={{
            margin: '5px',
            padding: '10px 15px',
            backgroundColor: '#17a2b8',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.6 : 1
          }}
        >
          Force Refresh (Bypasses Safeguards)
        </button>

        {demoMode === 'rate-limit' && (
          <button
            onClick={triggerRapidRequests}
            disabled={loading}
            style={{
              margin: '5px',
              padding: '10px 15px',
              backgroundColor: '#ffc107',
              color: 'black',
              border: 'none',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1
            }}
          >
            Trigger Rapid Requests
          </button>
        )}

        <button
          onClick={resetCircuitBreaker}
          style={{
            margin: '5px',
            padding: '10px 15px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reset Circuit Breaker
        </button>

        <button
          onClick={resetRateLimit}
          style={{
            margin: '5px',
            padding: '10px 15px',
            backgroundColor: '#6c757d',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          Reset Rate Limit
        </button>
      </div>

      {weatherData && (
        <div style={{ marginBottom: '20px' }}>
          <h3>Weather Data</h3>
          <div style={{
            padding: '15px',
            backgroundColor: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '4px',
            color: '#155724'
          }}>
            <div><strong>Cities:</strong> {weatherData.cities?.length || 0}</div>
            <div><strong>Last Updated:</strong> {weatherData.lastUpdated || 'Never'}</div>
          </div>
        </div>
      )}

      <div style={{ marginTop: '30px', fontSize: '14px', color: '#6c757d' }}>
        <h4>How to Test Error Loop Prevention:</h4>
        <ol>
          <li><strong>Rate Limiting:</strong> Switch to "Rate Limiting Demo" mode and click "Trigger Rapid Requests" to see rate limiting in action.</li>
          <li><strong>Circuit Breaker:</strong> If the backend is failing, the circuit breaker will open after consecutive failures.</li>
          <li><strong>Manual Override:</strong> Use "Manual Retry" or "Force Refresh" to bypass safeguards when needed.</li>
          <li><strong>Reset Functions:</strong> Use reset buttons to clear safeguard states for testing.</li>
        </ol>
      </div>
    </div>
  );
};

export default ErrorLoopPreventionDemo;