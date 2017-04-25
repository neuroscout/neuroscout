import * as React from 'react';
import { Button, Tabs, Row, Col } from 'antd';
import './App.css';

import { OverviewTab } from './Overview'
import { Store } from './commontypes'

const TabPane = Tabs.TabPane;
// const logo = require('./logo.svg');
const domainRoot = 'http://localhost:80'
const USERNAME = 'test2@test.com';
const PASSWORD = 'password';
const initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  transformationsActive: false,
  analysis: {
    analysisId: null,
    analysisName: 'Untitled',
    analysisDescription: '',
    datasetId: null,
    predictions: '',
    runIds: []
  },
  datasets: [],
  availableRuns: []
});

const getJwt = () => new Promise((resolve, reject) => {
  /* Returns an access token (JWT) as a promise, either straight from local 
     storage or by fetching from server (/auth) with username/password and 
     caching it to local storage. */
  let jwt = window.localStorage.getItem('jwt')
  if (jwt) {
    resolve(jwt);
  }
  else {
    fetch(domainRoot + '/auth', {
      method: 'post',
      body: JSON.stringify({ username: USERNAME, password: PASSWORD }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        response.json().then((data: { access_token: string }) => {
          window.localStorage.setItem('jwt', data.access_token);
          resolve(data.access_token);
        })
      });
  }
});

const aFetch = (path: string, options?: object): Promise<any> => {
  return getJwt().then((jwt: string) => {
    const newOptions = Object.assign({
      headers: {
        'Content-type': 'application/json',
        'Authorization': 'JWT ' + jwt
      }
    }, options)
    return fetch(path, newOptions);
  });
}

class App extends React.Component<{}, Store> {
  constructor(props) {
    super(props);
    this.state = initializeStore();
    aFetch(domainRoot + '/api/datasets').then(response => {
      response.json().then(data => {
        this.setState({ 'datasets': data })
      })
    })
  }

  updateState = (attrName: string) => (value: any) => {
    if (attrName == 'analysis' && value.datasetId != this.state.analysis.datasetId) {
      aFetch(`${domainRoot}/api/runs?dataset=${value.datasetId}`)
        .then(response => {
          response.json().then(data => {
            console.log(`Received ${data.length} datasets from /api/runs`);
            console.log(data);
            this.setState({availableRuns: data});
          })
        })
    }
    let stateUpdate = {}
    stateUpdate[attrName] = value;
    this.setState(stateUpdate);
  }

  render() {
    const { predictorsActive, transformationsActive, analysis, datasets, availableRuns } = this.state;
    return (
      <div className="App">
        <div className="App-header">
          {/*<img src={logo} className="App-logo" alt="logo" />*/}
          <h2>Neuroscout</h2>
        </div>
        <Row>
          <Col span={24}>
            <Tabs>
              <TabPane tab="Overview" key="1">
                <OverviewTab
                  analysis={analysis}
                  datasets={datasets}
                  availableRuns={availableRuns}
                  updateAnalysis={this.updateState('analysis')}
                />
              </TabPane>
              <TabPane tab="Predictors" key="2" disabled={!predictorsActive} />
              <TabPane tab="Transformations" key="3" disabled={!transformationsActive} />
              <TabPane tab="Contrasts" key="4" />
              <TabPane tab="Modeling" key="5" />
              <TabPane tab="Review" key="6" />
            </Tabs>
          </Col>
        </Row>
        <Button type="primary">Button</Button>
      </div>
    );
  }
}

const init = () => {
  window.localStorage.clear(); // Dev-only, will remove later once there is user/password prompt functionality
}

init();
export default App;
