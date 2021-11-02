import * as React from 'react'
import { QuestionOutlined } from '@ant-design/icons'
import {
  Anchor,
  Button,
  Card,
  Checkbox,
  Collapse,
  Form,
  Input,
  List,
  Row,
  Tabs,
  Table,
  Upload,
  Alert,
} from 'antd'
import { TableRowSelection } from 'antd/lib/table/interface'

import { api } from '../api'
import { Dataset, Run, RunFilters } from '../coretypes'
import { datasetColumns, MainCol } from '../HelperComponents'
import { RunSelector } from './RunSelector'
import { PredictorDescriptionForm } from './PredictorDescriptionForm'
import { FilesAndRunsForm } from './FilesAndRunsForm'

const { Link } = Anchor

/*
  predictors - these are the new predictors extracted from tsv headers
  descriptions - descriptions of new predictors
  filesAndRuns - collection of tsv file contents and the runs they apply to
*/
type AddPredictorsFormState = {
  datasetId: string
  predictors: string[]
  descriptions: string[]
  key: number
  collectionName: string
  filesAndRuns: {
    file?: File
    runFilters: RunFilters
    display: boolean
  }[]
}

type AddPredictorsFormProps = {
  datasets: Dataset[]
  closeModal: () => void
}

type Partial<T> = {
  [P in keyof T]: T[P]
}

type PartialState = Partial<AddPredictorsFormState>

export class AddPredictorsForm extends React.Component<
  AddPredictorsFormProps,
  AddPredictorsFormState
> {
  constructor(props) {
    super(props)
    this.state = {
      datasetId: '',
      filesAndRuns: [
        {
          file: undefined,
          runFilters: { numbers: [], subjects: [], sessions: [] },
          display: false,
        },
      ],
      predictors: [] as string[],
      descriptions: [] as string[],
      key: 1,
      collectionName: '',
    }
  }

  prevTab = () => {
    this.setState({ key: Math.max(this.state.key - 1, 1) })
  }

  nextTab = () => {
    this.setState({ key: Math.min(this.state.key + 1, 3) })
  }

  applyRunFilter = (runs, filter) => {
    const runIds: string[] = []
    for (const filterKey in filter) {
      if (!filter[filterKey]) {
        continue
      }
      const runKey = filterKey.slice(0, -1)
      runs.forEach(run => {
        if (
          filter[filterKey].indexOf(run[runKey]) !== -1 &&
          runIds.indexOf(run.id) === -1
        ) {
          runIds.push(run.id)
        }
      })
    }
    return runIds
  }

  upload = () => {
    const formData: any = new FormData()
    void api
      .getRuns(this.state.datasetId)
      .then(runs => {
        formData.append('dataset_id', this.state.datasetId)
        formData.append('collection_name', this.state.collectionName)
        this.state.filesAndRuns.map(x => {
          if (x.file === undefined) {
            return
          }
          const runIds = this.applyRunFilter(runs, x.runFilters).map(runId =>
            parseInt(runId, 10),
          )
          formData.append('runs', runIds)
          formData.append('event_files', x.file, x.file.name)
        })
        return api.postPredictorCollection(formData)
      })
      .then(ret => {
        if (ret.statusCode && ret.statusCode > 400) {
          if (ret.statusCode === 422) {
            // form issues?
          }
          // need to figure out how to encode actual error message
          // eslint-disable-next-line no-console
          console.log(ret)
        } else {
          this.props.closeModal()
        }
      })

    return
  }

  updateState = (value: PartialState) => {
    if ('predictors' in value) {
      value.predictors = [...this.state.predictors, ...value.predictors]
    }

    if ('descriptions' in value) {
      value.descriptions = [...this.state.descriptions, ...value.descriptions]
    }

    this.setState({ ...value })
  }

  updateDescription = (index: number, value: string) => {
    const descriptions = this.state.descriptions
    if (!(index < descriptions.length && index >= 0)) {
      return
    }
    descriptions[index] = value
    this.setState({ descriptions: descriptions })
  }

  onTabClick = (key: string) => {
    this.setState({ key: parseInt(key, 10) })
  }

  render() {
    const rowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.setState({ datasetId: record.id, key: 2 })
      },
      selectedRowKeys: this.state.datasetId ? [this.state.datasetId] : [],
    }

    return (
      <Tabs
        activeKey={String(this.state.key)}
        onTabClick={newTab => this.onTabClick(newTab)}
      >
        <Tabs.TabPane tab="Select Dataset" key={String(1)}>
          <Alert
            message="Select a dataset for which you want to upload custom predictors."
            type="info"
            showIcon
          />
          <Table
            className="selectDataset"
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={this.props.datasets}
            rowSelection={rowSelection}
            pagination={
              this.props.datasets.length > 10
                ? { position: ['bottomRight'] }
                : false
            }
          />
          <a
            href="https://neuroscout.github.io/neuroscout/faq/#can-i-contribute-my-own-predictors-to-neuroscout"
            target="_blank"
            rel="noreferrer"
          >
            <Button icon={<QuestionOutlined />}>Help</Button>
          </a>
        </Tabs.TabPane>
        <Tabs.TabPane tab="Select Files and Runs" key={String(2)}>
          {this.state.datasetId && (
            <Alert
              message="For each set of runs with the same events (i.e. with same stimuli),
             upload a BIDS compliant TSV events file (e.g. onset, duration, event_1, event_2, etc...)"
              type="info"
              showIcon
            />
          )}
          {this.state.datasetId && (
            <>
              <div className="runSelectorContainer">
                <FilesAndRunsForm
                  datasetId={this.state.datasetId}
                  updateState={this.updateState}
                  collectionName={this.state.collectionName}
                  filesAndRuns={this.state.filesAndRuns}
                />
              </div>
              <Button
                type="primary"
                style={{ margin: '10px 0 0 0', float: 'right' }}
                onClick={this.nextTab}
              >
                Next
              </Button>
            </>
          )}
          {!this.state.datasetId && (
            <Alert
              message="Please select a dataset from the previous tab"
              type="error"
              showIcon
            />
          )}
          <br />
          <a
            href="https://neuroscout.github.io/neuroscout/faq/#can-i-contribute-my-own-predictors-to-neuroscout"
            target="_blank"
            rel="noreferrer"
          >
            <Button icon={<QuestionOutlined />}>Help</Button>
          </a>
        </Tabs.TabPane>
        <Tabs.TabPane tab="Predictor Descriptions" key={String(3)}>
          {this.state.filesAndRuns.length > 0 &&
            this.state.filesAndRuns[0].file !== undefined &&
            this.state.collectionName !== '' && (
              <Alert
                message="Please specify a description for each event column."
                type="info"
                showIcon
              />
            )}
          {this.state.filesAndRuns[0].file !== undefined &&
            this.state.collectionName !== '' && (
              <>
                <PredictorDescriptionForm
                  predictors={this.state.predictors}
                  descriptions={this.state.descriptions}
                  updateDescription={this.updateDescription}
                />
                <Button onClick={this.upload} type="primary">
                  Upload
                </Button>
              </>
            )}
          {this.state.collectionName === '' && (
            <Alert
              message="Please specify a descriptive name for your collection on the previous tab"
              type="error"
              showIcon
            />
          )}
          {this.state.filesAndRuns[0].file === undefined && (
            <Alert
              message="Please select at least one file to upload from the <a onClick={this.prevTab}>previous tab</a>"
              type="error"
              showIcon
            />
          )}
        </Tabs.TabPane>
      </Tabs>
    )
  }
}
