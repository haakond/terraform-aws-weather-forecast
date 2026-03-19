import React from 'react';
import './Attribution.css';

const Attribution = ({ source, sourceUrl }) => (
  <p className="attribution">
    Data source:{' '}
    <a
      href={sourceUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="attribution__link"
    >
      {source}
    </a>
  </p>
);

export default Attribution;
