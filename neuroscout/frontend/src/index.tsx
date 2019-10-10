import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as Sentry from '@sentry/browser';
import App from './App';

Sentry.init({dsn: 'https://779d1809d42f48fe8a58a69eece1c9f6@sentry.io/1775913'});

ReactDOM.render(<App />, document.getElementById('root') as HTMLElement);
