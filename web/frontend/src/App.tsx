import * as React from 'react';
import { Tabs, Row, Col, Layout, message } from 'antd';

import './App.css';

import { OverviewTab } from './Overview';
import { PredictorsTab } from './Predictors';
import { Store, Analysis, Dataset, Task, Run, ApiDataset } from './commontypes';

const { TabPane } = Tabs;
const { Footer, Content } = Layout;

// const logo = require('./logo.svg');
const domainRoot = 'http://localhost:80';
const EMAIL = 'test2@test.com';
const PASSWORD = 'password';

// Create initialized app state (used in the constructor of the top-level App component)
const initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  transformationsActive: false,
  contrastsActive: false,
  modelingActive: false,
  reviewActive: true,
  analysis: {
    analysisId: null,
    analysisName: 'Untitled',
    analysisDescription: '',
    datasetId: null,
    predictions: '',
    runIds: [],
    predictorIds: []
  },
  datasets: [],
  availableTasks: [],
  availableRuns: [],
  selectedTaskId: null,
  availablePredictors: []
});

const getJwt = () => new Promise((resolve, reject) => {
  /* Returns an access token (JWT) as a promise, either straight from local 
     storage or by fetching from the server (/auth) with username/password and 
     caching it to local storage. */
  const jwt = window.localStorage.getItem('jwt');
  if (jwt) {
    resolve(jwt);
  }
  else {
    fetch(domainRoot + '/api/auth', {
      method: 'post',
      body: JSON.stringify({ email: EMAIL, password: PASSWORD }),
      headers: {
        'Content-type': 'application/json'
      }
    })
      .then((response) => {
        response.json().then((data: { access_token: string }) => {
          if (data.access_token) {
            message.success('Authentication successful');
            window.localStorage.setItem('jwt', data.access_token);
            resolve(data.access_token);
          }
        });
      })
      .catch(error => {
        console.log('An error happened: ', error);
        message.error(error.toString());
      });
  }
});

// Wrapper around 'fetch' to add JWT authorization header and authenticate first if necessary  
const aFetch = (path: string, options?: object): Promise<any> => {
  return getJwt().then((jwt: string) => {
    const newOptions = Object.assign({
      headers: {
        'Content-type': 'application/json',
        'Authorization': 'JWT ' + jwt
      }
    }, options);
    return fetch(path, newOptions);
  });
};

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const authors = d.description.Authors? d.description.Authors.join(', '): 'No authors listed';
  const description = d.description.Description;
  const url = d.description.URL;
  const {name, id} = d;
  return {id, name, authors, url, description};
};


// Get array of unique tasks from a list of runs, and count the number of runs associated with each
const getTasks = (runs: Run[]): Task[] => {
  let taskMap: Map<string, Task> = new Map();
  for (let run of runs) {
    const key = run.task.id;
    if (taskMap.has(key))
      taskMap.get(key)!.numRuns += 1;
    else
      taskMap.set(key, { ...run.task, numRuns: 1 });
  }
  return Array.from(taskMap.values());
}

class App extends React.Component<{}, Store> {
  constructor(props) {
    super(props);
    this.state = initializeStore();
    aFetch(domainRoot + '/api/datasets').then(response => {
      response.json().then(data => {
        const datasets: Dataset[] = data.map(d => normalizeDataset(d));
        this.setState({ 'datasets': datasets });
      });
    })
      .catch(error => { message.error(error.toString()); });
  }

  updateState = (attrName: keyof Store) => (value: any) => {
    /* 
     Main function to update application state. May split this up into
     smaller pieces of it gets too complex.
    */
    let stateUpdate = {};
    if (attrName === 'analysis') {
      const updatedAnalysis: Analysis = value;
      if (updatedAnalysis.datasetId !== this.state.analysis.datasetId) {
        // If a new dataset is selected we need to fetch the associated runs
        aFetch(`${domainRoot}/api/runs?dataset_id=${updatedAnalysis.datasetId}`)
          .then(response => {
            response.json().then((data: Run[]) => {
              this.setState({ availableRuns: data });
              this.setState({ availableTasks: getTasks(data)});
            });
          })
          .catch(error => { console.log(error); });
      }
      if (updatedAnalysis.runIds.length !== this.state.analysis.runIds.length) {
        // If there was any change in selection of runs, fetch the associated predictors
        const runIds = updatedAnalysis.runIds.join(',');
        aFetch(`${domainRoot}/api/predictors?runs=${runIds}`)
          .then(response => {
            response.json().then(data => {
              this.setState({ availablePredictors: data });
            });
          })
          .catch(error => { console.log(error); });
      }
      // Enable predictors tab only if the number of selected runs is greater than zero
      stateUpdate['predictorsActive'] = value.runIds.length > 0;
    }
    stateUpdate[attrName] = value;
    this.setState(stateUpdate);
  }

  render() {
    const { predictorsActive, transformationsActive, contrastsActive, modelingActive,
      reviewActive, analysis, datasets, availableTasks, availableRuns, 
      selectedTaskId, availablePredictors } = this.state;
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
                      availableTasks={availableTasks}
                      availableRuns={availableRuns}
                      selectedTaskId={selectedTaskId}
                      updateAnalysis={this.updateState('analysis')}
                      updateSelectedTaskId={this.updateState('selectedTaskId')}                      
                    />
                  </TabPane>
                  <TabPane tab="Predictors" key="2" disabled={!predictorsActive}>
                    <PredictorsTab
                      analysis={analysis}
                      availablePredictors={availablePredictors}
                      updateAnalysis={this.updateState('analysis')}
                    />
                  </TabPane>
                  <TabPane tab="Transformations" key="3" disabled={!transformationsActive} />
                  <TabPane tab="Contrasts" key="4" disabled={!contrastsActive} />
                  <TabPane tab="Modeling" key="5" disabled={!modelingActive} />
                  <TabPane tab="Review" key="6" disabled={!reviewActive}>
                    <p>
                      {JSON.stringify(analysis)}
                    </p>
                  </TabPane>
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
};

init();
export default App;
