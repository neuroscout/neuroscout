import * as React from 'react';
// import * as $ from 'jquery'
import { Button, Tabs, Row, Col } from 'antd';
import './App.css';

import { Analysis, Dataset, OverviewTab } from './Overview'

const TabPane = Tabs.TabPane;
// const logo = require('./logo.svg');
const domainRoot = 'http://localhost:80'
const USERNAME = 'test2@test.com';
const PASSWORD = 'password';

interface Store {
  activeTab: 'overview' | 'predictors' | 'transformations' | 'contrasts' | 'modeling' | 'overview';
  predictorsActive: boolean;
  transformationsActive: boolean;
  analysis: Analysis;
  datasets: Dataset[];
}

const initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  transformationsActive: false,
  analysis: {
    analysisId: null,
    analysisName: 'Untitled',
    analysisDescription: '',
    datasetId: null,
    predictions: ''
  },
  datasets: []
});

const getJwt = () => new Promise((resolve, reject) => {
  /* Returns an access token (JWT) as a promise, either straight from local 
     storage or by fetching from server (/auth) with username/password and 
     caching it to local storage. */
  console.log('Inside getJwt executor...');
  let jwt = window.localStorage.getItem('jwt')
  if (jwt) {
    console.log('Getting JWT from localstorage...');
    resolve(jwt);
  }
  else {
    console.log('Fetching from /auth...');
    fetch(domainRoot + '/auth', {
      method: 'post',
      body: JSON.stringify({ username: USERNAME, password: PASSWORD }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        console.log('Received response from /auth...');
        response.json().then((data: { access_token: string }) => {
          window.localStorage.setItem('jwt', data.access_token);
          console.log('Saving JWT to local storage');
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
        this.setState({'datasets': data})
        console.log(`Received ${data.length} datasets from /api/datasets/ data`);
      })
    })
  }

  updateState = (attrName: string) => (value: any) => {
    let stateUpdate = {}
    stateUpdate[attrName] = value;
    this.setState(stateUpdate);
  }

  render() {
    const { activeTab, predictorsActive, transformationsActive, analysis, datasets } = this.state;
    console.log(activeTab);
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
