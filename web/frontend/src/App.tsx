import * as React from 'react';
import { Tabs, Row, Col, Layout, message } from 'antd';

import './App.css';

import { OverviewTab } from './Overview'
import { Store } from './commontypes'

const TabPane = Tabs.TabPane;
const { Footer, Content } = Layout;

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
          if (data.access_token) {
            message.success('Authentication successful')
            window.localStorage.setItem('jwt', data.access_token);
            resolve(data.access_token);
          }
        })
      })
      .catch(error => {
        console.log('An error happened: ', error)
        message.error(error.toString());
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
    .catch(error => {message.error(error.toString());})
  }

  updateState = (attrName: string) => (value: any) => {
    let stateUpdate = {}
    if (attrName == 'analysis') {
      if (value.datasetId != this.state.analysis.datasetId) {
        // If a new dataset is selected we need to fetch the associated runs
        aFetch(`${domainRoot}/api/runs?dataset=${value.datasetId}`)
          .then(response => {
            response.json().then(data => {
              this.setState({ availableRuns: data });
            })
          })
          .catch(error => { console.log(error); })
      }
      // Enable predictors tab only if the number of selected runs is greater than zero
      stateUpdate['predictorsActive'] = value.runIds.length > 0;
    }
    stateUpdate[attrName] = value;
    this.setState(stateUpdate);
  }

  render() {
    const { predictorsActive, transformationsActive, analysis, datasets, availableRuns } = this.state;
    return (
      <div className="App">
        <Layout>
          {/*<Header>
            <Row type="flex" justify="center">
              <Col span={16}>
                <h2>Neuroscout</h2>
              </Col>
            </Row>
          </Header>*/}
          {/*<img src={logo} className="App-logo" alt="logo" />*/}
          <Content>
            <Row type="flex" justify="center">
              <Col span={16}>
                <h1>Neuroscout</h1>
                <hr />
                <br />
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
          </Content>
          <Footer>
            <Row type="flex" justify="center">
              <Col span={16}>
                <p>Neuroscout - Copyright 2017</p>
              </Col>
            </Row>
          </Footer>
        </Layout>
      </div>
    );
  }
}

const init = () => {
  window.localStorage.clear(); // Dev-only, will remove later once there is user/password prompt functionality
}

init();
export default App;
