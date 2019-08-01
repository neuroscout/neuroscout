import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Row, Tabs, Table, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { Dataset, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { RunSelector } from './RunSelector';
import { PredictorDescriptionForm } from  './PredictorDescriptionForm';
import { FilesAndRunsForm } from './FilesAndRunsForm';

/*
  predictors - these are the new predictors extracted from tsv headers
  descriptions - descriptions of new predictors
  filesAndRuns - collection of tsv file contents and the runs they apply to
*/
type AddPredictorsFormState = {
  datasetId: string,
  predictors: string[],
  descriptions: string[],
  key: number,
  collectionName: string
  filesAndRuns: {
    file: string,
    runFilters: RunFilters,
    display: boolean
  }[]
};

type Partial<T> = {
    [P in keyof T]: T[P];
};

type PartialState = Partial<AddPredictorsFormState>;

export class AddPredictorsForm extends React.Component<{datasets: Dataset[]}, AddPredictorsFormState> {
  constructor(props) {
    super(props);
    this.state = {
      datasetId: '',
      filesAndRuns: [],
      predictors: [] as string[],
      descriptions: [] as string[],
      key: 1,
      collectionName: ''
    };
  }

  prevTab = () => {
    this.setState({key: Math.max(this.state.key - 1, 1)});
  };

  nextTab = () => {
    this.setState({key: Math.min(this.state.key + 1, 3)});
  };

  upload = () => {
    return;
  };
  
  updateState = (value: PartialState) => this.setState({ ...value });

  updateDescription = (index: number, value: string) => {
    let descriptions = this.state.descriptions;
    if (!(index < descriptions.length && index >= 0)) {
      return;
    }
    descriptions[index] = value;
    this.setState({ descriptions: descriptions });
  }

  render() {
    const rowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.setState({datasetId: record.id, key: 2});
      },
      selectedRowKeys: this.state.datasetId ? [ this.state.datasetId ] : []
    };

    return (
      <Tabs activeKey={'' + this.state.key}>
        <Tabs.TabPane tab="Select Dataset" key={'' + 1}>
          <Table
            className="selectDataset"
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={this.props.datasets}
            rowSelection={rowSelection}
            pagination={(this.props.datasets.length > 10) ? {'position': 'bottom'} : false}
          />
        </Tabs.TabPane>
        <Tabs.TabPane tab="Select Files and Runs" key={'' + 2}>
        {this.state.datasetId &&
          <>
            <div className="runSelectorContainer">
              <FilesAndRunsForm
                datasetId={this.state.datasetId}
                updateState={this.updateState}
                collectionName={this.state.collectionName}
                filesAndRuns={this.state.filesAndRuns}
              />
            </div>
            <Button onClick={this.prevTab}>Prev</Button>
            <Button onClick={this.nextTab}>Next</Button>
          </>
        }
        </Tabs.TabPane>
        <Tabs.TabPane tab="Predictor Descriptions" key={'' + 3}>
          <PredictorDescriptionForm
            predictors={this.state.predictors}
            descriptions={this.state.descriptions}
            updateDescription={this.updateDescription}
          /> 
          <Button onClick={this.prevTab}>Prev</Button>
          <Button onClick={this.upload} type="primary">Upload</Button>
        </Tabs.TabPane>
      </Tabs>
    );
  }
}
