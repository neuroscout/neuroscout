import * as React from 'react';
import { Table, Input, Button } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor } from './commontypes';

class PredictorTable extends React.Component<TableProps<any>, any> {
  render() {
    return <Table {...this.props} />;
  }
}

interface PredictorTabProps {
  analysis: Analysis;
  availablePredictors: Predictor[];
  updateAnalysis: (value: any) => void;
}

interface PredictorsTabState {
  searchText: string;
  filteredPredictors: Predictor[];
}

export class PredictorsTab extends React.Component<PredictorTabProps, PredictorsTabState> {
  state = {
    searchText: '',
    filteredPredictors: this.props.availablePredictors
  };

  onInputChange = (e) => {
    const { availablePredictors } = this.props;
    const searchText: string = e.target.value;
    const searchRegex = new RegExp(searchText.trim(), 'i');
    const newState: PredictorsTabState = { searchText, filteredPredictors: availablePredictors };
    if (searchText.length > 2) {
      newState.filteredPredictors = availablePredictors.filter(
        p => searchRegex.test(p.name + (p.description || '')));
    }
    this.setState(newState);
  }

  updateAnalysis = (attrName: keyof Analysis) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  }

  updateAnalysisFromEvent = (attrName: keyof Analysis) => (event: any) => {
    this.updateAnalysis(attrName)(event.target.value);
  }

  render() {
    const { availablePredictors } = this.props;
    const { filteredPredictors } = this.state;
    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' }
    ];

    const rowSelection: TableRowSelection<Predictor> = {
      onSelect: (record, selected, selectedRows: Predictor[]) => {
        this.updateAnalysis('predictorIds')(selectedRows.map(x => x.id));
      },
      onSelectAll: (selected, selectedRows: Predictor[], changeRows) => {
        this.updateAnalysis('predictorIds')(selectedRows.map(x => x.id));
      }
    };

    return (
      <div>
        <div>
          <Input
            placeholder="Search predictor name or description..."
            value={this.state.searchText}
            onChange={this.onInputChange}
          /><br /><br />
        </div>
        <div>
          <p>{`Select predictors (displaying ${filteredPredictors.length} 
            out of ${availablePredictors.length} total predictors):`}</p>
          <PredictorTable
            columns={columns}
            rowKey="id"
            pagination={false}
            size="small"
            dataSource={this.state.filteredPredictors}
            rowSelection={rowSelection} />
        </div>
      </div>
    );
  }
}
