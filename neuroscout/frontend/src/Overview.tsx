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

export class OverviewTab extends React.Component<OverviewTabProps, any> {
  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  };

  updateAnalysisFromEvent = (attrName: string) => 
    (event: (React.FormEvent<HTMLInputElement> | React.FormEvent<HTMLTextAreaElement>)) => {
      this.updateAnalysis(attrName)(event.currentTarget.value);
    };

  render() {
    const {
      analysis,
      datasets,
      availableTasks,
      availableRuns,
      selectedTaskId,
      goToNextTab,
      predictorsActive
    } = this.props;

    const datasetColumns = [
      {
        title: 'Name',
        dataIndex: 'name',
        width: 100,
        sorter: (a, b) => a.name.localeCompare(b.name)
      },
      { title: 'Description', dataIndex: 'description', width: 100 },
      { title: 'Author(s)', dataIndex: 'authors', width: 100 },
    ];

    const selectedDatasetId: string[] = analysis.datasetId ? [analysis.datasetId.toString()] : [];
    // let datasetSelections: any = [];
    // if (analysis.datasetId) {
    //   datasetSelections = [{
    //     key: analysis.datasetId.toString(),
    //     text: 'Dataset Id',
    //     onSelect: (keys) => {return;}
    //   }]
    // }
    // console.log(`selected data set Id = ${selectedDatasetId}`);
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

      { title: 'Description', dataIndex: 'description' },
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

    const runColumns = [
      {
        title: 'ID',
        dataIndex: 'id',
        defaultOrder: 'ascend' as 'ascend',
        sorter: (a, b) => a.id - b.id
      },
      {
        title: 'Subject',
        dataIndex: 'subject',
        sorter: (a, b) => a.subject.localeCompare(b.subject, undefined, {numeric: true}),
      },
      {
        title: 'Session',
        dataIndex: 'session',
        sorter: (a, b) => a.session.localeCompare(b.session, undefined, {numeric: true}),
      }
    ];

    const runRowSelection: TableRowSelection<Run> = {
      type: 'checkbox',
      onSelect: (record, selected, selectedRows: any) => {
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id));
      },
      onSelectAll: (selected, selectedRows: any, changeRows) => {
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id));
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
              <Table
                columns={runColumns}
                rowKey="id"
                size="small"
                dataSource={availableRuns.filter(r => r.task.id === selectedTaskId)}
                pagination={(availableRuns.length > 20) ? {'position': 'bottom'} : false}
                rowSelection={runRowSelection}
              />
              <br />
            </div>}
        </Form>
        {predictorsActive &&
          <Button type="primary" onClick={goToNextTab}>
            Next: Select Predictors
          </Button>}
      </div>
    );
  }
}
