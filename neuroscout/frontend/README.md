## Frontned Development Notes

The frontend app was bootstrapped using create-react-app but with the Typescript option:

`create-react-app frontend --scripts-version=react-scripts-ts`

See these links for more details:
https://github.com/facebookincubator/create-react-app
https://github.com/wmonk/create-react-app-typescript

## Dependencies

Major external libraries used in the frontend app, apart from what comes by default with create-react-app:

- React Router v4 (routing library): https://github.com/ReactTraining/react-router
- Antd (UI component library for React): https://ant.design/docs/react/introduce

Development dependencies:

- Prettier (for autoformatting all ts/tsx/js/jsx files): https://github.com/prettier/prettier

## Setting up the development server 

Install dependencies:
Linux: `sudo apt-get update && sudo apt-get install yarn`
Mac: `brew install yarn`

Navigate to web/frontend:
`cd frontend`

Build frontend dev environment:
`yarn`

Run dev server:
`yarn start`

This should automatically open a browser page at localhost:3000

To build:
`yarn build`

To run the test suite:
`yarn test`

## Code organization

All application state is contained in two main components:

- The top-level component is App (defined in App.tsx), which is responsible for authentication, routing and managing (i.e. listing/cloning/deleting) existing analyses.
- AnalysisBuilder component (Builder.tsx) which is the interface for creating/editing analyses

`coretypes.tsx` contains the type definitinos for most key models, such as analysis, run, predictor, contrast, transformation, etc. The data models in this module are largely UI agonstic. This file is a good starting point to understand the
 shape of the data in the frontend app. All resusable type definitions should go into this module.
