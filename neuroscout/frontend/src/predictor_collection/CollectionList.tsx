import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Modal, Row, Tabs, Table, Typography,
         Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { ApiUser, Dataset, PredictorCollection, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { AddPredictorsForm } from './AddPredictorsForm';

const { Text } = Typography;

type CollectionListProps = {
  datasets: Dataset[]
};

type CollectionListState = {
  formModal: boolean,
  user?: ApiUser,
  collections?: PredictorCollection[]
};

export class PredictorCollectionList extends React.Component<CollectionListProps, CollectionListState> {
  constructor(props) {
    super(props);
    this.state = { formModal: false };
  }

  loadCollections() {
    api.getUser().then(user => {
      if (user && user.predictor_collections) {
        let collections = user.predictor_collections.map((x) => {
          return api.getPredictorCollection(x.id);
        });
        return Promise.all(collections);
      } else {
        return [];
      }
    }).then((collections) => {
      /* need to get dataset id from first predictor in each collection */
      collections.sort((a, b) => { return b.id - a.id; });
      this.setState({collections: collections});
    });
  }
  
  componentDidMount() {
    this.loadCollections();
  }

  closeModal() {
    this.loadCollections();
    this.setState({formModal: false});
  }

  render() {
    let collectionColumns = [
      { 
        title: 'Name',
        dataIndex: 'collection_name',
        sorter: (a, b) => a.collection_name.localeCompare(b.collection_name)
      },
      {
        title: 'Status',
        dataIndex: 'status',
        sorter: (a, b) => a.status.localeCompare(b.status)
      },
      { title: 'Predictors',
        dataIndex: 'predictors',
        render: (predictors, record, index) => {
          if (!record.traceback) {
            return (predictors.map(x => x.name).join(', '));
          }
          return (<Text type="danger">{record.traceback}</Text>);
        }
      }
    ];

    return (
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
           <Button
             onClick={() => this.setState({formModal: true})}
           >
             <Icon type="plus" /> Add New Predictors
           </Button>
           <br />
          {this.state.formModal &&
            <Modal
              title="Upload New Predictors"
              width="70%"
              visible={this.state.formModal}
              onCancel={() => this.setState({formModal: false})}
              okButtonProps={{ hidden: true }}
            >
              <AddPredictorsForm datasets={this.props.datasets} closeModal={this.closeModal} />
            </Modal>
          }
          {this.state.collections &&
            <Table
              rowKey="id"
              columns={collectionColumns}
              dataSource={this.state.collections}
            />
          }
        </MainCol>
       </Row>
    );
  }
}
