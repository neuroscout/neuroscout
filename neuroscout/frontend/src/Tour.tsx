import * as React from 'react';
import Reactour from 'reactour';
import {
  withRouter
} from 'react-router-dom';

const Tour = withRouter(
  ({ isOpen, closeTour, location: { pathname }, history }) => {
    const steps = [
      {
        content: 'Welcome to Neuroscout. Lets get oriented the interface.'
      },
      {
        selector: '.browseMain',
        content: 'You can browse existing analyses, including public ones.'
      },
      {
        selector: '.newAnalysis',
        content: 'Or launch the builder to create a new analysis'
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
            content: 'Welcome to the builder. Here you can create an analysis from start to finish. '
          },
          {
            selector: '.selectDataset',
            content: 'First, get started by selecting from one or curated set of naturalistic fMRI datasets'
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
