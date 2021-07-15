import * as React from 'react'
import * as ReactDOM from 'react-dom'
import * as Sentry from '@sentry/browser'
import App from './App'
import { config } from './config'

if (config.sentry_uri !== '') {
  Sentry.init({
    dsn: config.sentry_uri,
  })
}

ReactDOM.render(<App />, document.getElementById('root') as HTMLElement)
