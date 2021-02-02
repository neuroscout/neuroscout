/*
PredictorSelector component used anywhere we need to select among a list of available
predictors. The component includes a table of predictors as well as search box to instantly
filter the table down to predictors whose name or description match the entered search term
*/
import * as React from 'react';
import { Table, Input, Row, Col, Tag } from 'antd';
import { TableRowSelection } from 'antd/lib/table/interface';

import isEqual from 'lodash.isequal';
import memoize from 'memoize-one';

import { Predictor } from '../coretypes';

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
  selectedText?: string;
}

export class PredictorSelector extends React.Component<
  PredictorSelectorProps,
  PredictorsSelectorState
> {
  constructor(props: PredictorSelectorProps) {
    super(props);
    const { availablePredictors, selectedPredictors, selectedText } = props;
    this.state = {
      searchText: '',
      filteredPredictors: availablePredictors,
      selectedPredictors,
      selectedText: selectedText ? selectedText : ''
    };
  }

  onInputChange = e => {
    this.setState({ searchText: e.target.value });
  };

  // only for use with sidebar showing selected predictors
  removePredictor = (predictorId: string) => {
    const newSelection = this.props.selectedPredictors.filter(p => p.id !== predictorId);
    this.props.updateSelection(newSelection, this.props.selectedPredictors);
  };

  searchFilter = memoize((searchText, filteredPredictors) => {
    const searchRegex = new RegExp(searchText.trim(), 'i');
    // const newState = { searchText, filteredPredictors: availablePredictors };
    if (searchText.length > 2) {
      return filteredPredictors.filter(p => {
        let targetText = p.name + (p.description || '');
        targetText += ' ' + p.source;
        return searchRegex.test(targetText);
        }
      );
    }
    return filteredPredictors;
  });

  setSource = memoize(
    (availablePredictors) => {
      availablePredictors.map(
        (x) => {
          if (!x.description && x.extracted_feature && x.extracted_feature.description) {
            x.description = x.extracted_feature.description;
          }
          if (x.extracted_feature && x.extracted_feature.extractor_name) {
            x.source = x.extracted_feature.extractor_name;
          }
        }
      );
      this.setState({ searchText: '' });
      return availablePredictors;
    },
    isEqual
  );

  sourceCmp = (a, b) => {
    let x = a.source + a.name;
    let y = b.source + b.name;
    return x.localeCompare(y);
  }

  render() {
    let { availablePredictors, selectedPredictors, updateSelection } = this.props;
    let filteredPredictors = this.setSource(availablePredictors);
    filteredPredictors = this.searchFilter(this.state.searchText, filteredPredictors);
    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
        render: (text, record) => (
          <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
            {text}
          </div>
        )
        // width: '35%'
      },
      {
        title: 'Source',
        dataIndex: 'source',
        sorter: this.sourceCmp,
        defaultSortOrder: 'ascend' as 'ascend',
        render: (text, record) => (
          <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
            {text}
          </div>
        )
        // width: '30%'
      },
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
      let compactCol = [columns[0]];
      // compactCol[0].width = '100%';
      return (
        <div>
          <Row >
            <Col span={24}>
              {filteredPredictors && filteredPredictors.length > 20 &&
                <div>
                  <Input
                    placeholder="Search predictor name or description..."
                    value={this.state.searchText}
                    onChange={this.onInputChange}
                  />
                  <br />
                  <br />
                </div>
              }
              <div>
                <Table
                  locale={{ emptyText: this.state.searchText ? 'No results found' : 'No data'}}
                  columns={compactCol}
                  rowKey="id"
                  pagination={false}
                  scroll={{y: 465}}
                  size="small"
                  dataSource={filteredPredictors}
                  rowSelection={rowSelection}
                  bordered={false}
                  loading={this.props.predictorsLoad}
                />
              </div>
            </Col>
          </Row>
        </div>
      );
    }

    return (
      <div>
        <Row>
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
              <Table
                locale={{ emptyText: this.state.searchText ? 'No results found' : 'No data'}}
                columns={columns}
                rowKey="id"
                pagination={{defaultPageSize: 100}}
                scroll={{y: 465}}
                size="small"
                dataSource={filteredPredictors}
                rowSelection={rowSelection}
                bordered={false}
                loading={this.props.predictorsLoad}
                expandedRowRender={record => <p>{record.description}</p>}
              />
            </div>
            <p style={{'float': 'right'}}>
              {`Showing  ${filteredPredictors.length} of ${availablePredictors.length} predictors`}
            </p>
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
