/*
 OverviewTab component
*/
import * as React from 'react';
import { Col, Collapse, Form, Icon, Input, Row, Table, Tooltip, Button, List, Descriptions } from 'antd';
import { ColumnProps, TableRowSelection } from 'antd/lib/table';

import { getTasks } from './Builder';
import { Analysis, Dataset, Run, Task } from '../coretypes';
import { datasetColumns } from '../HelperComponents';
import { sortSub, sortNum, sortSes } from '../utils';

const FormItem = Form.Item;
const Panel = Collapse.Panel;

interface OverviewTabProps {
  analysis: Analysis;
  datasets: Dataset[];
  availableRuns: Run[];
  selectedTaskId: string | null;
  predictorsActive: boolean;
  updateAnalysis: (value: any) => void;
  updateSelectedTaskId: (value: string) => void;
}

interface OverviewTabState {
  clearFilteredVal: boolean;
  filteredVal: any[];
  runColumns: ColumnProps<any>[];
  taskMsg: string;
}

export class OverviewTab extends React.Component<OverviewTabProps, OverviewTabState> {

  constructor(props) {
    super(props);
    this.state = {
      clearFilteredVal: false,
      filteredVal: [],
      runColumns: [],
      taskMsg: 'Please Select'
    };
  }

  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  };

  updateAnalysisFromEvent = (attrName: string) =>
    (event: (React.FormEvent<HTMLInputElement> | React.FormEvent<HTMLTextAreaElement>)) => {
      this.updateAnalysis(attrName)(event.currentTarget.value);
    };

  applyFilter = (pagination, filters, sorter) => {
      /* If we have no set filters, but some selected subjects and we change pages then all subjects will
       * be selected. To prevent this we return immediatly if no filters are set.
       */
      if (Object.keys(filters).map((y) => filters[y]).filter((z) => z.length > 0).length === 0) {
        return;
      }
      let newRunIds = this.props.availableRuns.filter(x => x.task === this.props.selectedTaskId);
      let newRunColumns = this.state.runColumns;
      Object.keys(filters).map(key => {
        if (filters[key] === null || filters[key].length === 0) { return; }
        newRunIds = newRunIds.filter((x) => {return filters[key].includes(String(x[key])); });
        newRunColumns = newRunColumns.map((x) => {
          if (x.key === key) {
            let newCol = x;
            newCol.filteredValue = filters[key];
            return newCol;
          }
          return x;
        });
      });
      this.updateAnalysis('runIds')(newRunIds.map(x => x.id));
      this.setState({filteredVal: filters});
  };

  componentDidUpdate(prevProps) {
    if (this.props.analysis.datasetId !== prevProps.analysis.datasetId) {
      this.setState({clearFilteredVal: true});
    }

    if (this.props.availableRuns.length !== prevProps.availableRuns.length) {
      let subCol = this.makeCol('Subject', 'subject', sortSub);
      let runCol = this.makeCol('Run Number', 'number', sortNum);
      let sesCol = this.makeCol('Session', 'session', sortSes);
      let _runColumns = [subCol, runCol, sesCol].filter(x => x !== undefined) as ColumnProps<any>[];
      if (_runColumns[0]) { _runColumns[0].defaultSortOrder = 'ascend' as 'ascend'; }
      if (this.state.clearFilteredVal) {
        _runColumns.map(x => x.filteredValue = []);
      }
      this.setState({runColumns: _runColumns, clearFilteredVal: false});
    }
  }

  /* Run column settings were largely similar, this function creates them.
     The cast to String before sort is to account for run numbers being a
     numeric type.
  */
  makeCol = (title: string, _key: string, sortFn) => {
    let extractKey: string[] = this.props.availableRuns.filter((x) => {
      return (x !== null) && (this.props.analysis.runIds.indexOf(x.id) > -1);
    }).map(x => String(x[_key]));

    let unique = Array.from(
      new Set(extractKey)
    ).sort((a, b) => a.localeCompare(b, undefined, {numeric: true})) as string[];
    unique = unique.filter((x) => (x !== undefined && x !== null && x !== 'null'));

    let col: ColumnProps<any> = {
      title: title,
      dataIndex: _key,
      key: _key,
      sorter: sortFn
    };

    if (unique.length > 0) {
      col.filters = unique.map((x) => {return {'text': x, 'value': x}; });
      col.onFilter = (value, record) => {
        return value === String(record[_key]);
      };

      if (this.props.analysis.runIds.length === this.props.availableRuns.length) {
        col.filteredValue = this.state.filteredVal[_key];
        let newFilteredVal = this.state.filteredVal;
        newFilteredVal[_key] = unique;
        this.setState({filteredVal: newFilteredVal});
      }
    } else {
      return;
    }
    return col;
  };

  clearFilters = () => {
    let newRunCols = this.state.runColumns;
    newRunCols = newRunCols.map((x) => {
      x.filteredValue = [];
      return x;
    });
    this.setState({runColumns: newRunCols});
    this.updateAnalysis('runIds')
      (this.props.availableRuns.map(x => x.id));
  };

  taskColumns = [
    { title: 'Name', dataIndex: 'name', sorter: (a, b) => a.name.localeCompare(b.name)},
    { title: 'Summary', dataIndex: 'summary' },
    {
      title: 'Subjects',
      dataIndex: 'n_subjects',
      sorter: (a, b) => a.numRuns - b.numRuns
    },
    {
      title: 'Runs Per Subject',
      dataIndex: 'n_runs_subject'
    },
    {
      title: 'Avg Run Length',
      dataIndex: 'avg_run_duration',
      render: (text) => text + 's'
    },
    { title: 'TR', dataIndex: 'TR', render: (text) => text + 's'}
  ];

  datasetExpandRow = (record, index, indent, expanded) => {
    let rowData: {title?: string, content: string, span?: number}[] = [
      {'content': record.longDescription ? record.longDescription : 'n/a'},
      {'title': 'Authors', 'content': record.authors.join(', ')},
      {'title': 'Mean Age', 'content': record.meanAge ? record.meanAge.toFixed(1) : 'n/a', 'span': 1},
      {
        'title': 'Percent Female',
        'content': record.percentFemale ? (record.percentFemale * 100).toFixed(1) : 'n/a',
        'span': 4
      },
      {'title': 'References and Links', 'content': (<a href={record.url}>{record.url}</a>)}
    ];

    return (
      <Descriptions column={5} size="small">
        {rowData.map((x, i) =>
          <Descriptions.Item label={x.title} key={i} span={x.span ? x.span : 5}>{x.content}</Descriptions.Item>)}
      </Descriptions>
    );
  }

  render() {
    let {
      analysis,
      datasets,
      availableRuns,
      selectedTaskId,
    } = this.props;

    let availableTasks = getTasks(datasets, analysis.datasetId);

    const selectedDatasetId: string[] = analysis.datasetId ? [analysis.datasetId.toString()] : [];

    const datasetRowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.updateAnalysis('datasetId')(record.id);
      },
      selectedRowKeys: selectedDatasetId,
      columnWidth: '10px'
    };

    const taskRowSelection: TableRowSelection<Task> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.clearFilters();
        this.props.updateSelectedTaskId(record.id);
      },
      selectedRowKeys: selectedTaskId ? [selectedTaskId] : []
    };

    const runRowSelection: TableRowSelection<Run> = {
      type: 'checkbox',
      onSelect: (record, selected, selectedRows: any) => {
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id));
      },
      onSelectAll: (selected, selectedRows: any, changeRows) => {
        if (selected) {
          this.applyFilter(undefined, this.state.filteredVal, undefined);
        } else {
          this.updateAnalysis('runIds')([]);
        }
      },
      selectedRowKeys: analysis.runIds
    };

    // these should be able to live outside of render:
    let runMsg;
    const availableTaskRuns = this.props.availableRuns.filter((r) => r.task === selectedTaskId);
    if (availableTaskRuns.length === 0) {
      runMsg = 'No Task Selected';
    } else if (analysis.runIds.length === availableTaskRuns.length) {
      runMsg = 'Runs: All selected';
    } else {
      runMsg = 'Runs: ' + analysis.runIds.length + '/' + availableTaskRuns.length + ' selected';
    }
    // This one almost could live in state set by task selection function, but the first selectedTaskId
    //  is being set in builder, and doesn't trip the selection function in the table.
    let taskMsg = '';
    if (this.props.selectedTaskId && availableTasks) {
      let tasks = availableTasks.filter((x) => x.id === this.props.selectedTaskId);
      if (tasks.length === 1) {
        taskMsg = tasks[0].name;
      }
    }

    return (
      <div className="builderCol">
        <Form layout="vertical">
          <FormItem label="Analysis name" required={true}>
            <Row type="flex" justify="space-between">
              <Col xs={24}>
                <Input
                  placeholder="You can change this later"
                  value={analysis.name}
                  onChange={this.updateAnalysisFromEvent('name')}
                  required={true}
                  min={1}
                />
              </Col>
            </Row>
          </FormItem>
          <FormItem label="Description">
            <Input.TextArea
              value={analysis.description}
              autosize={{ minRows: 1, maxRows: 10 }}
              onChange={this.updateAnalysisFromEvent('description')}
            />
          </FormItem>
          <FormItem
            label={
              <span>
                Dataset&nbsp;&nbsp;
                <Tooltip title="Choose from a curated set of openly available, naturalistic datasets.">
                  <Icon type="info-circle" />
                </Tooltip>
              </span>
            }
            required={true}
          >
          <Table
            className="selectDataset"
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={datasets.filter((x) => {
              return x.active === true || x.id === this.props.analysis.datasetId;
            })}
            rowSelection={datasetRowSelection}
            pagination={(datasets.length > 10) ? {'position': 'bottom'} : false}
            expandedRowRender={this.datasetExpandRow}
          />
          <br />
          {availableRuns.length > 0 &&
            <div>
            <Collapse accordion={true} bordered={false} defaultActiveKey={['task']}>
              <Panel header={`Task: ${taskMsg}`} key="task">
                  <Table
                    columns={this.taskColumns}
                    rowKey="id"
                    size="small"
                    dataSource={availableTasks}
                    rowSelection={taskRowSelection}
                    pagination={(datasets.length > 10) ? {'position': 'bottom'} : false}
                  />
              </Panel>
              <Panel header={runMsg} key="runs">
                <Table
                  columns={this.state.runColumns}
                  rowKey="id"
                  size="small"
                  dataSource={availableRuns.filter(r => r.task === selectedTaskId).sort(sortSub)}
                  pagination={(availableRuns.length > 10) ? {'position': 'bottom'} : false}
                  rowSelection={runRowSelection}
                  onChange={this.applyFilter}
                />
                <div>
                  <Button onClick={this.clearFilters}>Clear Filters</Button>&nbsp;&nbsp;
                  <Tooltip
                   title={'You can filter runs using the filter icon in each column,\
                    and clear the filters using this button'}
                  >
                    <Icon type="info-circle" />
                  </Tooltip>
                </div>
              </Panel>
            </Collapse>
          </div>}
          </FormItem>
        </Form>
      </div>
    );
  }
}
