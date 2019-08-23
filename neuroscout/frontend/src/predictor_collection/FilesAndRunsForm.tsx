import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Row, Tabs, Table, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { Dataset, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { RunSelector } from './RunSelector';

const filtersInit = () => { return {numbers: [], subjects: [], sessions: []}; };
const filesAndRunsInit = () => ({file: undefined, runFilters: filtersInit(), display: false});

type FilesAndRunsFormState = {
  availableFilters: RunFilters,
};

type FilesAndRunsFormProps = {
  datasetId: string,
  updateState: (value) => void,
  collectionName: string,
  filesAndRuns: {
    file?: File,
    runFilters: RunFilters,
    display: boolean
  }[]

};

function _empty(filters) {
  for (let x in filters) {
    if (filters[x].length) {
      return false;
    }
  }
  return true;
}

export class FilesAndRunsForm extends React.Component<FilesAndRunsFormProps, FilesAndRunsFormState> {
  constructor(props) {
    super(props);
    this.state = {
      availableFilters: filtersInit()
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
    let filesAndRuns = this.props.filesAndRuns;
    // if (filesAndRuns[filesAndRuns.length - 1].file === '') { return; }
    filesAndRuns.map(x => x.display = _empty(x.runFilters));
    filesAndRuns.push(filesAndRunsInit());
    this.props.updateState({filesAndRuns: filesAndRuns});
  };

  remove = (index: number) => () => {
    let filesAndRuns = this.props.filesAndRuns.filter((x, i) => i !== index);
    this.props.updateState({filesAndRuns: filesAndRuns});
  };

  parseContents = (evt: any) => {
    if (evt && evt.target && evt.target.result) {
      let contents = evt.target.result;
      let rows = contents.split('\n');
      let headers = rows[0].trim().split('\t');
      /* should warnd here if onset and duration not present, upload will fail */
      headers = headers.filter(x => x !== 'onset' && x !== 'duration');
      this.props.updateState({predictors: headers, descriptions: Array(headers.length).fill('')});
    }
  };

  onChange = (index: number) => (key: string) => (value) => {
    let filesAndRuns = this.props.filesAndRuns;
    if (key === 'file' && filesAndRuns[index][key] === undefined && value !== undefined) {
      let reader = new FileReader();
      reader.onload = this.parseContents;
      reader.readAsText(value);
      /*
        When an empty file is filled out add new empty form
        filesAndRuns.push(filesAndRunsInit());
      */
      filesAndRuns[index].display = true;
    }
    filesAndRuns[index][key] = value;
    this.props.updateState({filesAndRuns: filesAndRuns});
  };

  render() {
    let formList: any[] = [];
    this.props.filesAndRuns.forEach((x, i) => {
      let fileName = 'No File'; 
      if (x.file && x.file.name) {
        fileName = x.file.name;
      }
      formList.push(
        <Form key={i}>
          {this.props.filesAndRuns[i].display &&
          <Card
            title={(
              <div>
                Select File to Upload
                <input
                  type="file"
                  onChange={(e) => {
                    if (e && e.target && e.target.files && e.target.files[0]) {
                      this.onChange(i)('file')(e.target.files[0]);
                    }
                  }}
                />
              </div>
            )}
            extra={<Icon type="close" onClick={this.remove(i)} />}
          >
            {this.props.filesAndRuns[i].display &&
              <>
                <RunSelector
                  availableFilters={this.state.availableFilters}
                  selectedFilters={this.props.filesAndRuns[i].runFilters}
                  onChange={this.onChange(i)('runFilters')}
                />
                <Button
                  className="runSelectorBtn"
                  type="primary"
                  onClick={() => this.onChange(i)('display')(false)}
                >
                  Ok
                </Button>
              </>
            }
          </Card>
          }
          {!this.props.filesAndRuns[i].display &&
            <>
              <span>{fileName}</span>
              <Button style={{margin: '0 0 0 10px'}} onClick={() => this.onChange(i)('display')(true)}>
                <Icon type="edit" /> Edit
              </Button>
            </>
          }
        </Form>
      );
    });

    return (
      <div>
        <Form>
          <Form.Item label="Collection Name">
            <Input
              onChange={(e) => this.props.updateState({collectionName: e.target.value})}
              value={this.props.collectionName}
            />
          </Form.Item>
        </Form>
        {formList}
        <Button style={{margin: '10px 0 0 0'}} onClick={this.addMore}><Icon type="plus" /> Add Event File</Button>
      </div>
    );
  }
}
