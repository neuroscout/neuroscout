import * as React from 'react';
import Reactour from 'reactour';
import {
  withRouter
} from 'react-router-dom';

const Tour = withRouter(
  ({ isOpen, closeTour, location: { pathname }, history }) => {
    const steps = [
      {
        content: 'Welcome to Neuroscout. Let\'s go on a tour! You can close this at any time.'
      },
      {
        selector: '.browseMain',
        content: 'You can browse existing analyses, including public ones.'
      },
      {
        selector: '.newAnalysis',
        content: 'Or launch the builder to create a new analysis. Let\'s try it.'
      },
      ...(pathname === '/'
      ? [
          {
            action: () => history.push('/builder')
          }
        ]
      : pathname === '/builder'
      ? [
          {
            selector: '.builderTabs',
            content: 'Welcome to the builder. Here you can create new fMRI model from start to finish. '
          },
          {
            selector: '.selectDataset',
            content: 'Get started by naming your analysis and selecting from the\
             curated set of naturalistic fMRI datasets.'
          }
        ]
        : [])
    ];

    return (
      <Reactour
        steps={steps}
        isOpen={isOpen}
        onRequestClose={closeTour}
        update={pathname}
      />
    );
  }
);

export default Tour;
