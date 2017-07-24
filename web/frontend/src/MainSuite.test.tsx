import * as React from 'react';
import * as ReactDOM from 'react-dom';
import { shallow, mount } from 'enzyme';
import { moveItem } from './utils';
import { Analysis, Dataset } from './coretypes';
import { OverviewTab } from './Overview';
import AnalysisBuilder from './Builder';
import App from './App';

describe('Test moveItem', () => {
  it('Move up', () => {
    expect(moveItem(['zero', 'one', 'two', 'three'], 2, 'up')).toEqual(['zero', 'two', 'one', 'three']);
  });
  it('Move down', () => {
    expect(moveItem(['zero', 'one', 'two', 'three'], 2, 'down')).toEqual(['zero', 'one', 'three', 'two']);
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
    status: 'DRAFT',
    config: { smoothing: 10, predictorConfigs: {} },
    transformations: [],
  };
  const tab = mount(<OverviewTab
    analysis={analysis}
    datasets={[]}
    availableTasks={[]}
    availableRuns={[]}
    selectedTaskId={null}
    predictorsActive={true}
    updateAnalysis={() => { }}
    updateSelectedTaskId={() => { }}
    goToNextTab={() => { }}
  />);
});

it('Analysis builder renders without errors', () => {
  const wrapper = mount(<AnalysisBuilder
    updatedAnalysis={() => { }}
  />);
  // Expect 7 tabs
  expect(wrapper.find('div[role="tab"]').length).toBe(7);
});

test('App renders without crashing and homepage looks ok', () => {
  const div = document.createElement('div');
  window.localStorage.removeItem('jwt');
  const wrapper = mount(<App />);
  // Create new analysis button
  expect(wrapper.text().toLowerCase()).toContain('create new analysis');
});

test('Homepage has 4 buttons with user is not logged in', () => {
  window.localStorage.removeItem('jwt');
  const wrapper = mount(<App />);
  expect(wrapper.find('button').length).toBe(4);
});

test('Homepage has 3 buttons with user is logged in', () => {
  window.localStorage.setItem('jwt', 'fakeJWT');
  const wrapper = mount(<App />);
  expect(wrapper.find('button').length).toBe(3);
});