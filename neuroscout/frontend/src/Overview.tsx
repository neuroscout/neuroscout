/*
 OverviewTab component
*/
import * as React from 'react';
import { Form, Input, AutoComplete, Table, Switch, Button } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';

const FormItem = Form.Item;

import { Analysis, Dataset, Run, Task } from './coretypes';

class DataTable extends React.Component<TableProps<any>, any> {
  render() {
    return <Table {...this.props} />;
  }
}

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

  updateAnalysisFromEvent = (attrName: string) => (event: React.FormEvent<HTMLInputElement>) => {
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
      { title: 'Name', dataIndex: 'name', width: 60 },
      { title: 'Description', dataIndex: 'description', width: 300 },
      { title: 'Author(s)', dataIndex: 'authors', width: 100 },
      { title: 'URL', dataIndex: 'url', width: 100 }
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
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' },
      { title: '#Runs', dataIndex: 'numRuns' }
    ];

    const taskRowSelection: TableRowSelection<Task> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.props.updateSelectedTaskId(record.id);
      },
      selectedRowKeys: selectedTaskId ? [selectedTaskId] : []
    };

    const runColumns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Subject', dataIndex: 'subject' },
      { title: 'Session', dataIndex: 'session' }
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
            <Input
              placeholder="Analysis name"
              value={analysis.name}
              onChange={this.updateAnalysisFromEvent('name')}
            />
          </FormItem>
          <FormItem label="Should this analysis be private (only visible to you) or public?">
            <Switch
              checked={analysis.private}
              checkedChildren="Private"
              unCheckedChildren="Public"
              onChange={checked => this.updateAnalysis('private')(checked)}
            />
          </FormItem>
          <FormItem label="Description:">
            <Input
              placeholder="Description of your analysis"
              value={analysis.description}
              onChange={this.updateAnalysisFromEvent('description')}
              type="textarea"
              autosize={{ minRows: 3, maxRows: 20 }}
            />
          </FormItem>
          <FormItem label="Predictions:">
            <Input
              placeholder="Enter your preditions about what you expect the results to look like"
              value={analysis.predictions}
              onChange={this.updateAnalysisFromEvent('predictions')}
              type="textarea"
              autosize={{ minRows: 3, maxRows: 20 }}
            />
          </FormItem>
          <p>Select a dataset:</p>
          <br />
          <DataTable
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={datasets}
            rowSelection={datasetRowSelection}
            pagination={datasets.length > 20}
          />
          <br />
          {availableRuns.length > 0 &&
            <div>
              <p>Select a task:</p>
              <br />
              <DataTable
                columns={taskColumns}
                rowKey="id"
                size="small"
                dataSource={availableTasks}
                rowSelection={taskRowSelection}
                pagination={datasets.length > 20}
              />
              <br />
            </div>}
          {selectedTaskId &&
            <div>
              <p>Select runs:</p>
              <br />
              <DataTable
                columns={runColumns}
                rowKey="id"
                size="small"
                dataSource={availableRuns.filter(r => r.task.id === selectedTaskId)}
                pagination={availableRuns.length > 20}
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
