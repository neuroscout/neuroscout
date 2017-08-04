import { Transformation } from './coretypes';

const trasnformationSchema = {
  title: 'Transformation Schema',
  type: 'array',
  items: {
    type: 'object',
    properties: {
      name: { enum: ['standardize', 'orthogonalize'] },
      parameters: {
        type: 'array',
        items: {
          name: { type: 'string' },
          kind: { type: 'boolean' },
          value: {
            anyOf: [{ type: 'boolean' }, { type: 'array' }]
          }
        }
      }
    }
  }
};

const transformDefinitions: Transformation[] = [
  {
    name: 'standardize',
    parameters: [
      {
        name: 'demean',
        kind: 'boolean',
        value: false // default value
      },
      {
        name: 'scale',
        kind: 'boolean',
        value: true // default value
      }
    ]
  },
  {
    name: 'orthogonalize',
    parameters: [
      {
        name: 'wrt',
        kind: 'predictors',
        value: []
      }
    ]
  }
];

export default transformDefinitions;
