/*
 OverviewTab component
*/
import * as React from 'react';
import { Col, Form, Input, AutoComplete, Row, Table, Tooltip, Switch, Button } from 'antd';
import { ColumnProps, TableRowSelection } from 'antd/lib/table';

const FormItem = Form.Item;
const InputGroup = Input.Group;

import { Analysis, Dataset, Run, Task } from './coretypes';

/*
class DataTable extends React.Component<any> {
  render() {
    return <Table {...this.props} />;
  }
}
*/

interface OverviewTabProps {
  analysis: Analysis;
  datasets: Dataset[];
  availableTasks: Task[];
  availableRuns: Run[];
  selectedTaskId: string | null;
  predictorsActive: boolean;
  updateAnalysis: (value: any) => void;
  updateSelectedTaskId: (value: string) => void;
  goToNextTab: () => void;
}

interface OverviewTabState {
  filteredVal: any[];
  runColumns: ColumnProps<any>[];
}

export class OverviewTab extends React.Component<OverviewTabProps, OverviewTabState> {

  constructor(props) {
    super(props);
    this.state = {
      filteredVal: [],
      runColumns: []
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

  tableChange = (pagination, filters, sorter) => {
    let newRunIds = this.props.availableRuns;
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
    if (this.props.availableRuns.length !== prevProps.availableRuns.length) {
      let subCol = this.makeCol('Subject', 'subject', this.sortSub);
      let runCol = this.makeCol('Run Number', 'number', this.sortNum);
      let sesCol = this.makeCol('Session', 'session', this.sortSes);
      let _runColumns = [subCol, runCol, sesCol].filter(x => x !== undefined) as ColumnProps<any>[];
      if (_runColumns[0]) { _runColumns[0].defaultSortOrder = 'ascend' as 'ascend'; }
      this.setState({runColumns: _runColumns});
    }
  }

  // Number column can be a mixture of ints and strings sometimes, hence the cast to string
  // number is stored as text in postgres, should see about treating it consistently in app
  _sortRuns = (keys, a, b) => {
    for (var i = 0; i < keys.length; i++) {
      let _a = String(a[keys[i]]);
      let _b = String(b[keys[i]]);
      let cmp = _a.localeCompare(_b, undefined, {numeric: true});
      if (cmp !== 0) { return cmp; }
    }
    return 0;
  }

  sortSub = this._sortRuns.bind(null, ['subject', 'number', 'session']);
  sortNum = this._sortRuns.bind(null, ['number', 'subject',  'session']);
  sortSes = this._sortRuns.bind(null, ['session', 'subject', 'number']);

  /* Run column settings were largely similar, this function creates them.
     The cast to String before sort is to account for run numbers being a 
     numeric type. 
  */
  makeCol = (title: string, _key: string, sortFn) => {
    let extractKey: string[] = this.props.availableRuns.filter(x => x !== null).map(x => String(x[_key]));

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
        col.filteredValue = unique;
        /*
        col.filteredValue = this.state.filteredVal[_key];
        let newFilteredVal = this.state.filteredVal;
        newFilteredVal[_key] = unique;
        this.setState({filteredVal: newFilteredVal});
        */
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
    this.updateAnalysis('runIds')([]);
  };
  
  render() {
    let {
      analysis,
      datasets,
      availableTasks,
      availableRuns,
      selectedTaskId,
      goToNextTab,
      predictorsActive,
    } = this.props;
    // tslint:disable-next-line:no-console
    console.log(datasets);

    const datasetColumns = [
      {
        title: 'Name',
        dataIndex: 'name',
        width: 130,
        sorter: (a, b) => a.name.localeCompare(b.name),
        render: (text, record) => <a href={record.url}>{text}</a>,
      },
      { title: 'Description', dataIndex: 'description'},
      { title: 'Author(s)', dataIndex: 'authors', width: 280 },
      // { title: 'URL', dataIndex: 'url', width: 50 }
    ];

    const selectedDatasetId: string[] = analysis.datasetId ? [analysis.datasetId.toString()] : [];

    const datasetRowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.updateAnalysis('datasetId')(record.id);
      },
      // selections: datasetSelections,
      selectedRowKeys: selectedDatasetId
    };

    const taskColumns = [
      { title: 'Name', dataIndex: 'name', sorter: (a, b) => a.name.localeCompare(b.name)},

      { title: 'Summary', dataIndex: 'summary' },
      {
        title: '#Runs',
        dataIndex: 'numRuns',
        sorter: (a, b) => a.numRuns - b.numRuns
      }
    ];

    const taskRowSelection: TableRowSelection<Task> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
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
          this.updateAnalysis('runIds')
            (this.props.availableRuns.filter(r => r.task.id === selectedTaskId).map(x => x.id));
        } else {
          this.updateAnalysis('runIds')([]);
        }
      },
      selectedRowKeys: analysis.runIds
    };

    return (
      <div>
        <Form layout="vertical">
          <FormItem label="Analysis name:">
            <Row type="flex" justify="space-between">
              <Col xs={24} md={21}>
                <Input
                  placeholder="Analysis name"
                  value={analysis.name}
                  onChange={this.updateAnalysisFromEvent('name')}
                />
              </Col>
              <Col md={3}>
                <div className="privateSwitch">
                  <Tooltip title="Should this analysis be private (only visible to you) or public?">
                    <Switch
                      checked={!analysis.private}
                      checkedChildren="Public"
                      unCheckedChildren="Private"
                      onChange={checked => this.updateAnalysis('private')(!checked)}
                    />
                  </Tooltip>
                </div>
              </Col>
            </Row>
          </FormItem>
          <FormItem label="Description:">
            <Input.TextArea
              placeholder="Description of your analysis"
              value={analysis.description}
              autosize={{ minRows: 3, maxRows: 20 }}
              onChange={this.updateAnalysisFromEvent('description')}
            />
          </FormItem>
          <FormItem label="Predictions:">
            <Input.TextArea
              placeholder="Enter your preditions about what you expect the results to look like"
              value={analysis.predictions}
              autosize={{ minRows: 3, maxRows: 20 }}
              onChange={this.updateAnalysisFromEvent('predictions')}
            />
          </FormItem>
          <p>Select a dataset:</p>
          <br />
          <Table
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={datasets}
            rowSelection={datasetRowSelection}
            pagination={(datasets.length > 10) ? {'position': 'bottom'} : false}
          />
          <br />
          {availableRuns.length > 0 &&
            <div>
              <p>Select a task:</p>
              <br />
              <Table
                columns={taskColumns}
                rowKey="id"
                size="small"
                dataSource={availableTasks}
                rowSelection={taskRowSelection}
                pagination={(datasets.length > 20) ? {'position': 'bottom'} : false}
              />
              <br />
            </div>}
          {selectedTaskId &&
            <div>
              <p>Select runs:</p>
              <br />
              <span>
                {`Selected ${ analysis.runIds.length } items`}
              </span>
              <div>
                <Button onClick={this.clearFilters}>Clear Selection</Button>
              </div>
              <Table
                columns={this.state.runColumns}
                rowKey="id"
                size="small"
                dataSource={availableRuns.filter(r => r.task.id === selectedTaskId).sort(this.sortSub)}
                pagination={(availableRuns.length > 20) ? {'position': 'bottom'} : false}
                rowSelection={runRowSelection}
                onChange={this.tableChange}
              />
              <br />
            </div>}
        </Form>
          <Button type="primary" onClick={goToNextTab} disabled={!predictorsActive}>
            Next: Select Predictors
          </Button>
      </div>
    );
  }
}
