import {Transformation} from './coretypes';

const transformDefinitions: Transformation[] = [
  {
    name: 'standardize',
    parameters: {
      demean: 'boolean',
      scale: 'boolean'
    }
  },
  {
    name: 'orthogonalize',
    parameters: {
      wrt: 'predictors.id',
      bluetooth: 'boolean'
    }
  }
];

export default transformDefinitions;