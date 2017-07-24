import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Icon, message } from 'antd';
import { Prompt } from 'react-router-dom';
import { OverviewTab } from './Overview';
import { PredictorSelector } from './Predictors';
import { XformsTab } from './Transformations';
import OptionsTab from './Options';
import {
  Store, Analysis, Dataset, Task, Run, Predictor,
  ApiDataset, ApiAnalysis, AnalysisConfig, Transformation
} from './coretypes';
import { displayError, jwtFetch } from './utils';
import { Space } from './HelperComponents';
import Status from './Status';

const { TabPane } = Tabs;
const { Footer, Content } = Layout;

// const logo = require('./logo.svg');
const domainRoot = 'http://localhost:80';
const EMAIL = 'test2@test.com';
const PASSWORD = 'password';
const DEFAULT_SMOOTHING = 50;

// Create initialized app state (used in the constructor of the top-level App component)
const initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  transformationsActive: false,
  contrastsActive: false,
  modelingActive: true,
  reviewActive: true,
  analysis: {
    analysisId: undefined,
    name: '',
    description: '',
    datasetId: null,
    predictions: '',
    runIds: [],
    predictorIds: [],
    status: 'DRAFT',
    private: true,
    config: { smoothing: DEFAULT_SMOOTHING, predictorConfigs: {} },
    transformations: [],
  },
  datasets: [],
  availableTasks: [],
  availableRuns: [],
  selectedTaskId: null,
  availablePredictors: [],
  selectedPredictors: [],
  unsavedChanges: false
});

const getJwt = () => new Promise((resolve, reject) => {
  /* Returns an access token (JWT) as a promise, either straight from local 
     storage or by fetching from the server (/auth) with username/password and 
     caching it to local storage. */
  const jwt = window.localStorage.getItem('jwt');
  if (jwt) {
    resolve(jwt);
  } else {
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
const authorizeAndFetch = (path: string, options?: object) => {
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
  const id = d.id.toString();
  const { name } = d;
  return { id, name, authors, url, description };
};

// Get array of unique tasks from a list of runs, and count the number of runs associated with each
const getTasks = (runs: Run[]): Task[] => {
  let taskMap: Map<string, Task> = new Map();
  for (let run of runs) {
    const key = run.task.id;
    if (taskMap.has(key)) {
      taskMap.get(key)!.numRuns += 1;
    } else {
      taskMap.set(key, { ...run.task, numRuns: 1 });
    }
  }
  return Array.from(taskMap.values());
}

// Given an updated list of predictor IDs, create an updated version of analysis config. 
// preserving the existing predictor configs, and adding/removing new/old ones as necessary
const getUpdatedConfig = (config: AnalysisConfig, predictorIds: string[]): AnalysisConfig => {
  let newConfig = { ...config };
  let newPredictorConfigs = { ...config.predictorConfigs }
  predictorIds.forEach((id) => {
    if (!newPredictorConfigs.hasOwnProperty(id)) {
      newPredictorConfigs[id] = {
        convolution: 'Gamma',
        temporalDerivative: true,
        orthogonalize: false,
      };
    }
  });
  // TODO: remove unnecessary predictorConfigs
  newConfig.predictorConfigs = newPredictorConfigs;
  return newConfig;
}

type BuilderProps = {
  id?: string;
  updatedAnalysis: () => void;
}
export default class AnalysisBuilder extends React.Component<BuilderProps, Store> {
  constructor(props: BuilderProps) {
    super(props);
    this.state = initializeStore();
    // Load analysis from server if an analysis id is specified in the props
    if (!!props.id) {
      jwtFetch(`${domainRoot}/api/analyses/${props.id}`)
        // .then(response => response.json() as Promise<ApiAnalysis>)
        .then((data: ApiAnalysis) => this.loadAnalysis(data))
        .catch(displayError);
    }
    jwtFetch(domainRoot + '/api/datasets')
      // .then(response => response.json())
      .then(data => {
        const datasets: Dataset[] = data.map(d => normalizeDataset(d));
        this.setState({ 'datasets': datasets });
      })
      .catch(displayError);
  }

  saveEnabled = (): boolean => this.state.unsavedChanges && this.state.analysis.status === 'DRAFT';
  submitEnabled = (): boolean => this.state.analysis.status === 'DRAFT';

  // Save analysis to server, either with lock=false (just save), or lock=true (save & submit)
  saveAnalysis = ({ compile = false }) => (): void => {
    if ((!compile && !this.saveEnabled()) || (compile && !this.submitEnabled())) {
      return;
    }
    const analysis = this.state.analysis;
    if (analysis.datasetId === null) {
      displayError(Error('Analysis cannot be saved without selecting a dataset'));
      return;
    }
    if (!analysis.name) {
      displayError(Error('Analysis cannot be saved without a name'));
      return;
    }
    const apiAnalysis: ApiAnalysis = {
      name: analysis.name,
      description: analysis.description,
      predictions: analysis.predictions,
      private: analysis.private,
      dataset_id: analysis.datasetId,
      status: analysis.status,
      runs: analysis.runIds.map(id => ({ id })),
      predictors: analysis.predictorIds.map(id => ({ id })),
      transformations: analysis.transformations,
      config: analysis.config,
    };
    // const method = analysis.analysisId ? 'put' : 'post';
    let method: string;
    let url: string;
    if (compile && analysis.analysisId) { // Submit for compilation
      url = `${domainRoot}/api/analyses/${analysis.analysisId}/compile`;
      method = 'post';
    } else if (!compile && analysis.analysisId) { // Save existing analysis
      url = `${domainRoot}/api/analyses/${analysis.analysisId}`;
      method = 'put';
    } else if (!compile && !analysis.analysisId) { // Save new analysis
      url = `${domainRoot}/api/analyses`;
      method = 'post';
    } else { // Wat?
      const error = Error('Error saving or submitting analysis.');
      displayError(error);
      throw error;
    }
    jwtFetch(url, { method, body: JSON.stringify(apiAnalysis) })
      // .then(response => response.json())
      .then((data: ApiAnalysis & {statusCode: number}) => {
        if(data.statusCode !== 200) throw new Error('Oops...something went wrong. Analysis was not saved.')
        message.success(compile ? 'Analysis submitted for generation' : 'Analysis saved');
        this.setState({
          analysis: {
            ...analysis,
            analysisId: data.hash_id,
            status: data.status,
            modifiedAt: data.modified_at,
          },
          unsavedChanges: false,
        });
        this.props.updatedAnalysis();
      })
      .catch(displayError);
  }

  loadAnalysis = (data: ApiAnalysis): Promise<Analysis> => {
    if(!data.transformations){
      return Promise.reject('Data returned by server is missing transformations array.');
    }
    const analysis: Analysis = {
      ...data,
      analysisId: data.hash_id,
      datasetId: data.dataset_id,
      runIds: data.runs!.map(({ id }) => id),
      predictorIds: data.predictors!.map(({ id }) => id),
      config: data.config, 
      transformations: data.transformations.filter(xform => xform.name), // TODO: remove the filter once this issue is fixed: https://github.com/PsychoinformaticsLab/neuroscout/issues/99
    };
    if (analysis.runIds.length > 0) {
      jwtFetch(`${domainRoot}/api/runs/${analysis.runIds[0]}`)
        // .then(response => response.json() as Promise<Run>)
        .then(data => {
          this.setState({ selectedTaskId: data.task.id });
          this.updateState('analysis', true)(analysis);
        })
        .catch(displayError);
    } else {
      this.updateState('analysis', true)(analysis);
    }
    return Promise.resolve(analysis);
  }

  confirmSubmission = (): void => {
    if (!this.submitEnabled()) return;
    const { saveAnalysis } = this;
    Modal.confirm({
      title: 'Are you sure you want to submit the analysis?',
      content: `Once you submit an analysis you will no longer be able to modify it. 
                You will, however, be able to clone it as a starting point for a new analysis.`,
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        saveAnalysis({ compile: true })();
      },
    });
  }

  updateConfig = (newConfig: AnalysisConfig): void => {
    const newAnalysis = { ...this.state.analysis };
    newAnalysis.config = newConfig;
    this.setState({ analysis: newAnalysis, unsavedChanges: true });
  }

  updateTransformations = (xforms: Transformation[]): void => {
    this.setState({
      analysis: { ...this.state.analysis, transformations: xforms },
      unsavedChanges: true,
    });
  }

  /* Main function to update application state. May split this up into
   smaller pieces if it gets too complex. 
   
   When keepClean is true, don't set unsavedChanges to true. This is useful in situations
   like loading a new analysis (loadAnalysis function) where updateState is called but
   since state changes aren't really user edits we don't want to set unsavedChanges.
   */
  updateState = (attrName: keyof Store, keepClean = false) => (value: any) => {
    const { analysis, availableRuns, availablePredictors } = this.state;
    if (analysis.status !== 'DRAFT' && !keepClean) {
      message.warning('This analysis is locked and cannot be edited');
      return;
    }
    let stateUpdate: any = {};
    if (attrName === 'analysis') {
      const updatedAnalysis: Analysis = value;
      if (updatedAnalysis.datasetId !== analysis.datasetId) {
        // If a new dataset is selected we need to fetch the associated runs
        jwtFetch(`${domainRoot}/api/runs?dataset_id=${updatedAnalysis.datasetId}`)
          // .then(response => response.json())
          .then((data: Run[]) => {
            message.success(`Fetched ${data.length} runs associated with the selected dataset`);
            this.setState({
              availableRuns: data,
              availableTasks: getTasks(data),
              // availablePredictors: []
            });
          })
          .catch(displayError);
      }
      if (updatedAnalysis.runIds.length !== analysis.runIds.length) {
        // If there was any change in selection of runs, fetch the associated predictors
        const runIds = updatedAnalysis.runIds.join(',');
        if (runIds) {
          jwtFetch(`${domainRoot}/api/predictors?runs=${runIds}`)
            // .then(response => response.json())
            .then((data: Predictor[]) => {
              message.success(`Fetched ${data.length} predictors associated with the selected runs`);
              const selectedPredictors = data.filter(p => updatedAnalysis.predictorIds.indexOf(p.id) > -1);
              this.setState({
                availablePredictors: data,
                selectedPredictors
              });
              updatedAnalysis.config = getUpdatedConfig(updatedAnalysis.config, selectedPredictors.map(p => p.id));
            })
            .catch(displayError);
        } else {
          stateUpdate.availablePredictors = [];
        }
      }
      // Enable predictors tab only if at least one run has been selected
      stateUpdate.predictorsActive = value.runIds.length > 0;
      stateUpdate.transformationsActive = value.predictorIds.length > 0;
    } else if (attrName === 'selectedTaskId') {
      // When a different task is selected, autoselect all its associated run IDs
      this.updateState('analysis')({
        ...analysis,
        runIds: availableRuns.filter(r => r.task.id === value).map(r => r.id)
      });
    } else if (attrName === 'selectedPredictors') {
      let newAnalysis = { ...this.state.analysis };
      newAnalysis.predictorIds = (value as Predictor[]).map(p => p.id);
      newAnalysis.config = getUpdatedConfig(newAnalysis.config, newAnalysis.predictorIds);
      stateUpdate.analysis = newAnalysis;
      stateUpdate.transformationsActive = newAnalysis.predictorIds.length > 0;
    }
    stateUpdate[attrName] = value;
    if (!keepClean) stateUpdate.unsavedChanges = true;
    this.setState(stateUpdate);
  }

  render() {
    const { predictorsActive, transformationsActive, contrastsActive, modelingActive,
      reviewActive, activeTab, analysis, datasets, availableTasks, availableRuns,
      selectedTaskId, availablePredictors, selectedPredictors, unsavedChanges,
     } = this.state;
    const statusText: string = {
      DRAFT: 'This analysis has not yet been generated.',
      PENDING: 'This analysis has been submitted for generation and is being processed.',
      COMPILED: 'This analysis has been successfully generated',
    }[analysis.status]
    return (
      <div className="App">
        <Prompt
          when={unsavedChanges}
          message={'You have unsaved changes. Are you sure you want leave this page?'}
        />
        <Row type="flex" justify="center">
          <Col span={18}>
            <h2>
              {analysis.status !== 'DRAFT' ?
                <Icon type="lock" /> :
                <Icon type="unlock" />
              }
              <Space />
              <Button
                onClick={this.saveAnalysis({ compile: false })}
                disabled={!this.saveEnabled()}
                type={'primary'}
              >Save</Button>
              <Space />
              <Button
                onClick={this.confirmSubmission}
                type={'primary'}
                disabled={!this.submitEnabled()}
              >{unsavedChanges ? 'Save & Generate' : 'Generate'}</Button>
              <Space />
            </h2>
            <br />
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col span={18}>
            <Tabs
              activeKey={activeTab}
              onTabClick={(newTab) => this.setState({ activeTab: newTab })}
            >
              <TabPane tab="Overview" key="overview">
                <OverviewTab
                  analysis={analysis}
                  datasets={datasets}
                  availableTasks={availableTasks}
                  availableRuns={availableRuns}
                  selectedTaskId={selectedTaskId}
                  predictorsActive={predictorsActive}
                  updateAnalysis={this.updateState('analysis')}
                  updateSelectedTaskId={this.updateState('selectedTaskId')}
                  goToNextTab={() => this.setState({ activeTab: 'predictors' })}
                />
              </TabPane>
              <TabPane tab="Predictors" key="predictors" disabled={!predictorsActive}>
                <PredictorSelector
                  availablePredictors={availablePredictors}
                  selectedPredictors={selectedPredictors}
                  updateSelection={this.updateState('selectedPredictors')}
                />
              </TabPane>
              <TabPane tab="Transformations" key="transformations" disabled={!transformationsActive} >
                <XformsTab
                  predictors={selectedPredictors}
                  xforms={analysis.transformations}
                  onSave={xforms => this.updateTransformations(xforms)}
                />
              </TabPane>
              <TabPane tab="Contrasts" key="contrasts" disabled={!contrastsActive} />
              <TabPane tab="Options" key="modeling" disabled={!modelingActive}>
                <OptionsTab
                  analysis={analysis}
                  selectedPredictors={selectedPredictors}
                  updateConfig={this.updateConfig}
                />
              </TabPane>
              <TabPane tab="Review" key="review" disabled={!reviewActive}>
                <p>
                  {JSON.stringify(analysis)}
                </p>
              </TabPane>
              <TabPane tab="Status" key="status" disabled={false}>
                <Status status={analysis.status} />
                <br />
                <br />
                <p>{statusText}</p>
              </TabPane>
            </Tabs>
          </Col>
        </Row>
      </div>
    );
  }
}
