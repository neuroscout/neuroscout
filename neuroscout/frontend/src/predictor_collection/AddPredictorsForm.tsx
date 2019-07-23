import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Row, Tabs, Table, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { Dataset, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { RunSelector } from './RunSelector';

const filtersInit = () => { return {numbers: [], subjects: [], sessions: []}; };
const filesAndRunsInit = () => ({file: '', runFilters: filtersInit(), display: false});

type FilesAndRunsFormState = {
  availableFilters: RunFilters,
  filesAndRuns: {
    file: string,
    runFilters: RunFilters,
    display: boolean
  }[],
};

class FilesAndRunsForm extends React.Component<{datasetId: string}, FilesAndRunsFormState> {
  constructor(props) {
    super(props);
    this.state = {
      availableFilters: filtersInit(),
      filesAndRuns: [filesAndRunsInit()]
    };
  }
  
  getRuns = () => {
    api.getRuns(this.props.datasetId).then(runs => {
      let availableFilters = filtersInit();
      for (var key in availableFilters) {
        if (!availableFilters.hasOwnProperty(key)) {
          continue;
        }
        availableFilters[key] = Array.from(
          new Set(
            runs.map(x => '' + x[key.slice(0, -1)])
              .filter(x => !!x && x !== 'null')
              .sort((a, b) => a.localeCompare(b, undefined, {numeric: true})) as string[]
          )
        );
      }
      this.setState({availableFilters: availableFilters });
    });
  };

  componentDidMount() {
    this.getRuns();
  }

  componentDidUpdate(prevProps) {
    if (this.props.datasetId !== prevProps.datasetId && this.props.datasetId !== '') {
      this.getRuns();
    }
  }

  addMore = () => {
    let filesAndRuns = this.state.filesAndRuns;
    // if (filesAndRuns[filesAndRuns.length - 1].file === '') { return; }
    filesAndRuns.push(filesAndRunsInit());
    this.setState({filesAndRuns: filesAndRuns});
  };

  onChange = (index: number) => (key: string) => (value) => {
    let filesAndRuns = this.state.filesAndRuns;
    /* When an empty file is filled out add new empty form
    if (key === 'file' && filesAndRuns[index][key] === '' && value !== '') {
      filesAndRuns.push(filesAndRunsInit());
    }
    */
    filesAndRuns[index][key] = value;
    this.setState({filesAndRuns: filesAndRuns});
  };

  render() {
    let formList: any[] = [];
    this.state.filesAndRuns.forEach((x, i) => {
      formList.push(
        <Form key={i}>
          <Card
            title={(
              <div>
                Select File to Upload:
                <input type="file" onChange={(e) => this.onChange(i)('file')(e.target.value)} />
              </div>
            )}
          >
            {this.state.filesAndRuns[i].display &&
              <>
                <RunSelector
                  availableFilters={this.state.availableFilters}
                  selectedFilters={this.state.filesAndRuns[i].runFilters}
                  onChange={this.onChange(i)('runFilters')}
                />
                <Button onClick={() => this.onChange(i)('display')(false)}>Apply</Button>
              </>
            }
            {!this.state.filesAndRuns[i].display &&
              <Button onClick={() => this.onChange(i)('display')(true)}>Select Runs</Button>
            }
          </Card>
        </Form>
      );
    });

    return (
      <div>
        {formList}
        <Button onClick={this.addMore}>Upload More</Button>
      </div>
    );
  }
}

type AddPredictorsFormState = {
  datasetId: string,
  uploads: {file: string, predictors: string[]}[]
};

export class AddPredictorsForm extends React.Component<{datasets: Dataset[]}, AddPredictorsFormState> {
  constructor(props) {
    super(props);
    this.state = {datasetId: '', uploads: []};
  }

  render() {
    const rowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.setState({datasetId: record.id});
      },
      selectedRowKeys: this.state.datasetId ? [ this.state.datasetId ] : []
    };

    return (
      <Tabs activeKey={this.state.datasetId ? '2' : '1'}>
        <Tabs.TabPane tab="Select Dataset" key={'1'}>
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
        <Tabs.TabPane tab="Select Files and Runs" key={'2'}>
        {this.state.datasetId &&
          <div className="runSelectorContainer">
            <FilesAndRunsForm datasetId={this.state.datasetId} />
          </div>
        }
        </Tabs.TabPane>
      </Tabs>
    );
  }
}
