export const testTask = {
  id: '1',
  name: 'test task',
  description: 'task description',
  numRuns: 1,
}

export const testDataset = {
  name: 'test dataset',
  id: '1',
  authors: ['test author'],
  url: 'https://example.com',
  summary: 'dataset description',
  tasks: [testTask],
  active: true,
  modality: '',
}

export const testPredictor = {
  id: '1',
  name: 'uploadedPred',
  source: 'collection name',
  description: 'predictor description',
  private: true,
  dataset_id: 1,
}

export const predictorArray = [testPredictor]

export const testPredictorCollection = {
  id: '1',
  collection_name: 'collection name',
  predictors: predictorArray,
}

test('null test for data', () => {
  return undefined
})
