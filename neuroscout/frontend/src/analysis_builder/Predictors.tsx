/*
PredictorSelector component used anywhere we need to select among a list of available
predictors. The component includes a table of predictors as well as search box to instantly
filter the table down to predictors whose name or description match the entered search term
*/
import * as React from 'react';
import { Checkbox, Col, Descriptions, Input, Row, Table, Tabs, Tag, Tooltip } from 'antd';
import { TableRowSelection } from 'antd/lib/table/interface';

import memoize from 'memoize-one';

import { Predictor, ExtractorDescriptions } from '../coretypes';

const { TabPane } = Tabs;
const filterFields = ['source', 'extractor_name', 'modality'];

interface PredictorFilter {
  title: string;
  active: boolean;
  count: number;
}

interface PredictorReviewProps {
  selectedPredictors: Predictor[];
  removePredictor: (string) => void;
}

export class PredictorReview extends React.Component<PredictorReviewProps, {} > {
  render() {
    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
      },
      {
        title: 'Source',
        dataIndex: 'source',
      },
      {
        title: 'Action',
        dataIndex: 'id',
        render: (text) => <a onClick={() => this.props.removePredictor(text)}>Remove</a>,
      },
    ];
    return (
      <Table
        columns={columns}
        rowKey="id"
        size="small"
        dataSource={this.props.selectedPredictors}
      />
    );
  }
}

interface PredictorSelectorProps {
  availablePredictors: Predictor[]; // All available predictors to select from
  selectedPredictors: Predictor[]; // List of predictors selected by the user (when used as a controlled component)
  // Callback to parent component to update selection
  updateSelection: (newPredictors: Predictor[], filteredPredictors: Predictor[]) => void;
  predictorsLoad?: boolean;
  selectedText?: string;
  compact?: boolean;
  extractorDescriptions?: ExtractorDescriptions;
}

interface PredictorsSelectorState {
  searchText: string;  // Search term entered in search box
  filteredPredictors: Predictor[]; // Subset of available predictors whose name or description match the search term
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
      selectedText: selectedText ? selectedText : '',
      sourceFilters: [],
      modalityFilters: [],
      extractor_nameFilters: []
    };
    if (availablePredictors.length > 0) {
      this.updateFilters(availablePredictors);
    }
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
      predictors.map(x => !!x[field] ? unique.add(x[field]) : null);
      let stateField = field + 'Filters';
      let updatedFilters = [...unique].sort().map(x => {
        return {title: x, active: !!this.state[stateField].active, count: 0};
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

  clearFilters = () => {
    let stateUpdate = {};
    this.filterFields.map((field) => {
      let fieldName = field + 'Filters';
      stateUpdate[fieldName] = this.state[fieldName].map(filter => {
        filter.active = false;
        filter.count = 0;
        return filter;
      });
    });
    this.setState({...stateUpdate, filteredPredictors: this.props.availablePredictors});
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
    let filterOn = this.props.availablePredictors;

    this.filterFields.map(filterField => {
      if (!this.state[filterField + 'Filters'].find(filter => filter.active === true)) {
        return;
      }
      let filterClassPredictors = [] as Predictor[];
      this.state[filterField + 'Filters'].map(filter => {
        if (filter.active) {
          filter.count = filterOn.filter(predictor => {
            if (predictor[filterField] === filter.title) {
              filterClassPredictors.push(predictor);
              return true;
            }
            return false;
          }).length;
        }
      });
      filterOn = filterClassPredictors;
    });
    this.setState({filteredPredictors: [...filterOn]});
  };

  sourceCmp = (a, b) => {
    let x = a.source + a.name;
    let y = b.source + b.name;
    return x.localeCompare(y);
  }

  componentDidUpdate(prevProps) {
    if (prevProps.predictorsLoad && !this.props.predictorsLoad) {
      this.updateFilters(this.props.availablePredictors);
    }
  }

  filterCheckboxes = (filterType) => this.state[filterType + 'Filters'].map(filter => {
    let display = !!filter.count && filter.active ? `${filter.title} (${filter.count})` : filter.title;
    let checkbox = (
      <Checkbox
        onChange={() => this.toggleFilter(filterType, filter.title)}
        checked={filter.active}
        key={filter.title}
      >
        {display}
      </Checkbox>
    );

    if (this.props.extractorDescriptions && this.props.extractorDescriptions[filter.title]) {
      let description = this.props.extractorDescriptions[filter.title];
      checkbox = (<div title={description}>{checkbox}</div>);
    }
    return checkbox;
  })

  expandedRowRender = (predictor: Predictor) => {
    const detailFields = {'max': 'maximum', 'min': 'minimum', 'mean': 'mean', 'num_na': 'number of N/As',
      'modality': 'modality'};
    let descItems: JSX.Element[] = [];
    if ('description' in predictor && predictor.description) {
        descItems.push(<Descriptions.Item label="description" span={3}>{predictor.description}</Descriptions.Item>);
    }
    for (const field in detailFields) {
      if (field in predictor && predictor[field]) {
        descItems.push(<Descriptions.Item label={detailFields[field]}>{predictor[field]}</Descriptions.Item>);
      }
    }

    return (
      <Descriptions bordered={true} size="small">
        {descItems}
      </Descriptions>
    );
  }

  render() {
    let { availablePredictors, selectedPredictors, updateSelection } = this.props;
    let { filteredPredictors } = this.state;

    filteredPredictors = this.searchFilter(this.state.searchText, filteredPredictors);

    let numSelected = selectedPredictors.length;

    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
        sorter: (a, b) => a.name.localeCompare(b.name),
        render: (text, record) => (
          <div title={record.description} style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
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
        render: (text, record) => {
          let description = '';
          if (this.props.extractorDescriptions && this.props.extractorDescriptions[text]) {
            description = this.props.extractorDescriptions[text];
          }
          return (
            <div title={description} style={{ wordWrap: 'break-word', wordBreak: 'break-word' }}>
                {text}
            </div>
          );
        }
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

    let sourceCheckboxes = this.filterCheckboxes('source');
    let modalityCheckboxes = this.filterCheckboxes('modality');

    return (
      <div>
        <Tabs type="card">
          <TabPane tab="Available" key="1">
            <Row>
              <Col xl={{span: 16}} lg={{span: 24}}>
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
                    pagination={{defaultPageSize: 20}}
                    size="small"
                    dataSource={filteredPredictors}
                    rowSelection={rowSelection}
                    bordered={false}
                    loading={this.props.predictorsLoad}
                    expandedRowRender={this.expandedRowRender}
                  />
                </div>
                <p style={{'float': 'right'}}>
                  {`Showing  ${filteredPredictors.length} of ${availablePredictors.length} predictors`}
                </p>
              </Col>
              <Col xl={{span: 1}}/>
              <Col xl={{span: 7}}>
                <h4>Source:</h4>
                {sourceCheckboxes}
                {!!this.state.modalityFilters.length && <h4>Modality Filter:</h4>}
                {modalityCheckboxes}
                <a onClick={this.clearFilters}>Clear All</a>
              </Col>
            </Row>
          </TabPane>
          <TabPane tab={`Selected (${numSelected})`} key="2">
            <PredictorReview selectedPredictors={selectedPredictors} removePredictor={this.removePredictor} />
          </TabPane>
        </Tabs>
      </div>
    );
  }
}
