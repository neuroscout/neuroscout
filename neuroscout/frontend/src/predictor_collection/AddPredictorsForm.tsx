import * as React from 'react';
import { Anchor, Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Row, Tabs, Table, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { Dataset, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { RunSelector } from './RunSelector';
import { PredictorDescriptionForm } from  './PredictorDescriptionForm';
import { FilesAndRunsForm } from './FilesAndRunsForm';

const { Link } = Anchor;

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
    file?: File,
    runFilters: RunFilters,
    display: boolean
  }[]
};

type AddPredictorsFormProps = {
  datasets: Dataset[],
  closeModal: () => void
};

type Partial<T> = {
    [P in keyof T]: T[P];
};

type PartialState = Partial<AddPredictorsFormState>;

export class AddPredictorsForm extends React.Component<AddPredictorsFormProps, AddPredictorsFormState> {
  constructor(props) {
    super(props);
    this.state = {
      datasetId: '',
      filesAndRuns: [{file: undefined, runFilters: {numbers: [], subjects: [], sessions: []}, display: false}],
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

  applyRunFilter = (runs, filter) => {
    let runIds: string[] = [];
    for (var filterKey in filter) {
      if (!filter[filterKey]) {
        continue;
      }
      let runKey = filterKey.slice(0, -1);
      runs.forEach((run) => {
        if (filter[filterKey].indexOf(run[runKey]) !== -1 && runIds.indexOf(run.id) === -1) {
          runIds.push(run.id);
        }
      });
    }
    return runIds;
  };

  upload = () => {
    let formData: any = new FormData();
    api.getRuns(this.state.datasetId).then(runs => {
      formData.append('dataset_id', this.state.datasetId);
      formData.append('collection_name', this.state.collectionName);
      this.state.filesAndRuns.map((x) => {
        if (x.file === undefined) { return; }
        let runIds = this.applyRunFilter(runs, x.runFilters).map(runId => parseInt(runId, 10));
        formData.append('runs', runIds);
        formData.append('event_files', x.file, x.file.name);
      });
      return api.postPredictorCollection(formData);
    }).then(ret => {
      if (ret.statusCode && ret.statusCode > 400) {
        // need to figure out how to encode actual error message
        // tslint:disable-next-line:no-console
        console.log(ret);
      } else {
        this.props.closeModal();
      }
    });

    return;
  };

  updateState = (value: PartialState) => {
    if ('predictors' in value) {
      value.predictors = [...this.state.predictors, ...value.predictors];
    }

    if ('descriptions' in value) {
      value.descriptions = [...this.state.descriptions, ...value.descriptions];
    }

    this.setState({ ...value });
  }

  updateDescription = (index: number, value: string) => {
    let descriptions = this.state.descriptions;
    if (!(index < descriptions.length && index >= 0)) {
      return;
    }
    descriptions[index] = value;
    this.setState({ descriptions: descriptions });
  }

  onTabClick = (key: string) => {
    this.setState({ key: parseInt(key, 10) });
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
      <Tabs
        activeKey={'' + this.state.key}
        onTabClick={newTab => this.onTabClick(newTab)}
      >
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
            <Button type="primary" style={{ margin: '10px 0 0 0', float: 'right' }}onClick={this.nextTab}>Next</Button>
          </>
        }
        {!this.state.datasetId &&
          <div>
          Please select a dataset from the <a onClick={this.prevTab}>previous tab</a>
          </div>
        }
        </Tabs.TabPane>
        <Tabs.TabPane tab="Predictor Descriptions" key={'' + 3}>
        {this.state.filesAndRuns[0].file !== undefined &&
         this.state.collectionName !== undefined &&
          <>
            <PredictorDescriptionForm
              predictors={this.state.predictors}
              descriptions={this.state.descriptions}
              updateDescription={this.updateDescription}
            />
            <Button onClick={this.upload} type="primary">Upload</Button>
          </>
        }
        {this.state.collectionName === undefined &&
          <div>
            Please specify a descriptive name for your collection on the <a onClick={this.prevTab}>previous tab</a>
          </div>
        }
        {this.state.filesAndRuns[0].file === undefined &&
          <div>
            Please select at least one file to upload from the <a onClick={this.prevTab}>previous tab</a>
          </div>
        }
        </Tabs.TabPane>
      </Tabs>
    );
  }
}
