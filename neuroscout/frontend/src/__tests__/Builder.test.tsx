/*
 Builder component test suite
*/
import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { shallow } from 'enzyme';
import AnalysisBuilder from '../Builder';

let outputData: any = '';
let storeLog = inputs => (outputData = inputs);
test('console.error on saveanalysis with no name or datasetId', () => {
  // tslint:disable-next-line:no-console
  console.error = jest.fn(storeLog);
  let wrapper: any = shallow(<AnalysisBuilder updatedAnalysis={() => {}} />);
  let instance: any = wrapper.instance();

  instance.saveAnalysis({compile: false})();
  expect(outputData.message).toBe('Analysis cannot be saved without selecting a dataset');

  instance.state.analysis.datasetId = 'fake-id';
  instance.saveAnalysis({compile: false})();
  expect(outputData.message).toBe('Analysis cannot be saved without a name');

  outputData = '';
  instance.state.analysis.name = 'fake-name';
  instance.saveAnalysis({compile: false})();
  expect(outputData).toBe('');

});

test('saveAnalysis does not append replaceNA with no predictors', () => {
  let wrapper: any = shallow(<AnalysisBuilder updatedAnalysis={() => {}} />);
  let instance: any = wrapper.instance();
  let expectedXform = {
    Name: 'Replace',
    Input: ['fake-predictorId'],
    Replace: {'n/a': 0}
  };

  instance.state.analysis.analysisId = 'fake-id';
  instance.state.analysis.datasetId = 'fake-datasetId';
  instance.state.analysis.name = 'fake-name';
  instance.saveAnalysis({compile: true})();
  expect(instance.state.analysis.transformations.length).toBe(0);
});

test('saveAnalysis appends replaceNA', () => {
  let wrapper: any = shallow(<AnalysisBuilder updatedAnalysis={() => {}} />);
  let instance: any = wrapper.instance();
  let expectedXform = {
    Name: 'Replace',
    Input: ['fake-predictorId'],
    Replace: {'n/a': 0}
  };

  instance.state.analysis.analysisId = 'fake-id';
  instance.state.analysis.datasetId = 'fake-datasetId';
  instance.state.analysis.name = 'fake-name';
  instance.state.analysis.predictorIds = ['fake-predictorId'];
  instance.saveAnalysis({compile: true})();
  let res = JSON.stringify(instance.state.analysis.transformations[0]);
  expect(res === JSON.stringify(expectedXform));
});
