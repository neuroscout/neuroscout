import * as React from 'react';

import { api } from '../api';
import { ApiUser, PredictorCollection } from '../coretypes';

class PredictorCollectionList extends React.Component<{}, {user: ApiUser}> {
  constructor(props) {
    super(props);
    // get user preditcor collections
  }
  
  componentDidMount() {
    api.getUser().then(user => {
      return user.predictor_collections.map((x) => {
        return api.getPredictorCollection(x.id);
      });
      
    });
  }

  render() {
    return (
      <div />
    );
  }
}
