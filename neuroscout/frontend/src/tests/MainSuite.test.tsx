/*
 Main frontend test suite
*/
import * as React from 'react';
import { BrowserRouter }  from 'react-router-dom';
import { mount } from 'enzyme';
import { moveItem } from '../utils';
import { Analysis } from '../coretypes';
import { OverviewTab } from '../analysis_builder/Overview';
import AnalysisBuilder from '../analysis_builder/Builder';
import App from '../App';

describe('Test moveItem', () => {
  it('Move up', () => {
    expect(moveItem(['zero', 'one', 'two', 'three'], 2, 'up')).toEqual([
      'zero',
      'two',
      'one',
      'three'
    ]);
  });
  it('Move down', () => {
    expect(moveItem(['zero', 'one', 'two', 'three'], 2, 'down')).toEqual([
      'zero',
      'one',
      'three',
      'two'
    ]);
  });
});

it('Overview tab renders without errors', () => {
  const analysis: Analysis = {
    analysisId: undefined,
    name: 'Test analysis',
    description: 'This is just a test',
    predictions: 'Rainy',
    runIds: [],
    datasetId: null,
    predictorIds: [],
    hrfPredictorIds: [],
    status: 'DRAFT',
    config: { smoothing: 10, predictorConfigs: {} },
    transformations: [],
    contrasts: [],
    dummyContrast: true
  };
  mount(
    <OverviewTab
      analysis={analysis}
      datasets={[]}
      availableRuns={[]}
      selectedTaskId={null}
      predictorsActive={true}
      updateAnalysis={() => {}}
      updateSelectedTaskId={() => {}}
    />
  );
});

it('Analysis builder renders without errors', () => {
  const wrapper = mount(<BrowserRouter><AnalysisBuilder updatedAnalysis={() => {}} /></BrowserRouter>);
  // Expect 7 tabs
  expect(wrapper.find('div[role="tab"]').length).toBe(7);
});

test('App renders without crashing and homepage looks ok', () => {
  document.createElement('div');
  window.localStorage.removeItem('jwt');
  const wrapper = mount(<App />);
  // Create new analysis button
  expect(wrapper.text().toLowerCase()).toContain('neuroscout');
  expect(wrapper.text().toLowerCase()).toContain('sign up');
  expect(wrapper.text().toLowerCase()).toContain('sign in');
});

test('Homepage has 1 buttons with user is not logged in', () => {
  window.localStorage.removeItem('jwt');
  const wrapper = mount(<App />);
  expect(wrapper.find('button').length).toBe(1);
});
