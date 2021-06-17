/*
 OverviewTab component
*/
import * as React from 'react'
import { QuestionCircleTwoTone } from '@ant-design/icons'
import {
  Col,
  Collapse,
  Input,
  Row,
  Table,
  Tooltip,
  Button,
  Descriptions,
  Form,
} from 'antd'
import { ColumnType, ColumnProps } from 'antd/lib/table'
import { TableRowSelection, CompareFn } from 'antd/lib/table/interface'

import { getTasks } from './Builder'
import { Analysis, Dataset, Run, RunFilters, Task } from '../coretypes'
import { datasetColumns } from '../HelperComponents'
import { sortSub, sortNum, sortSes } from '../utils'

const FormItem = Form.Item
const Panel = Collapse.Panel

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
  filteredVal: RunFilters
  runColumns: ColumnType<Run>[]
  taskMsg: string
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
    }
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

  applyFilter = (pagination, filters: RunFilters, sorter): void => {
    /* If we have no set filters, but some selected subjects and we change pages then all subjects will
     * be selected. To prevent this we return immediatly if no filters are set.
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
      if (this.state.clearFilteredVal) {
        _runColumns.map(x => (x ? (x.filteredValue = []) : null))
      }
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
        this.props.analysis.runIds.length === this.props.availableRuns.length
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

  datasetExpandRow = (
    record: Dataset,
    index,
    indent,
    expanded,
  ): JSX.Element => {
    const rowData: { title?: string; content: string; span?: number }[] = [
      { content: record.longDescription ? record.longDescription : 'n/a' },
      { title: 'Authors', content: record.authors.join(', ') },
      {
        title: 'Mean Age',
        content: record.meanAge ? record.meanAge.toFixed(1) : 'n/a',
        span: 1,
      },
      {
        title: 'Percent Female',
        content: record.percentFemale
          ? (record.percentFemale * 100).toFixed(1)
          : 'n/a',
        span: 4,
      },
      {
        title: 'References and Links',
        content: `<a href=${record.url}>${record.url}</a>`,
      },
    ]

    return (
      <Descriptions column={5} size="small">
        {rowData.map((x, i) => (
          <Descriptions.Item label={x.title} key={i} span={x.span ? x.span : 5}>
            {x.content}
          </Descriptions.Item>
        ))}
      </Descriptions>
    )
  }

  render() {
    const { analysis, datasets, availableRuns, selectedTaskId } = this.props

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
          this.applyFilter(undefined, this.state.filteredVal, undefined)
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
          <FormItem label="Analysis name" required>
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
            required>
            <Table
              className="selectDataset"
              columns={datasetColumns}
              rowKey="id"
              size="small"
              dataSource={datasets.filter(x => {
                return (
                  x.active === true || x.id === this.props.analysis.datasetId
                )
              })}
              rowSelection={datasetRowSelection}
              pagination={
                datasets.length > 10 ? { position: ['bottomCenter'] } : false
              }
              expandedRowRender={this.datasetExpandRow}
            />
            <br />
            {availableRuns.length > 0 && (
              <div>
                <Collapse
                  accordion
                  bordered={false}
                  defaultActiveKey={['task']}>
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
                      // onChange={this.applyFilter}
                    />
                    <div>
                      <Button onClick={this.clearFilters}>Clear Filters</Button>
                      &nbsp;&nbsp;
                      <Tooltip
                        title={
                          'You can filter runs using the filter icon in each column,\
                    and clear the filters using this button'
                        }>
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
