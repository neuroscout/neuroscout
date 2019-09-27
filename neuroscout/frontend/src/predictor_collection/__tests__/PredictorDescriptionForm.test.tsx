import * as React from 'react';
import { mount } from 'enzyme';

import { PredictorDescriptionForm } from '../PredictorDescriptionForm';
import * as testData from './data';

let testProps = {
  predictors: [testData.testPredictor.name],
  descriptions: [''],
  updateDescription: (x, y) => {}
}

test('PredictorDescriptionForm renders without crashing', () => {
  const wrapper = mount(<PredictorDescriptionForm {...testProps} />);
  // Create new analysis button
  expect(wrapper.text().toLowerCase()).toContain(testData.testPredictor.name);
});
