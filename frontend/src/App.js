// Weather Forecast App - Main Component
import React, { useEffect } from 'react';
import WeatherDisplay from './components/WeatherDisplay';
import { setupMockApi, shouldUseMockApi } from './services/mockWeatherApi';
import './App.css';

function App() {
  useEffect(() => {
    // Setup mock API for development/testing
    let cleanup = () => {};

    if (shouldUseMockApi()) {
      cleanup = setupMockApi();
    }

    // Cleanup on unmount
    return cleanup;
  }, []);

  return (
    <div className="App">
      <WeatherDisplay />
    </div>
  );
}

export default App;