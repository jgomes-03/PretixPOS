import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import { getMountNode, normalizeConfig } from './bootstrap';

const mountNode = getMountNode();

if (!mountNode) {
  throw new Error('Missing #betterpos-app mount node');
}

const config = normalizeConfig();
const root = createRoot(mountNode);

root.render(
  <React.StrictMode>
    <App config={config} />
  </React.StrictMode>
);
