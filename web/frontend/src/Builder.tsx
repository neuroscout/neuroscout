import * as React from 'react';
import { Tabs, Row, Col, Layout, message } from 'antd';

import { OverviewTab } from './Overview';
import { PredictorsTab } from './Predictors';
import { Home } from './Home';
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
  availablePredictors: [],
  selectedPredictors: []
});

const displayError = (error: Error) => message.error(error.toString());

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
      .catch(displayError);
  }
});

// Wrapper around 'fetch' to add JWT authorization header and authenticate first if necessary  
const aFetch = (path: string, options?: object): Promise<any> => {
  return getJwt().then((jwt: string) => {
    const newOptions = {
      ...options,
      headers: {
        'Content-type': 'application/json',
        'Authorization': 'JWT ' + jwt
      }
    };
    return fetch(path, newOptions);
  });
};

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const authors = d.description.Authors ? d.description.Authors.join(', ') : 'No authors listed';
  const description = d.description.Description;
  const url = d.description.URL;
  const { name, id } = d;
  return { id, name, authors, url, description };
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

export class AnalysisBuilder extends React.Component<{}, Store> {
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
     smaller pieces if it gets too complex.
    */
    const { analysis, availableRuns } = this.state;
    let stateUpdate: any = {};
    if (attrName === 'analysis') {
      const updatedAnalysis: Analysis = value;
      if (updatedAnalysis.datasetId !== analysis.datasetId) {
        // If a new dataset is selected we need to fetch the associated runs
        aFetch(`${domainRoot}/api/runs?dataset_id=${updatedAnalysis.datasetId}`)
          .then(response => {
            response.json().then((data: Run[]) => {
              message.success(`Fetched ${data.length} runs associated with the selected dataset`);
              this.setState({
                availableRuns: data,
                selectedTaskId: null,
                availableTasks: getTasks(data),
                availablePredictors: []
              });
            });
          })
          .catch(displayError);
      }
      if (updatedAnalysis.runIds.length !== analysis.runIds.length) {
        // If there was any change in selection of runs, fetch the associated predictors
        const runIds = updatedAnalysis.runIds.join(',');
        if (runIds) {
          aFetch(`${domainRoot}/api/predictors?runs=${runIds}`)
            .then(response => {
              response.json().then(data => {
                message.success(`Fetched ${data.length} predictors associated with the selected runs`);
                this.setState({ availablePredictors: data });
              });
            })
            .catch(displayError);
        } else {
          stateUpdate.availablePredictors = [];
        }
      }
      // Enable predictors tab only if at least one run has been selected
      stateUpdate.predictorsActive = value.runIds.length > 0;
    } else if (attrName === 'selectedTaskId') {
      // When a different task is selected, autoselect all its associated run IDs
      this.updateState('analysis')({
        ...analysis,
        runIds: availableRuns.filter(r => r.task.id === value).map(r => r.id)
      });
    } else if (attrName === 'selectedPredictors') {
      let newAnalysis = { ...this.state.analysis };
      newAnalysis.predictorIds = value.map(p => p.id);
      stateUpdate.analysis = newAnalysis;
    }
    stateUpdate[attrName] = value;
    this.setState(stateUpdate);
  }

  render() {
    const { predictorsActive, transformationsActive, contrastsActive, modelingActive,
      reviewActive, analysis, datasets, availableTasks, availableRuns,
      selectedTaskId, availablePredictors, selectedPredictors } = this.state;
    return (
      <div className="App">
        <Row type="flex" justify="center">
          <Col span={16}>
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
                  selectedPredictors={selectedPredictors}
                  updateSelectedPredictors={this.updateState('selectedPredictors')}
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
      </div>
    );
  }
}
