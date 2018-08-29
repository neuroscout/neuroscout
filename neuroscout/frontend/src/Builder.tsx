 /*
 Top-level AnalysisBuilder component which contains all of the necessary state for editing
 an analysis.
*/
import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Icon, message } from 'antd';
import { Prompt } from 'react-router-dom';
import { OverviewTab } from './Overview';
import { PredictorSelector } from './Predictors';
import { ContrastsTab } from './Contrasts';
import { XformsTab } from './Transformations';
import OptionsTab from './Options';
import {
  Store,
  Analysis,
  Dataset,
  Task,
  Run,
  Predictor,
  ApiDataset,
  ApiAnalysis,
  AnalysisConfig,
  Transformation,
  Contrast,
  Block,
  BlockModel,
  BidsModel,
  ImageInput,
} from './coretypes';
import { displayError, jwtFetch } from './utils';
import { Space } from './HelperComponents';
import Status from './Status';
import { config } from './config';

const { TabPane } = Tabs;
const { Footer, Content } = Layout;

// const logo = require('./logo.svg');
const domainRoot = config.server_url;
const EMAIL = 'user@example.com';
const PASSWORD = 'string';
const DEFAULT_SMOOTHING = 5;
const editableStatus = ['DRAFT', 'FAILED'];

const defaultConfig: AnalysisConfig = { smoothing: DEFAULT_SMOOTHING, predictorConfigs: {} };

// Create initialized app state (used in the constructor of the top-level App component)
const initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  predictorsLoad: false,
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
    hrfPredictorIds: [],
    status: 'DRAFT',
    private: true,
    config: defaultConfig,
    transformations: [],
    contrasts: [],
    autoContrast: true,
    model: {
      blocks: [{
        level: 'run',
        transformations: [],
        contrasts: []
      }]
    }
  },
  datasets: [],
  availableTasks: [],
  availableRuns: [],
  selectedTaskId: null,
  availablePredictors: [],
  selectedPredictors: [],
  selectedHRFPredictors: [],
  unsavedChanges: false,
  currentLevel: 'run'
});

const getJwt = () =>
  new Promise((resolve, reject) => {
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
        .then(response => {
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
        Authorization: 'JWT ' + jwt
      }
    };
    return fetch(path, newOptions);
  });
};

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const authors = d.description.Authors ? d.description.Authors.join(', ') : 'No authors listed';
  const description = d.summary;
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
};

// Given an updated list of predictor IDs, create an updated version of analysis config.
// preserving the existing predictor configs, and adding/removing new/old ones as necessary
const getUpdatedConfig = (old_config: AnalysisConfig, predictorIds: string[]): AnalysisConfig => {
  let newConfig = { ...old_config };
  let newPredictorConfigs = { ...old_config.predictorConfigs };
  predictorIds.forEach(id => {
    if (!newPredictorConfigs.hasOwnProperty(id)) {
      newPredictorConfigs[id] = {
        convolution: 'Gamma',
        temporalDerivative: true,
        orthogonalize: false
      };
    }
  });
  // TODO: remove unnecessary predictorConfigs
  newConfig.predictorConfigs = newPredictorConfigs;
  return newConfig;
};

type BuilderProps = {
  id?: string;
  updatedAnalysis: () => void;
};

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
        this.setState({ datasets });
      })
      .catch(displayError);
  }

  saveEnabled = (): boolean => this.state.unsavedChanges && editableStatus.includes(this.state.analysis.status);
  submitEnabled = (): boolean => editableStatus.includes(this.state.analysis.status);

  buildModel = (): BidsModel => {

    let availableRuns = this.state.availableRuns;

    let task: string[] = this.state.availableTasks.filter(
      x => x.id === this.state.selectedTaskId
    ).map(y => y.name);

    let runs: number[] = this.state.availableRuns.filter(
      x => this.state.analysis.runIds.find(runId => runId === x.id)
    ).filter(y => y.number !== null).map(z => parseInt(z.number, 10));
    runs = Array.from(new Set(runs));

    let sessions: string[] = this.state.availableRuns.filter(
      x => this.state.analysis.runIds.find(runId => runId === x.id)
    ).filter(y => y.session !== null).map(z => z.session) as string[];
    sessions = Array.from(new Set(sessions));

    let subjects: string[] = this.state.availableRuns.filter(
      x => this.state.analysis.runIds.find(runId => runId === x.id)
    ).filter(y => y.subject !== null).map(z => z.subject) as string[];
    subjects = Array.from(new Set(subjects));

    /* analysis predictorIds is still being stored in its own field in database.
     * Leave it alone in analysis object and convert Ids to names here. If the
     * predictors field in the database is dropped, predictorIds should be converted
     * to hold predictor names instead of Ids.
     */
    let variables: string[];
    variables = this.state.analysis.predictorIds.map(id => {
      let found = this.state.availablePredictors.find(elem => elem.id === id);
      if (found) {
        return found.name;
      }
      return '';
    });
    variables = variables.filter(x => x !== '');

    let blocks: Block[] = [
      {
        level: 'run',
        transformations: this.state.analysis.transformations,
        contrasts: this.state.analysis.contrasts,
        auto_contrasts: this.state.analysis.autoContrast,
        model: {
          variables: variables,
        }
      },
      {
        level: 'dataset',
        auto_contrasts: true
      }
    ];

    if (this.state.analysis.hrfPredictorIds) {
      let hrfVariables: string[];
      hrfVariables = this.state.analysis.hrfPredictorIds.map(id => {
        let found = this.state.availablePredictors.find(elem => elem.id === id);
        if (found) {
          return found.name;
        }
        return '';
      });
      hrfVariables = hrfVariables.filter(x => x !== '');
      blocks[0].model!.HRF_variables = hrfVariables;
    }

    let imgInput: ImageInput = {};
    if (runs.length > 0) {
      imgInput.run = runs;
    }

    if (sessions.length > 0) {
      imgInput.session = sessions;
    }

    if (subjects.length >  0) {
      imgInput.subject = subjects;
    }

    if (task[0]) {
      imgInput.task = task[0];
    }

    return {
      name: this.state.analysis.name,
      description: this.state.analysis.description,
      input: imgInput,
      blocks: blocks,
    };
  };

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
      contrasts: analysis.contrasts,
      config: analysis.config
    };

    apiAnalysis.model = this.buildModel();

    // const method = analysis.analysisId ? 'put' : 'post';
    let method: string;
    let url: string;
    if (compile && analysis.analysisId) {
      // Submit for compilation
      url = `${domainRoot}/api/analyses/${analysis.analysisId}/compile`;
      method = 'post';
      this.setState({analysis: {...analysis, status: 'SUBMITTING'}});
    } else if (!compile && analysis.analysisId) {
      // Save existing analysis
      url = `${domainRoot}/api/analyses/${analysis.analysisId}`;
      method = 'put';
    } else if (!compile && !analysis.analysisId) {
      // Save new analysis
      url = `${domainRoot}/api/analyses`;
      method = 'post';
    } else {
      // Wat?
      const error = Error('Error saving or submitting analysis.');
      displayError(error);
      throw error;
    }
    jwtFetch(url, { method, body: JSON.stringify(apiAnalysis) })
      // .then(response => response.json())
      .then((data: ApiAnalysis & { statusCode: number }) => {
        if (data.statusCode !== 200) {
          if (compile) {
            this.setState({analysis: {...analysis, status: 'DRAFT'}});
          }
          throw new Error('Oops...something went wrong. Analysis was not saved.');
        }
        message.success(compile ? 'Analysis submitted for generation' : 'Analysis saved');
        this.setState({
          analysis: {
            ...analysis,
            analysisId: data.hash_id,
            status: data.status,
            modifiedAt: data.modified_at
          },
          unsavedChanges: false
        });
        this.props.updatedAnalysis();
      })
      .catch(displayError);
  };

  // Decode data returned by '/api/analyses/<id>' (ApiAnalysis) to convert it to the right shape (Analysis)
  // and fetch the associated runs
  loadAnalysis = (data: ApiAnalysis): Promise<Analysis> => {
    data.transformations = [];

    // Extract transformations and contrasts from within block object of response.
    let contrasts;
    let hrfPredictorIds;
    if (data && data.model && data.model.blocks) {
      for (var i = 0; i < data.model.blocks.length; i++) {
        if (data.model.blocks[i].level !== this.state.currentLevel) {
          continue;
        }
        if (data.model.blocks[i].transformations) {
          data.transformations = data.model.blocks[i].transformations;
        }
        if (data.model.blocks[i].contrasts) {
          data.contrasts = data.model.blocks[i].contrasts;
        }
        if (data.model.blocks[i].model && data.model.blocks[i].model!.HRF_variables) {
          hrfPredictorIds = data.model.blocks[i].model!.HRF_variables;
        }
      }
    }

    if (!data.transformations) {
      return Promise.reject('Data returned by server is missing transformations array.');
    }

    const analysis: Analysis = {
      name: data.name,
      description: data.description,
      predictions: data.predictions,
      status: data.status,
      analysisId: data.hash_id,
      datasetId: data.dataset_id,
      runIds: data.runs!.map(({ id }) => id),
      predictorIds: data.predictors!.map(({ id }) => id),
      hrfPredictorIds: hrfPredictorIds,
      config: data.config || defaultConfig,
      transformations: data.transformations,
      contrasts: data.contrasts || [],
      autoContrast: true
    };

    if (analysis.runIds.length > 0) {
      jwtFetch(`${domainRoot}/api/runs/${analysis.runIds[0]}`)
        // .then(response => response.json() as Promise<Run>)
        .then(fetch_data => {
          this.setState({ selectedTaskId: fetch_data.task.id });
          this.updateState('analysis', true)(analysis);
        })
        .catch(displayError);
    } else {
      this.updateState('analysis', true)(analysis);
    }
    return Promise.resolve(analysis);
  };

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
        saveAnalysis({ compile: false})();
        saveAnalysis({ compile: true })();
      }
    });
  };

  updateConfig = (newConfig: AnalysisConfig): void => {
    const newAnalysis = { ...this.state.analysis };
    newAnalysis.config = newConfig;
    this.setState({ analysis: newAnalysis, unsavedChanges: true });
  };

  updateTransformations = (xforms: Transformation[]): void => {
    this.setState({
      analysis: { ...this.state.analysis, transformations: xforms },
      unsavedChanges: true
    });
  };

  updateContrasts = (contrasts: Contrast[]): void => {
    this.setState({
      analysis: { ...this.state.analysis, contrasts },
      unsavedChanges: true
    });
  };

  updatePredictorState = (value: any, filteredPredictors: Predictor[], hrf: boolean = false) => {
    let stateUpdate: any = {};
    let newAnalysis = { ...this.state.analysis };
    let filteredIds = filteredPredictors.map(x => x.id);
    let valueIds = value.map(x => x.id);
    let selectedPredictors = hrf ? 'selectedHRFPredictors' : 'selectedPredictors';
    let predictorIds = hrf ? 'hrfPredictorIds' : 'predictorIds';

    if (newAnalysis[predictorIds] === undefined) {
      newAnalysis[predictorIds] = [];
    }
    // Discard any Ids that appear in the filtered list but have not been selected
    newAnalysis[predictorIds] = newAnalysis[predictorIds].filter(x => {
      return !((filteredIds.indexOf(x) > -1) && !(valueIds.indexOf(x) > -1));
    });
    // Add new ids that have been selected but aren't currently in the analysis predictor list
    valueIds.map(x => newAnalysis[predictorIds].indexOf(x) === -1 ? newAnalysis[predictorIds].push(x) : null);

    newAnalysis.config = getUpdatedConfig(newAnalysis.config, newAnalysis[predictorIds]);
    stateUpdate.analysis = newAnalysis;
    stateUpdate.transformationsActive = newAnalysis[predictorIds].length > 0;

    // Update states version of the predictor list which uses whole predictor objects.
    stateUpdate[selectedPredictors] = this.state.availablePredictors.filter(
      (x) => {
        return newAnalysis[predictorIds].indexOf(x.id) > -1;
      }
    );

    // If we remove a predictor this needs to be reflected in the selected hrf predictors
    if (!(hrf)) {
      stateUpdate.selectedHRFPredictors = this.state.selectedHRFPredictors.filter(
        (x) => {
          return stateUpdate.analysis.predictorIds.indexOf(x.id) > -1;
        }
      );
      stateUpdate.analysis.hrfPredictorIds = this.state.analysis.hrfPredictorIds.filter(
        (x) => {
          return stateUpdate.analysis.predictorIds.indexOf(x) > -1;
        }
      );
    }

    stateUpdate.unsavedChanges = true;
    this.setState(stateUpdate);
  }

  updateHRFPredictorState = (value: any, filteredPredictors: Predictor[]) => {
    return this.updatePredictorState(value, filteredPredictors, true);
  }

  /* Main function to update application state. May split this up into
   smaller pieces if it gets too complex.

   When keepClean is true, don't set unsavedChanges to true. This is useful in situations
   like loading a new analysis (loadAnalysis function) where updateState is called but
   since state changes aren't really user edits we don't want to set unsavedChanges.
  */
  updateState = (attrName: keyof Store, keepClean = false) => (value: any) => {
    const { analysis, availableRuns, availablePredictors } = this.state;
    if (!editableStatus.includes(analysis.status) && !keepClean) {
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
              availableTasks: getTasks(data)
              // availablePredictors: []
            });
          })
          .catch(displayError);
      }
      if (updatedAnalysis.runIds.length !== analysis.runIds.length) {
        // If there was any change in selection of runs, fetch the associated predictors
        const runIds = updatedAnalysis.runIds.join(',');
        if (runIds) {
          this.setState({predictorsLoad: true});
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
    }

    stateUpdate[attrName] = value;
    if (!keepClean) stateUpdate.unsavedChanges = true;

    this.setState(stateUpdate);
  };

  tabChange = (activeKey) => {
    if (activeKey === 'overview' || this.state.predictorsLoad === false) {
      return;
    }
    const analysis = this.state.analysis;

    jwtFetch(`${domainRoot}/api/predictors?run_id=${analysis.runIds}`)
    .then((data: Predictor[]) => {
      message.success(
        `Fetched ${data.length} predictors associated with the selected runs`
      );
      const selectedPredictors = data.filter(
        p => analysis.predictorIds.indexOf(p.id) > -1
      );

      let selectedHRFPredictors: Predictor[] = [];
      if (analysis.hrfPredictorIds) {
        selectedHRFPredictors = data.filter(
          p => analysis.hrfPredictorIds.indexOf(p.id) > -1
        );
        // hrfPredictorIds comes in as a list of names from api, convert it to IDs here.
        analysis.hrfPredictorIds = selectedHRFPredictors.map(x => x.id);
      }

      this.setState({
        analysis: analysis,
        availablePredictors: data,
        selectedPredictors,
        selectedHRFPredictors,
        predictorsLoad: false
      });
      analysis.config = getUpdatedConfig(
        analysis.config,
        selectedPredictors.map(p => p.id)
      );
    })
    .catch(displayError);
  }

  render() {
    const {
      predictorsActive,
      transformationsActive,
      contrastsActive,
      modelingActive,
      reviewActive,
      activeTab,
      analysis,
      datasets,
      availableTasks,
      availableRuns,
      selectedTaskId,
      availablePredictors,
      selectedPredictors,
      selectedHRFPredictors,
      unsavedChanges
    } = this.state;

    const statusText: string = {
      DRAFT: 'This analysis has not yet been generated.',
      PENDING: 'This analysis has been submitted for generation and is being processed.',
      COMPILED: 'This analysis has been successfully generated'
    }[analysis.status];
    return (
      <div className="App">
        <Prompt
          when={unsavedChanges}
          message={'You have unsaved changes. Are you sure you want leave this page?'}
        />
        <Row type="flex" justify="center">
          <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}}>
            <h2>
              {analysis.status !== 'DRAFT' ? <Icon type="lock" /> : <Icon type="unlock" />}
              {`Analysis ID: ${analysis.analysisId || 'n/a'}`}
              <Space />
              <Button
                onClick={this.saveAnalysis({ compile: false })}
                disabled={!this.saveEnabled()}
                type={'primary'}
              >
                Save
              </Button>
              <Space />
              <Button
                hidden={!this.state.analysis.analysisId}
                onClick={this.confirmSubmission}
                type={'primary'}
                disabled={!this.submitEnabled()}
              >
                {unsavedChanges ? 'Save & Generate' : 'Generate'}
              </Button>
              <Space />
            </h2>
            <br />
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}}>
            <Tabs
              activeKey={activeTab}
              onTabClick={newTab => this.setState({ activeTab: newTab })}
              onChange={this.tabChange}
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
                  goToNextTab={() => {this.setState({ activeTab: 'predictors' }); this.tabChange('predictors'); }}
                />
              </TabPane>
              <TabPane tab="Predictors" key="predictors" disabled={!predictorsActive}>
                <PredictorSelector
                  availablePredictors={availablePredictors}
                  selectedPredictors={selectedPredictors}
                  updateSelection={this.updatePredictorState}
                  predictorsLoad={this.state.predictorsLoad}
                />
                <br/>
                <h3>HRF Variables:</h3>
                <PredictorSelector
                  availablePredictors={selectedPredictors}
                  selectedPredictors={selectedHRFPredictors}
                  updateSelection={this.updateHRFPredictorState}
                />
              </TabPane>
              <TabPane
                tab="Transformations"
                key="transformations"
                disabled={!transformationsActive}
              >
                <XformsTab
                  predictors={selectedPredictors}
                  xforms={analysis.transformations}
                  onSave={xforms => this.updateTransformations(xforms)}
                />
              </TabPane>
              <TabPane tab="Contrasts" key="contrasts" disabled={!transformationsActive}>
                <ContrastsTab
                  contrasts={analysis.contrasts}
                  predictors={selectedPredictors}
                  onSave={this.updateContrasts}
                />
              </TabPane>
              <TabPane tab="Options" key="modeling" disabled={!modelingActive}>
                <OptionsTab
                  analysis={analysis}
                  selectedPredictors={selectedPredictors}
                  updateConfig={this.updateConfig}
                  updateAnalysis={this.updateState('analysis')}
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
                <p>
                  {statusText}
                </p>
              </TabPane>
            </Tabs>
          </Col>
        </Row>
      </div>
    );
  }
}
