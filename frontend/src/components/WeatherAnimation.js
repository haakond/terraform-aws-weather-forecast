import React from 'react';
import PropTypes from 'prop-types';
import './WeatherAnimation.css';

const KNOWN_CONDITIONS = ['clearsky', 'partlycloudy', 'cloudy', 'rain', 'snow', 'fog', 'thunderstorm'];

const getScene = (condition) =>
  KNOWN_CONDITIONS.includes(condition) ? condition : 'cloudy';

const ClearSkyScene = () => (
  <div className="wa-scene wa-scene--clearsky">
    <div className="wa-sun">
      <div className="wa-sun__core" />
      {[...Array(8)].map((_, i) => (
        <div key={i} className={`wa-sun__ray wa-sun__ray--${i}`} />
      ))}
    </div>
  </div>
);

const PartlyCloudyScene = () => (
  <div className="wa-scene wa-scene--partlycloudy">
    <div className="wa-sun wa-sun--partial">
      <div className="wa-sun__core" />
    </div>
    <div className="wa-cloud wa-cloud--front" />
  </div>
);

const CloudyScene = () => (
  <div className="wa-scene wa-scene--cloudy">
    <div className="wa-cloud wa-cloud--back" />
    <div className="wa-cloud wa-cloud--front" />
  </div>
);

const RainScene = () => (
  <div className="wa-scene wa-scene--rain">
    <div className="wa-cloud wa-cloud--rain" />
    <div className="wa-rain">
      {[...Array(8)].map((_, i) => (
        <div key={i} className={`wa-rain__drop wa-rain__drop--${i}`} />
      ))}
    </div>
  </div>
);

const SnowScene = () => (
  <div className="wa-scene wa-scene--snow">
    <div className="wa-cloud wa-cloud--snow" />
    <div className="wa-snow">
      {[...Array(8)].map((_, i) => (
        <div key={i} className={`wa-snow__flake wa-snow__flake--${i}`} />
      ))}
    </div>
  </div>
);

const FogScene = () => (
  <div className="wa-scene wa-scene--fog">
    {[...Array(4)].map((_, i) => (
      <div key={i} className={`wa-fog__band wa-fog__band--${i}`} />
    ))}
  </div>
);

const ThunderstormScene = () => (
  <div className="wa-scene wa-scene--thunderstorm">
    <div className="wa-cloud wa-cloud--storm" />
    <div className="wa-rain">
      {[...Array(6)].map((_, i) => (
        <div key={i} className={`wa-rain__drop wa-rain__drop--${i}`} />
      ))}
    </div>
    <div className="wa-lightning" />
  </div>
);

const SCENE_MAP = {
  clearsky: ClearSkyScene,
  partlycloudy: PartlyCloudyScene,
  cloudy: CloudyScene,
  rain: RainScene,
  snow: SnowScene,
  fog: FogScene,
  thunderstorm: ThunderstormScene,
};

const WeatherAnimation = ({ condition }) => {
  const scene = getScene(condition);
  const Scene = SCENE_MAP[scene];

  return (
    <div className="weather-animation" aria-hidden="true">
      <Scene />
    </div>
  );
};

WeatherAnimation.propTypes = {
  condition: PropTypes.string,
};

export default WeatherAnimation;
