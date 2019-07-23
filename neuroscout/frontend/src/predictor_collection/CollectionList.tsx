import * as React from 'react';
import { Button, Card, Checkbox, Collapse, Form, Icon, Input, List, Row, Tabs, Table, Upload } from 'antd';
import { TableRowSelection } from 'antd/lib/table';

import { api } from '../api';
import { ApiUser, Dataset, Run, RunFilters } from '../coretypes';
import { datasetColumns, MainCol } from '../HelperComponents';
import { AddPredictorsForm } from './AddPredictorsForm';

type CollectionListProps = {
  datasets: Dataset[]
};

type CollectionListState = {
  formModal: boolean,
  user: ApiUser
};

export class PredictorCollectionList extends React.Component<CollectionListProps, CollectionListState> {
  constructor(props) {
    super(props);
    // get user preditcor collections
  }
  
  componentDidMount() {
    api.getUser().then(user => {
      if (user && user.predictorCollections) {
        const col = user.predictorCollections.map((x) => {
          return api.getPredictorCollection(x.id);
        });
      }
    });
  }

  render() {
    return (
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
           <Button
             onClick={() => this.setState({formModal: true})}
           >
             <Icon type="plus" /> Add New Predictors
           </Button>
          <AddPredictorsForm datasets={this.props.datasets} />
        </MainCol>
       </Row>
    );
  }
}
