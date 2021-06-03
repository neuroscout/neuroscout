import * as React from 'react';
import * as ReactDOM from 'react-dom';
import * as Sentry from '@sentry/browser';
import App from './App';

Sentry.init({
    dsn: 'https://96e0d2454fea493e886b3122504e22d3@sentry.io/1776214',
});

ReactDOM.render(<App />, document.getElementById('root') as HTMLElement);
