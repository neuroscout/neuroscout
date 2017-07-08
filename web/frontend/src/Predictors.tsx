import * as React from 'react';
import { Table, Input, Button, Row, Col, Tag } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor } from './coretypes';

class PredictorTable extends React.Component<TableProps<any>, any> {
  render() {
    return <Table {...this.props} />;
  }
}

interface PredictorTabProps {
  analysis: Analysis;
  availablePredictors: Predictor[];
  selectedPredictors: Predictor[];
  updateSelectedPredictors: (newPredictors: Predictor[]) => void;
}

interface PredictorsTabState {
  searchText: string;
  filteredPredictors: Predictor[];
}

export class PredictorsTab extends React.Component<PredictorTabProps, PredictorsTabState> {
  state = {
    searchText: '',
    filteredPredictors: this.props.availablePredictors,
    selectedPredictors: this.props.availablePredictors.filter(p => p.id in this.props.analysis.predictorIds)
  };

  onInputChange = (e) => {
    const { availablePredictors } = this.props;
    const searchText: string = e.target.value;
    const searchRegex = new RegExp(searchText.trim(), 'i');
    const newState = { searchText, filteredPredictors: availablePredictors };
    if (searchText.length > 2) {
      newState.filteredPredictors = availablePredictors.filter(
        p => searchRegex.test(p.name + (p.description || '')));
    }
    this.setState(newState);
  }

  removePredictor = (predictorId: string) => {
    const newSelection = this.props.selectedPredictors.filter(p => p.id !== predictorId);
    this.props.updateSelectedPredictors(newSelection);
  }

  render() {
    const { availablePredictors, selectedPredictors, updateSelectedPredictors } = this.props;
    const { filteredPredictors } = this.state;
    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' }
    ];

    const rowSelection: TableRowSelection<Predictor> = {
      onSelect: (record, selected, selectedRows: Predictor[]) => {
        updateSelectedPredictors(selectedRows);
      },
      onSelectAll: (selected, selectedRows: Predictor[], changeRows) => {
        updateSelectedPredictors(selectedRows);
      },
      selectedRowKeys: this.props.analysis.predictorIds
    };

    return (
      <div>
        <Row type="flex">
          <Col span={16}>
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
                rowSelection={rowSelection}
              />
            </div>
          </Col>
          <Col span={4}>
            <p>Selected predictors:</p>
            {selectedPredictors.map(p =>
              <Tag closable={true} onClose={ev => this.removePredictor(p.id)} key={p.id}>{p.name}</Tag>)}
          </Col>
        </Row>
      </div>
    );
  }
}
