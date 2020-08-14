import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Modal, Row, Tabs, Table, Tag,
         Typography, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { ApiUser, Dataset, PredictorCollection, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { AddPredictorsForm } from './AddPredictorsForm';

const { Text } = Typography;

export interface CollectionListProps {
  datasets: Dataset[];
  collections: PredictorCollection[];
  updateUser: (data: any, updateLocal?: boolean) => void;
}

export interface CollectionListState {
  formModal: boolean;
  user?: ApiUser;
  collections?: PredictorCollection[];
  loading: boolean;
}

export class PredictorCollectionList extends React.Component<CollectionListProps, CollectionListState> {
  constructor(props) {
    super(props);
    this.state = { formModal: false, loading: false };
  }

  // this duplicates code in auth.store but allows us to handle promise more easily and keep
  // loading state local
  loadCollections = () => {
    this.setState({loading: true});
    api.getUser().then((user: ApiUser): any => {
      if (user && user.predictor_collections) {
        let collections = user.predictor_collections.map((x) => {
          return api.getPredictorCollection(x.id);
        });
        return Promise.all(collections);
      } else {
        this.setState({loading: false});
        return [];
      }
    }).then((collections) => {
      // collections.sort((a, b) => { return b.id - a.id; });
      this.setState({loading: false});
      this.props.updateUser({predictorCollections: collections});
    });
  };
 
  componentDidMount() {
    this.loadCollections();
  }

  closeModal = ()  => {
    this.loadCollections();
    this.setState({formModal: false});
  };

  render() {
    let datasets = this.props.datasets.filter(x => x.active === true);
    let collectionColumns = [
      { 
        title: 'Name',
        dataIndex: 'collection_name',
        sorter: (a, b) => a.collection_name.localeCompare(b.collection_name)
      },
      {
        title: (<>Status <Icon type="reload" onClick={this.loadCollections} /></>),
        dataIndex: 'status',
        sorter: (a, b) => a.status.localeCompare(b.status)
      },
      {
        title: 'Predictors',
        dataIndex: 'predictors',
        render: (predictors, record, index) => {
          if (!record.traceback) {
            return (predictors.map(x => x.name).join(', '));
          }
          return (<Text type="danger">{record.traceback}</Text>);
        }
      },
      {
        title: 'Predictor Visibility',
        dataIndex: 'predictors',
        key: 'pred_visiblity',
        render: (predictors, record, index) => {
          if (!predictors || !predictors.length) {
            return ('');
          } else if (predictors.every(x => x.private === true)) {
            return (<Tag>Private</Tag>);
          } else if (predictors.every(x => x.private === false)) {
            return (<Tag color="blue">Public</Tag>);
          } else {
            return (<Tag color="yellow">Mixed</Tag>);
          }
        }
      },
    ];

    return (
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
           <Row>
             <span className="viewTitle"> My Predictor Collections</span>
             <span style={{float: 'right'}}>
             <Button
               onClick={() => this.setState({formModal: true})}
             >
               <Icon type="plus" /> Add New Predictors
             </Button>
             </span>
           </Row>
           <br />
          {this.state.formModal &&
            <Modal
              title="Upload New Predictors"
              width="70%"
              visible={this.state.formModal}
              onCancel={() => this.setState({formModal: false})}
              okButtonProps={{ hidden: true }}
              cancelButtonProps={{ hidden: true }}
            >
              <AddPredictorsForm datasets={datasets} closeModal={this.closeModal} />
            </Modal>
          }
          {this.props.collections &&
            <Table
              columns={collectionColumns}
              rowKey="id"
              dataSource={this.props.collections}
              loading={this.state.loading}
              locale={{ emptyText: 'No custom predictors uploaded.' }}
            />
          }
        </MainCol>
       </Row>
    );
  }
}
