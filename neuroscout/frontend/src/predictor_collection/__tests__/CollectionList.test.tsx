import * as React from 'react';
import { mount } from 'enzyme';

import { PredictorCollectionList, CollectionListProps } from '../CollectionList';

import * as testData from './data';

let testProps: CollectionListProps = {
  datasets: [testData.testDataset],
  collections: [testData.testPredictorCollection],
  updateUser: (x) => { null; }
};

test('PredictorCollectionList renders without crashing and looks ok', () => {
  const wrapper = mount(<PredictorCollectionList {...testProps} />);
  // Create new analysis button
  expect(wrapper.text().toLowerCase()).toContain('collection name');
  expect(wrapper.text().toLowerCase()).toContain('uploadedpred');
});
