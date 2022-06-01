import { Transformation, ReplaceNA } from '../coretypes'

// Todo: Add more transformations, from pybids
// At first, only allow transformations that occur in place
// Include: scale, orthogonalize, threshold

// Later: allow transformations w/ predictable names,
// but need to implement detecting new column names and making them available
// for subsequent transformations.

const transformDefinitions: Transformation[] = [
  {
    Name: 'Scale',
    Demean: true,
    Rescale: true,
    ReplaceNA: 'after' as ReplaceNA,
  },
  {
    Name: 'Threshold',
    Threshold: 0,
    Above: true,
    Binarize: false,
    Signed: true,
  }
]

export default transformDefinitions
