import * as React from 'react';
import { Form, Input, AutoComplete, Table } from 'antd'
import { TableProps, TableRowSelection } from "antd/lib/table/Table";

const FormItem = Form.Item;

import { Analysis, Dataset, Run, Task } from './commontypes';


class DataTable extends React.Component<TableProps<any>, any>{
  render() {
    return <Table {...this.props} />
  }
}

interface OverviewTabProps {
  analysis: Analysis;
  datasets: Dataset[];
  availableTasks: Task[];
  availableRuns: Run[];
  updateAnalysis: (value) => void;
  updateSelectedTaskId: (value: string) => void;
}

export class OverviewTab extends React.Component<OverviewTabProps, any>{
  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  }

  updateAnalysisFromEvent = (attrName: string) => (event: any) => {
    this.updateAnalysis(attrName)(event.target.value);
  }

  render() {
    const { analysis, datasets, availableTasks, availableRuns } = this.props;

    const datasetColumns = [
      { title: 'Name', dataIndex: 'name', width: 50 },
      { title: 'Description', dataIndex: 'description', width: 300 },
      { title: 'Author(s)', dataIndex: 'authors', width: 100 },
      { title: 'URL', dataIndex: 'url', width: 100 }
    ]

    const datasetRowSelection: TableRowSelection<Dataset> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.updateAnalysis('datasetId')(record.id);
      }
    };

    const taskColumns = [
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' },
      { title: '#Runs', dataIndex: 'numRuns' }
    ]

    const taskRowSelection: TableRowSelection<Task> = {
      type: 'radio',
      onSelect: (record, selected, selectedRows) => {
        this.props.updateSelectedTaskId(record.id);
      }
    }

    const runColumns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Task', dataIndex: 'task' },
      { title: 'Subject', dataIndex: 'subject' },
      { title: 'Session', dataIndex: 'session' }
    ];

    const runRowSelection: TableRowSelection<Run> = {
      type: 'checkbox',
      onSelect: (record, selected, selectedRows: any) => {
        console.log('Selected rows = ', selectedRows);
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id))
      },
      onSelectAll: (selected, selectedRows: any, changeRows) => {
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id))
      }
    }

    return <div>
      <Form layout='vertical'>
        <FormItem label="Analysis name:">
          <Input placeholder="Analysis name"
            value={analysis.analysisName}
            onChange={this.updateAnalysisFromEvent('analysisName')}
          />
        </FormItem>
        <FormItem label="Description:">
          <Input placeholder="Description of your analysis"
            value={analysis.analysisDescription}
            onChange={this.updateAnalysisFromEvent('analysisDescription')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>
        <FormItem label="Predictions:">
          <Input placeholder="Enter your preditions about what you expect the results to look like"
            value={analysis.predictions}
            onChange={this.updateAnalysisFromEvent('predictions')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>

        {/*<FormItem label="Dataset:">
          <AutoComplete
            dataSource={datasets.map(item =>
              ({ value: item.id.toString(), text: item.name || item.id.toString() }))} // TODO: stop using id in text once name is included
            placeholder="Type dataset name to search"
            onSelect={this.updateAnalysis('datasetId')}
          />
        </FormItem>*/}
        <p>Select a dataset:</p>
        <DataTable
          columns={datasetColumns}
          rowKey="id"
          dataSource={datasets}
          rowSelection={datasetRowSelection}
        />
        {availableRuns.length > 0 &&
          <div>
            <p>Select a task:</p>
            <DataTable
              columns={taskColumns}
              rowKey="id"
              dataSource={availableTasks}
              rowSelection={taskRowSelection}
            />
            <p>Select runs:</p>
            <DataTable
              columns={runColumns}
              rowKey="id"
              pagination={false}
              dataSource={availableRuns}
              rowSelection={runRowSelection} />
          </div>
        }
      </Form>
    </div>
  }
}