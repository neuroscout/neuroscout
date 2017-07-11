import * as React from 'react';
import { Table, Input, Button, Row, Col, Tag } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor } from './coretypes';

class PredictorTable extends React.Component<TableProps<any>, any> {
  render() {
    return <Table {...this.props} />;
  }
}

interface PredictorSelectorProps {
  availablePredictors: Predictor[];
  selectedPredictors: Predictor[];
  updateSelection: (newPredictors: Predictor[]) => void;
}

interface PredictorsSelectorState {
  searchText: string;
  filteredPredictors: Predictor[];
  selectedPredictors: Predictor[];
}

export class PredictorSelector extends React.Component<PredictorSelectorProps, PredictorsSelectorState> {
  constructor(props: PredictorSelectorProps) {
    super();
    const { availablePredictors, selectedPredictors } = props;
    this.state = {
      searchText: '',
      filteredPredictors: availablePredictors,
      selectedPredictors
    };
  }

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
    this.props.updateSelection(newSelection);
  }

  componentWillReceiveProps(nextProps: PredictorSelectorProps) {
    if (this.props.availablePredictors.length !== nextProps.availablePredictors.length) {
      this.setState({ filteredPredictors: nextProps.availablePredictors, searchText: '' });
    }
  }
  render() {
    const { availablePredictors, selectedPredictors, updateSelection } = this.props;
    const { filteredPredictors } = this.state;
    const columns = [
      { title: 'ID', dataIndex: 'id' },
      { title: 'Name', dataIndex: 'name' },
      { title: 'Description', dataIndex: 'description' }
    ];

    const rowSelection: TableRowSelection<Predictor> = {
      onSelect: (record, selected, selectedRows: Predictor[]) => {
        updateSelection(selectedRows);
      },
      onSelectAll: (selected, selectedRows: Predictor[], changeRows) => {
        updateSelection(selectedRows);
      },
      selectedRowKeys: selectedPredictors.map(p => p.id),
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
                scroll={{ y: 300 }}
                size="small"
                dataSource={this.state.filteredPredictors}
                rowSelection={rowSelection}
              />
            </div>
          </Col>
          <Col span={1}>
          </Col>
          <Col span={3}>
            <p>Selected predictors:</p>
            {selectedPredictors.map(p =>
              <Tag closable={true} onClose={ev => this.removePredictor(p.id)} key={p.id}>{p.name}</Tag>)}
          </Col>
        </Row>
      </div>
    );
  }
}
