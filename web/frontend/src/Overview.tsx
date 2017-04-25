import * as React from 'react';
import { Form, Input, AutoComplete, Table } from 'antd'
import { TableProps } from "antd/lib/table/Table";

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
  updateAnalysis = (attrName: string) => (event: any) => {
    let newAnalysis = { ...this.props.analysis };
    if (typeof (event) === 'string') {
      newAnalysis[attrName] = event;
    }
    else {
      newAnalysis[attrName] = event.target.value;
    }
    this.props.updateAnalysis(newAnalysis)
  }

  render() {
    const { analysis, datasets, availableRuns } = this.props;
    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Task', dataIndex: 'task' },
      { title: 'Subject', dataIndex: 'subject' },
      { title: 'Session', dataIndex: 'session' }
    ];
    const rowSelection = {
      onSelect: (record, selected, selectedRows) => {
        console.log('Selected rows = ', selectedRows);
        this.updateAnalysis('runIds')(selectedRows.map(x => x.id ))
      }
    }
    return <div>
      <p>Analysis Overview</p>
      <Form layout='vertical'>
        <FormItem label="Analysis name:">
          <Input placeholder="Analysis name"
            value={analysis.analysisName}
            onChange={this.updateAnalysis('analysisName')}
          />
        </FormItem>
        <FormItem label="Description:">
          <Input placeholder="Description of your analysis"
            value={analysis.analysisDescription}
            onChange={this.updateAnalysis('analysisDescription')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>
        <FormItem label="Predictions:">
          <Input placeholder="Enter your preditions about what you expect the results to look like"
            value={analysis.predictions}
            onChange={this.updateAnalysis('predictions')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>

        <FormItem label="Dataset">
          <AutoComplete
            dataSource={datasets.map(item =>
              ({ value: item.id.toString(), text: item.name || item.id.toString() }))} // TODO: stop using id in text once name is included
            placeholder="Type dataset name to search"
            onSelect={this.updateAnalysis('datasetId')}
          />
        </FormItem>
        {availableRuns.length > 0 ?
          <div>
            <p>Select runs:</p>
            <RunTable
              columns={columns}
              rowKey="id"
              dataSource={availableRuns}
              rowSelection={rowSelection} />
          </div>
          : null}
        {/*<FormItem label="Dataset">
          <Select
            mode="tags"
          >
          {this.props.datasets.map((dataset) => 
            <Option key={dataset.value}>{dataset.name}</Option>
          )}
          </Select>
        </FormItem>*/}
      </Form>
    </div>
  }
}