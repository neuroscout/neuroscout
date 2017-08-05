## Frontned Development Notes

The frontend app was bootstrapped using create-react-app but with the Typescript option:

`create-react-app frontend --scripts-version=react-scripts-ts`

See these links for more details:
https://github.com/facebookincubator/create-react-app
https://github.com/wmonk/create-react-app-typescript

## Setting up the development server

Install dependencies:
Linux: `sudo apt-get update && sudo apt-get install yarn`
Mac: `brew install yarn`

Navigate to neuroscout/frontend:
`cd frontend`

Build frontend dev environment:
`yarn`

Run dev server:
`yarn start`

This should automatically open a browser page at localhost:3000

To build:
`yarn build`
