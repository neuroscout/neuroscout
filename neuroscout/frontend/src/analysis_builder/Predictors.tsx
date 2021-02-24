/*
PredictorSelector component used anywhere we need to select among a list of available
predictors. The component includes a table of predictors as well as search box to instantly
filter the table down to predictors whose name or description match the entered search term
*/
import * as React from 'react';
import { Checkbox, Col, Input, Row, Table, Tag, Tooltip } from 'antd';
import { TableRowSelection } from 'antd/lib/table/interface';

import memoize from 'memoize-one';

import { Predictor, ExtractorDescriptions } from '../coretypes';

const filterFields = ['source', 'extractor_name', 'modality'];

interface PredictorFilter {
  title: string;
  active: boolean;
}

interface PredictorSelectorProps {
  availablePredictors: Predictor[]; // All available predictors to select from
  selectedPredictors: Predictor[]; // List of predicors selected by the user (when used as a controlled component)
  // Callback to parent component to update selection
  updateSelection: (newPredictors: Predictor[], filteredPredictors: Predictor[]) => void;
  predictorsLoad?: boolean;
  selectedText?: string;
  compact?: boolean;
  extractorDescriptions?: ExtractorDescriptions;
}

interface PredictorsSelectorState {
  searchText: string;  // Search term entered in search box
  filteredPredictors: Predictor[]; // Subset of available preditors whose name or description match the search term
  selectedPredictors: Predictor[]; // List of selected predictors (when used as an uncontrolled component)
  selectedText?: string;
  sourceFilters: PredictorFilter[];
  modalityFilters: PredictorFilter[];
  extractor_nameFilters: PredictorFilter[];
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
      selectedText: selectedText ? selectedText : '',
      sourceFilters: [],
      modalityFilters: [],
      extractor_nameFilters: []
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

  // Predictor members to make fields for and filter on
  filterFields = ['source', 'extractor_name', 'modality'];

  // initialize and update categorical predictors, intended to run when ever available predictors changes
  updateFilters = (predictors) => {
    let updatedState = this.state;
    this.filterFields.map(field => {
      let unique = new Set();
      if (field === 'source') {
        predictors.map(x => !!x[field] ? unique.add(x[field]) : null);
      } else {
        predictors.map(x =>
          x.extracted_feature && !! x.extracted_feature[field] ? unique.add(x.extracted_feature[field]) : null
        );
      }
      let stateField = field + 'Filters';
      let updatedFilters = [...unique].sort().map(x => {
        return {title: x, active: !!this.state[stateField].active};
      });
      updatedState[stateField] = updatedFilters;
    });
    this.setState(updatedState, this.applyFilters);
  };

  toggleFilter = (field, title) => {
    let stateUpdate = {};

    field = (field + 'Filters') as keyof PredictorsSelectorState;
    let updatedFilters = this.state[field];

    let index = updatedFilters.findIndex((x) => x.title === title);
    updatedFilters[index].active = !updatedFilters[index].active;
    stateUpdate[field] = updatedFilters;
    this.setState(stateUpdate, this.applyFilters);
  }

  searchFilter = memoize((searchText, filteredPredictors) => {
    const searchRegex = new RegExp(searchText.trim(), 'i');
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

  applyFilters = () => {
    let filteredPredictors = this.props.availablePredictors;

    let anyActive = !!this.filterFields.find(filterField => {
        return !!this.state[filterField + 'Filters'].find(filter => filter.active === true);
    });

    if (anyActive) {
      filteredPredictors = this.props.availablePredictors.filter(predictor => {
        let keep = false;
        this.filterFields.map(filterField => {
          this.state[filterField + 'Filters'].map(filter => {
            if (filter.active === true && predictor[filterField] === filter.title) {
              keep = true;
              return;
            }
          });
        });
        return keep;
      });
    }
    this.setState({filteredPredictors: filteredPredictors});
  };

  sourceCmp = (a, b) => {
    let x = a.source + a.name;
    let y = b.source + b.name;
    return x.localeCompare(y);
  }

  sourceRender = (text, record) => {
    let inner = (
      <div style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
        {text}
      </div>
    );
    if (this.props.extractorDescriptions && this.props.extractorDescriptions[text]) {
      return (
        <Tooltip color="pink" title={this.props.extractorDescriptions[text]}>
          {inner}
        </Tooltip>
      );
    } else {
      return inner;
    }
  }

  componentDidUpdate(prevProps) {
    if (prevProps.predictorsLoad && !this.props.predictorsLoad) {
      this.updateFilters(this.props.availablePredictors);
    }
  }

  render() {
    let { availablePredictors, selectedPredictors, updateSelection } = this.props;
    let { filteredPredictors } = this.state;
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
        render: this.sourceRender
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
            <h4>Predictor Source Filter:</h4>
            {this.state.sourceFilters.map(filter => 
              <Checkbox
                onChange={() => this.toggleFilter('source', filter.title)}
                checked={filter.active}
                key={filter.title}
              >
                  {filter.title}
              </Checkbox>
            )}
            {!!this.state.modalityFilters.length && <h4>Modality Filter:</h4>}
            {this.state.modalityFilters.map(filter => 
              <Checkbox
                onChange={() => this.toggleFilter('modality', filter.title)}
                checked={filter.active}
                key={filter.title}
              >
                  {filter.title}
              </Checkbox>
            )}
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
