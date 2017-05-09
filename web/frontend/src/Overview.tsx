import * as React from 'react';
import { Form, Input, AutoComplete, Table } from 'antd'
import { TableProps, TableRowSelection } from "antd/lib/table/Table";

const FormItem = Form.Item;

import { Analysis, Dataset, Run } from './commontypes';

// interface RunTableProps extends TableProps<any>{

// }

class RunTable extends React.Component<TableProps<any>, any>{
  render() {
    return <Table {...this.props} />
  }
}

interface OverviewTabProps {
  analysis: Analysis;
  datasets: Dataset[];
  availableRuns: Run[];
  updateAnalysis: (value: any) => void;
}

export class OverviewTab extends React.Component<OverviewTabProps, any>{
  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis)
  }

  updateAnalysisFromEvent = (attrName: string) => (event: any) => {
    this.updateAnalysis(attrName)(event.target.value);
  }

  render() {
    const { analysis, datasets, availableRuns } = this.props;

    const datasetColumns = [
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' },
      { title: 'Author', dataIndex: 'author' },
      { title: 'URL', dataIndex: 'url'}
    ]

    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Task', dataIndex: 'task' },
      { title: 'Subject', dataIndex: 'subject' },
      { title: 'Session', dataIndex: 'session' }
    ];

    const rowSelection: TableRowSelection<Run> = {
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

        <FormItem label="Dataset:">
          <AutoComplete
            dataSource={datasets.map(item =>
              ({ value: item.id.toString(), text: item.name || item.id.toString() }))} // TODO: stop using id in text once name is included
            placeholder="Type dataset name to search"
            onSelect={this.updateAnalysis('datasetId')}
          />
        </FormItem>
        <RunTable 
        columns={datasetColumns}
        rowKey="id"
        dataSource={datasets}
        />
        {availableRuns.length > 0 &&
          <div>
            <p>Select runs:</p>
            <RunTable
              columns={columns}
              rowKey="id"
              pagination={false}
              dataSource={availableRuns}
              rowSelection={rowSelection} />
          </div>
        }
      </Form>
    </div>
  }
}