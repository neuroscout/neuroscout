import * as React from 'react';
import { Form } from '@ant-design/compatible';
import '@ant-design/compatible/assets/index.css';
import { Button, Checkbox, List } from 'antd';

import { api } from '../api';
import { RunFilters } from '../coretypes';

// Is this better than just capitalizing first every call?
const labelLookup = {
  numbers: 'Runs',
  subjects: 'Subjects',
  sessions: 'Sessions'
};

const filtersInit = () => { return {numbers: [], subjects: [], sessions: []}; };

type RunSelectorProps = {
  availableFilters: RunFilters,
  onChange: (any) => void,
  selectedFilters: RunFilters
};

export class RunSelector extends React.Component<RunSelectorProps, {} > {
  constructor(props) {
    super(props);
  }

  listProps: any = {
    grid: { gutter: 1, column: 10 },
    renderItem: item => (<List.Item>{item}</List.Item>)
  };

  onChange = (key) => (value) => {
    let updatedFilters = {...this.props.selectedFilters};
    updatedFilters[key] = value;
    this.props.onChange(updatedFilters);
  };

  changeFunctions = {
    subjects: this.onChange('subjects'),
    numbers: this.onChange('numbers'),
    sessions: this.onChange('sessions')
  };

  selectAll = (key) => () => {
    this.onChange(key)(this.props.availableFilters[key]);
  };

  render() {
    var lists: any[] = [];

    for (var key in this.props.availableFilters) {
      if (this.props.availableFilters[key].length === 0) {
        continue;
      }
      lists.push(
        <div key={key}>
          <h4>
            {labelLookup[key]}:
            <Button
              type="primary"
              size="small"
              onClick={this.selectAll(key)}
              style={{ float: 'right' }}
            >
              All
            </Button>
          </h4>
          <Checkbox.Group
            options={this.props.availableFilters[key]}
            value={this.props.selectedFilters[key]}
            onChange={this.changeFunctions[key]}
          />
        </div>
      );
    }
    return (
      <div>
        {lists}
      </div>
    );
  }
}
