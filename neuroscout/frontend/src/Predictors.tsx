/*
PredictorSelector component used anywhere we need to select among a list of available
predictors. The component includes a table of predictors as well as search box to instantly
filter the table down to predictors whose name or description match the entered search term
*/
import * as React from 'react';
import { Layout, Table, Input, Button, Row, Col, Tag } from 'antd';
import { TableRowSelection } from 'antd/lib/table';
import { Analysis, Predictor } from './coretypes';

/*
class PredictorTable extends React.Component<TableProps<any>, any> {
  render() {
    return <Table {...this.props} />;
  }
}
*/

interface PredictorSelectorProps {
  availablePredictors: Predictor[]; // All available predictors to select from
  selectedPredictors: Predictor[]; // List of predicors selected by the user (when used as a controlled component)
  // Callback to parent component to update selection
  updateSelection: (newPredictors: Predictor[], filteredPredictors: Predictor[]) => void;
  predictorsLoad?: boolean;
  selectedText?: string;
  compact?: boolean;
}

interface PredictorsSelectorState {
  searchText: string;  // Search term entered in search box
  filteredPredictors: Predictor[]; // Subset of available preditors whose name or description match the search term
  selectedPredictors: Predictor[]; // List of selected predictors (when used as an uncontrolled component)
  predictorsLoad?: boolean;
  selectedText?: string;
}

export class PredictorSelector extends React.Component<
  PredictorSelectorProps,
  PredictorsSelectorState
> {
  constructor(props: PredictorSelectorProps) {
    super(props);
    const { availablePredictors, selectedPredictors, predictorsLoad, selectedText } = props;
    this.state = {
      searchText: '',
      filteredPredictors: availablePredictors,
      selectedPredictors,
      predictorsLoad: predictorsLoad,
      selectedText: selectedText ? selectedText : ''
    };
  }

  onInputChange = e => {
    const { availablePredictors } = this.props;
    const searchText: string = e.target.value;
    const searchRegex = new RegExp(searchText.trim(), 'i');
    const newState = { searchText, filteredPredictors: availablePredictors };
    if (searchText.length > 2) {
      newState.filteredPredictors = availablePredictors.filter(p => {
        let targetText = p.name + (p.description || '');
        targetText += ' ' + p.source;
        return searchRegex.test(targetText);
        }
      );
    }
    this.setState(newState);
  };

  // only for use with sidebar showing selected predictors
  removePredictor = (predictorId: string) => {
    const newSelection = this.props.selectedPredictors.filter(p => p.id !== predictorId);
    this.props.updateSelection(newSelection, this.props.selectedPredictors);
  };

  componentWillReceiveProps(nextProps: PredictorSelectorProps) {
    if (this.props.availablePredictors.length !== nextProps.availablePredictors.length) {
      let filteredPredictors = nextProps.availablePredictors;
      filteredPredictors.map(
        (x) => {
          if (!x.description && x.extracted_feature && x.extracted_feature.description) {
            x.description = x.extracted_feature.description;
          }
          if (x.extracted_feature && x.extracted_feature.extractor_name) {
            x.source = x.extracted_feature.extractor_name;
          }
        }
      );
      this.setState({ filteredPredictors: filteredPredictors, searchText: '' });
    }
    this.setState({predictorsLoad: nextProps.predictorsLoad});
  }

  sourceCmp = (a, b) => {
    let x = a.source + a.name;
    let y = b.source + b.name;
    return x.localeCompare(y);
  }

  render() {
    const { availablePredictors, selectedPredictors, updateSelection } = this.props;
    let { filteredPredictors } = this.state;
    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
        width: '35%'
      },
      {
        title: 'Source',
        dataIndex: 'source',
        sorter: this.sourceCmp,
        defaultSortOrder: 'ascend' as 'ascend',
        width: '30%'
      },
      {
        title: 'Description',
        dataIndex: 'description',
        width: '35%'
      }
    ];

    const rowSelection: TableRowSelection<Predictor> = {
      onSelect: (record, selected, selectedRows: Predictor[]) => {
        updateSelection(selectedRows, filteredPredictors);
      },
      onSelectAll: (selected, selectedRows: Predictor[], changeRows) => {
        updateSelection(selectedRows, filteredPredictors);
      },
      selectedRowKeys: selectedPredictors.map(p => p.id)
    };

    if (this.props.compact) {
      return (
        <div>
          <Row type="flex">
            <Col span={24}>
              <div>
                <Input
                  placeholder="Search predictor name or description..."
                  value={this.state.searchText}
                  onChange={this.onInputChange}
                />
                <br />
                <br />
              </div>
              <div>
                <p>{`Select predictors ${this.state.selectedText}(displaying ${filteredPredictors.length}
              out of ${availablePredictors.length} total predictors):`}</p>
                <Table
                  locale={{ emptyText: this.state.searchText ? 'No results found' : 'No data'}}
                  columns={columns}
                  rowKey="id"
                  pagination={false}
                  scroll={{y: 465}}
                  size="small"
                  dataSource={this.state.filteredPredictors}
                  rowSelection={rowSelection}
                  bordered={true}
                  loading={this.state.predictorsLoad}
                />
              </div>
            </Col>
          </Row>
        </div>
      );
    }
    return (
      <div>
        <Row type="flex">
          <Col xl={{span: 18}} lg={{span: 24}}>
            <div>
              <Input
                placeholder="Search predictor name or description..."
                value={this.state.searchText}
                onChange={this.onInputChange}
              />
              <br />
              <br />
            </div>
            <div>
              <p>{`Select predictors ${this.state.selectedText}(displaying ${filteredPredictors.length}
            out of ${availablePredictors.length} total predictors):`}</p>
              <Table
                locale={{ emptyText: this.state.searchText ? 'No results found' : 'No data'}}
                columns={columns}
                rowKey="id"
                pagination={false}
                scroll={{y: 465}}
                size="small"
                dataSource={this.state.filteredPredictors}
                rowSelection={rowSelection}
                bordered={true}
                loading={this.state.predictorsLoad}
              />
            </div>
          </Col>
          <Col xl={{span: 1}}/>
          <Col xl={{span: 5}}>
            <h4>Selected Predictors:</h4>
            {selectedPredictors.map(p =>
              <Tag closable={true} onClose={ev => this.removePredictor(p.id)} key={p.id}>
                {p.name}
              </Tag>
            )}
          </Col>
        </Row>
      </div>
    );
  }
}
