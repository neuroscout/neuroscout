import { Transformation } from './coretypes';

// Todo: Add more transformations, from pybids
// At first, only allow transformations that occur in place
// Include: scale, orthogonalize, threshold

// Later: allow transformations w/ predictable names,
// but need to implement detecting new column names and making them available
// for subsequent transformations.

const transformationSchema = {
  title: 'Transformation Schema',
  type: 'array',
  items: {
    type: 'object',
    properties: {
      name: { enum: ['scale', 'orthogonalize'] },
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
    Name: 'Scale',
    Demean: true,
    Rescale: true,
  },
  {
    Name: 'Orthogonalize',
    Other: []
  },
  {
    Name: 'Sum',
    Weights: []
  },
  {
   Name: 'Product'
  },
  {
    Name: 'Threshold',
    Threshold: 0,
    Above: true,
    Signed: true
  },
  {
    Name: 'Or'
  },
  {
    Name: 'And'
  },
  {
    Name: 'Not'
  },
  {
    Name: 'Replace',
    Replace: {}
  }

];

export default transformDefinitions;
