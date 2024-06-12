/*
 OverviewTab component
*/
import * as React from 'react'
import { QuestionCircleTwoTone } from '@ant-design/icons'
import { Col, Collapse, Input, Row, Table, Tooltip, Button, Form } from 'antd'
import { ColumnType, ColumnProps } from 'antd/lib/table'
import { TableRowSelection, CompareFn } from 'antd/lib/table/interface'

import { getTasks } from './Builder'
import { Analysis, Dataset, Run, RunFilters, Task } from '../coretypes'
import { datasetColumns } from '../HelperComponents'
import { sortSub, sortNum, sortSes } from '../utils'
import { DatasetDescription } from '../browser/DatasetDetailView'

const FormItem = Form.Item
const Panel = Collapse.Panel

const DatasetDescriptionExpand = (
  record: Dataset,
  index,
  indent,
  string,
): JSX.Element => <DatasetDescription {...record} />

interface OverviewTabProps {
  analysis: Analysis
  datasets: Dataset[]
  availableRuns: Run[]
  selectedTaskId: string | null
  predictorsActive: boolean
  updateAnalysis: (value: Analysis) => void
  updateSelectedTaskId: (value: string) => void
}

interface OverviewTabState {
  clearFilteredVal: boolean
  filteredVal: RunFilters | null
  runColumns: ColumnType<Run>[]
  taskMsg: string
  searchText: string
  datasetDataSource: Dataset[]
}

export class OverviewTab extends React.Component<
  OverviewTabProps,
  OverviewTabState
> {
  constructor(props: OverviewTabProps) {
    super(props)
    this.state = {
      clearFilteredVal: false,
      filteredVal: { numbers: [], subjects: [], sessions: [] },
      runColumns: [] as ColumnType<Run>[],
      taskMsg: 'Please Select',
      searchText: '',
      datasetDataSource: props.datasets.filter(x => x.active),
    }
  }

  onInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.setState({
      searchText: e.target.value,
      datasetDataSource: this.props.datasets.filter(
        x =>
          e.target.value.length < 3 ||
          JSON.stringify(x)
            .toLowerCase()
            .includes(e.target.value.toLowerCase()),
      ),
    })
  }

  updateAnalysis =
    (attrName: keyof Analysis) =>
    (value: Analysis[keyof Analysis]): void => {
      const newAnalysis = { ...this.props.analysis, [attrName]: value }
      this.props.updateAnalysis(newAnalysis)
    }

  updateAnalysisFromEvent =
    (attrName: keyof Analysis) =>
    (
      event:
        | React.FormEvent<HTMLInputElement>
        | React.FormEvent<HTMLTextAreaElement>,
    ): void => {
      this.updateAnalysis(attrName)(event.currentTarget.value)
    }

  applyFilter = (pagination, filters, sorter, extra): void => {
    /* If we have no set filters, but some selected subjects and we change pages then all subjects will
     * be selected. To prevent this we return immediately if no filters are set.
     */
    if (
      Object.keys(filters)
        .map(y => filters[y as keyof RunFilters])
        .filter(z => z.length > 0).length === 0
    ) {
      return
    }
    let newRunIds = this.props.availableRuns.filter(
      x => x.task === this.props.selectedTaskId,
    )
    let newRunColumns = this.state.runColumns
    Object.keys(filters).map(key => {
      if (
        filters[key] === null ||
        filters[key as keyof RunFilters].length === 0
      ) {
        return
      }
      newRunIds = newRunIds.filter(x => {
        return filters[key as keyof RunFilters].includes(String(x[key]))
      })
      newRunColumns = newRunColumns.map(x => {
        if (x.key === key) {
          const newCol = x
          newCol.filteredValue = filters[key as keyof RunFilters]
          return newCol
        }
        return x
      })
    })
    this.updateAnalysis('runIds')(newRunIds.map(x => x.id))
    this.setState({ filteredVal: filters })
  }

  componentDidUpdate(prevProps: OverviewTabProps): void {
    if (this.props.analysis.datasetId !== prevProps.analysis.datasetId) {
      const datasetId = this.props.analysis.datasetId
      if (
        datasetId &&
        !this.state.datasetDataSource.map(x => x.id).includes(datasetId)
      ) {
        const dataset = this.props.datasets.find(x => x.id === datasetId)
        if (dataset) {
          this.setState({
            datasetDataSource: [...this.state.datasetDataSource, dataset],
          })
        }
      }
      this.setState({ clearFilteredVal: true })
    }

    if (
      this.props.availableRuns.length !== prevProps.availableRuns.length ||
      this.props.selectedTaskId !== prevProps.selectedTaskId
    ) {
      const subCol = this.makeCol('Subject', 'subject', sortSub)
      const runCol = this.makeCol('Run Number', 'number', sortNum)
      const sesCol = this.makeCol('Session', 'session', sortSes)
      const _runColumns = [subCol, runCol, sesCol].filter(x => x !== undefined)
      if (_runColumns[0]) {
        _runColumns[0].defaultSortOrder = 'ascend' as const
      }
      _runColumns.map(x => (x ? (x.filteredValue = []) : null))

      this.setState({
        runColumns: _runColumns as ColumnType<Run>[],
        clearFilteredVal: false,
      })
    }
  }

  /* Run column settings were largely similar, this function creates them.
     The cast to String before sort is to account for run numbers being a
     numeric type.
  */
  makeCol = (
    title: string,
    _key: string,
    sortFn: CompareFn<Run>,
  ): ColumnType<Run> | undefined => {
    const extractKey: string[] = this.props.availableRuns
      .filter(x => {
        return x !== null && x.task === this.props.selectedTaskId
      })
      .map(x => String(x[_key]))

    let unique = Array.from(new Set(extractKey)).sort((a, b) =>
      a.localeCompare(b, undefined, { numeric: true }),
    )
    unique = unique.filter(x => x !== undefined && x !== null && x !== 'null')

    const col: ColumnProps<Run> = {
      title: title,
      dataIndex: _key,
      key: _key,
      sorter: sortFn,
    }

    if (unique.length > 0) {
      col.filters = unique.map(x => {
        return { text: x, value: x }
      })
      col.onFilter = (value, record) => {
        return value === String(record[_key])
      }

      if (
        this.props.analysis.runIds.length === this.props.availableRuns.length &&
        this.state.filteredVal
      ) {
        col.filteredValue = this.state.filteredVal[_key as keyof RunFilters]
        const newFilteredVal = this.state.filteredVal
        newFilteredVal[_key] = unique
        this.setState({ filteredVal: newFilteredVal })
      }
    } else {
      return
    }
    return col
  }

  clearFilters = (): void => {
    let newRunCols = this.state.runColumns
    newRunCols = newRunCols.map(x => {
      x.filteredValue = []
      return x
    })
    this.setState({ runColumns: newRunCols })
    this.updateAnalysis('runIds')(this.props.availableRuns.map(x => x.id))
  }

  taskColumns = [
    {
      title: 'Name',
      dataIndex: 'name',
      sorter: (a: Task, b: Task): number => a.name.localeCompare(b.name),
    },
    { title: 'Summary', dataIndex: 'summary' },
    {
      title: 'Subjects',
      dataIndex: 'n_subjects',
      sorter: (a: Task, b: Task): number => a.numRuns - b.numRuns,
    },
    {
      title: 'Runs Per Subject',
      dataIndex: 'n_runs_subject',
    },
    {
      title: 'Avg Run Length',
      dataIndex: 'avg_run_duration',
      render: text => String(text) + 's',
    },
    { title: 'TR', dataIndex: 'TR', render: text => String(text) + 's' },
  ]

  render() {
    const { analysis, datasets, availableRuns, selectedTaskId } = this.props
    const { searchText } = this.state

    const availableTasks = getTasks(datasets, analysis.datasetId)

    const selectedDatasetId: string[] = analysis.datasetId
      ? [analysis.datasetId.toString()]
      : []

    const datasetRowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, _selected, _selectedRows) => {
        this.updateAnalysis('datasetId')(record.id)
      },
      selectedRowKeys: selectedDatasetId,
      columnWidth: '10px',
    }

    const taskRowSelection: TableRowSelection<Task> = {
      type: 'radio',
      onSelect: (record, _selected, _selectedRows) => {
        this.clearFilters()
        this.props.updateSelectedTaskId(record.id)
      },
      selectedRowKeys: selectedTaskId ? [selectedTaskId] : [],
    }

    const runRowSelection: TableRowSelection<Run> = {
      type: 'checkbox',
      onSelect: (_record, _selected, selectedRows) => {
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id))
      },
      onSelectAll: (selected, _selectedRows, _changeRows) => {
        if (selected) {
          this.applyFilter(
            undefined,
            this.state.filteredVal,
            undefined,
            undefined,
          )
        } else {
          this.updateAnalysis('runIds')([])
        }
      },
      selectedRowKeys: analysis.runIds,
    }

    // these should be able to live outside of render:
    let runMsg: string
    const availableTaskRuns = this.props.availableRuns.filter(
      r => r.task === selectedTaskId,
    )
    if (availableTaskRuns.length === 0) {
      runMsg = 'No Task Selected'
    } else if (analysis.runIds.length === availableTaskRuns.length) {
      runMsg = 'Runs: All selected'
    } else {
      runMsg =
        'Runs: ' +
        String(analysis.runIds.length) +
        '/' +
        String(availableTaskRuns.length) +
        ' selected'
    }
    // This one almost could live in state set by task selection function, but the first selectedTaskId
    //  is being set in builder, and doesn't trip the selection function in the table.
    let taskMsg = ''
    if (this.props.selectedTaskId && availableTasks) {
      const tasks = availableTasks.filter(
        x => x.id === this.props.selectedTaskId,
      )
      if (tasks.length === 1) {
        taskMsg = tasks[0].name
      }
    }

    return (
      <div className="builderCol">
        <Form layout="vertical">
          <FormItem label="Name" required>
            <Row justify="space-between">
              <Col xs={24}>
                <Input
                  className="builderAnalysisNameInput"
                  placeholder="You can change this later"
                  value={analysis.name}
                  onChange={this.updateAnalysisFromEvent('name')}
                  min={1}
                />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="Description">
            <Input.TextArea
              className="builderAnalysisDescriptionInput"
              value={analysis.description}
              autoSize={{ minRows: 1, maxRows: 10 }}
              onChange={this.updateAnalysisFromEvent('description')}
            />
          </FormItem>
          <FormItem
            label={
              <span>
                Dataset&nbsp;&nbsp;
                <Tooltip title="Choose from a curated set of openly available, naturalistic datasets.">
                  <QuestionCircleTwoTone />
                </Tooltip>
              </span>
            }
            required
          >
            <Input.Search
              placeholder="Search by dataset or task name..."
              value={this.state.searchText}
              onChange={this.onInputChange}
              className="datasetListSearch"
            />
            <Table
              className="selectDataset"
              columns={datasetColumns}
              rowKey="id"
              size="small"
              dataSource={this.state.datasetDataSource}
              rowSelection={datasetRowSelection}
              pagination={
                datasets.length > 10 ? { position: ['bottomCenter'] } : false
              }
              expandedRowRender={DatasetDescriptionExpand}
            />
            <br />
            {availableRuns.length > 0 && (
              <div>
                <Collapse
                  accordion
                  bordered={false}
                  defaultActiveKey={['task']}
                >
                  <Panel header={`Task: ${taskMsg}`} key="task">
                    <Table
                      className="builderAnalysisTaskSelect"
                      columns={this.taskColumns}
                      rowKey="id"
                      size="small"
                      dataSource={availableTasks}
                      rowSelection={taskRowSelection}
                      pagination={
                        datasets.length > 10
                          ? { position: ['bottomCenter'] }
                          : false
                      }
                    />
                  </Panel>
                  <Panel header={runMsg} key="runs">
                    <Table
                      className="builderAnalysisRunsSelect"
                      columns={this.state.runColumns}
                      rowKey="id"
                      size="small"
                      dataSource={availableRuns
                        .filter(r => String(r.task) === String(selectedTaskId))
                        .sort(sortSub)}
                      pagination={
                        availableRuns.length > 10
                          ? { position: ['bottomCenter'] }
                          : false
                      }
                      rowSelection={runRowSelection}
                      onChange={this.applyFilter}
                    />
                    <div>
                      <Button onClick={this.clearFilters}>Clear Filters</Button>
                      &nbsp;&nbsp;
                      <Tooltip
                        title={
                          'You can filter runs using the filter icon in each column,\
                    and clear the filters using this button'
                        }
                      >
                        <QuestionCircleTwoTone />
                      </Tooltip>
                    </div>
                  </Panel>
                </Collapse>
              </div>
            )}
          </FormItem>
        </Form>
      </div>
    )
  }
}
