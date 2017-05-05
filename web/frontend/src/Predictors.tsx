import * as React from 'react';
import { Table } from 'antd'
import { TableProps, TableRowSelection } from "antd/lib/table/Table";
import { Analysis, Predictor } from './commontypes';


class PredictorTable extends React.Component<TableProps<any>, any>{
  render() {
    return <Table {...this.props} />
  }
}

interface PredictorTabProps {
  analysis: Analysis;
  availablePredictors: Predictor[];
  updateAnalysis: (value: any) => void;
}

export class PredictorsTab extends React.Component<PredictorTabProps, any>{
  updateAnalysis = (attrName: keyof Analysis) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis)
  }

  updateAnalysisFromEvent = (attrName: keyof Analysis) => (event: any) => {
    this.updateAnalysis(attrName)(event.target.value);
  }

  render() {
    const { availablePredictors } = this.props;
    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' }
    ];

    const rowSelection: TableRowSelection<Predictor> = {
      onSelect: (record, selected, selectedRows: any) => {
        console.log('Selected rows = ', selectedRows);
        this.updateAnalysis('predictorIds')(selectedRows.map(x => x.id))
      },
      onSelectAll: (selected, selectedRows: any, changeRows) => {
        this.updateAnalysis('predictorIds')(selectedRows.map(x => x.id))
      }
    }

    return <div>
      <div>
        <p>Select predictors:</p>
        <PredictorTable
          columns={columns}
          rowKey="id"
          pagination={false}
          dataSource={availablePredictors}
          rowSelection={rowSelection} />
      </div>
    </div>
  }
}
