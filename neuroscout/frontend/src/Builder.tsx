 /*
 Top-level AnalysisBuilder component which contains all of the necessary state for editing
 an analysis.
*/
import { RouteComponentProps } from 'react-router';
import { createBrowserHistory } from 'history';
import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Modal, Icon, message } from 'antd';
import { Prompt } from 'react-router-dom';
import { OverviewTab } from './Overview';
import { PredictorSelector } from './Predictors';
import { ContrastsTab } from './Contrasts';
import { XformsTab } from './Transformations';
import { Review } from './Review';
import { Report } from './Report';
import { Status, Submit, Results } from './Status';
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
  AnalysisStatus,
  Transformation,
  Contrast,
  Block,
  BlockModel,
  BidsModel,
  ImageInput,
  TransformName,
  TabName
} from './coretypes';
import { displayError, jwtFetch, timeout } from './utils';
import { Space } from './HelperComponents';
import { config } from './config';
import { authActions } from './auth.actions';

const { TabPane } = Tabs;
const { Footer, Content } = Layout;
const tabOrder = ['overview', 'predictors', 'transformations', 'hrf', 'contrasts', 'review', 'submit'];

const history = createBrowserHistory();

// const logo = require('./logo.svg');
const domainRoot = config.server_url;
const EMAIL = 'user@example.com';
const PASSWORD = 'string';
const DEFAULT_SMOOTHING = 5;
const editableStatus = ['DRAFT', 'FAILED'];

const defaultConfig: AnalysisConfig = { smoothing: DEFAULT_SMOOTHING, predictorConfigs: {} };

// Create initialized app state (used in the constructor of the top-level App component)
let initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  predictorsLoad: false,
  transformationsActive: false,
  contrastsActive: false,
  hrfActive: false,
  submitActive: false,
  modelingActive: true,
  reviewActive: false,
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
    private: false,
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
  availableRuns: [],
  selectedTaskId: null,
  availablePredictors: [],
  selectedPredictors: [],
  selectedHRFPredictors: [],
  unsavedChanges: false,
  currentLevel: 'run',
  postReports: false,
  model: {
    blocks: [{
      level: 'run',
      transformations: [],
      contrasts: []
    }]
  },
  poll: true
});

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const authors = d.description.Authors ? d.description.Authors.join(', ') : 'No authors listed';
  const description = d.summary;
  const url = d.url;
  const id = d.id.toString();
  const { name, tasks } = d;
  return { id, name, authors, url, description, tasks };
};

// Get list of tasks from a given dataset
export const getTasks = (datasets: Dataset[], datasetId: string | null): Task[] => {
    let curDataset = datasets.find((x) => {
      return x.id === datasetId;
    });

    if (curDataset !== undefined) {
      return curDataset.tasks;
    }
    return [] as Task[];
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

export default class AnalysisBuilder extends React.Component<BuilderProps & RouteComponentProps<{}>, Store> {
  constructor(props: BuilderProps) {
    super(props);
    this.state = initializeStore();
    // Load analysis from server if an analysis id is specified in the props
    if (!!props.id) {
      jwtFetch(`${domainRoot}/api/analyses/${props.id}`)
        // .then(response => response.json() as Promise<ApiAnalysis>)
        .then((data: ApiAnalysis) => this.loadAnalysis(data))
        .then(() => {
          this.setState({model: this.buildModel()});
        })
        .catch(displayError);
    }

    jwtFetch(domainRoot + '/api/datasets?active_only=true')
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
    let availableTasks = getTasks(this.state.datasets, this.state.analysis.datasetId);

    let task: string[] = availableTasks.filter(
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
      if (hrfVariables.length > 0) {
        let hrfTransforms = {'name': 'ConvolveHRF' as TransformName, 'input': hrfVariables};
        // Right now we only want one HRF transform, remove all others to prevent duplicates
        blocks[0].transformations = blocks[0].transformations!.filter(x => x.name !== 'ConvolveHRF');
        blocks[0].transformations!.push(hrfTransforms);
      }
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

  // A one off poll for when the analysis is submitted.
  checkAnalysisStatus = async () => {
    while (this.state.poll) {
      let id = this.state.analysis.analysisId;
      if (id === undefined || this.state.analysis.status === undefined) {
        return;
      }
      jwtFetch(`${domainRoot}/api/analyses/${id}`, { method: 'get' })
        .then((data: ApiAnalysis) => {
          if (this.state.analysis.status !== data.status) {
            this.updateStatus(data.status);
            if (['DRAFT', 'SUBMITTING', 'PENDING'].indexOf(data.status) === -1) {
              this.setState({poll: false});
            }
          }
      })
      .catch(() => {
        // if fetch throws an error lets bail out. Redirect maybe?
        this.setState({poll: false});
        return;
      });
      await timeout(5000);
    }
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
      dataset_id: analysis.datasetId.toString(),
      status: analysis.status,
      runs: analysis.runIds,
      predictors: analysis.predictorIds,
      transformations: analysis.transformations,
      contrasts: analysis.contrasts,
      config: analysis.config,
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
      this.checkAnalysisStatus();
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
        let analysisId = this.state.analysis.analysisId;
        if (data.hash_id !== undefined) {
          analysisId = data.hash_id;
        }
        this.setState({
          analysis: {
            ...analysis,
            analysisId: analysisId,
            status: data.status,
            modifiedAt: data.modified_at
          },
          unsavedChanges: false
        });
        this.props.updatedAnalysis();
        if (data.hash_id !== undefined) {
          history.push('/builder/' + data.hash_id);
        }
      })
      .catch(displayError);
  };

  // Decode data returned by '/api/analyses/<id>' (ApiAnalysis) to convert it to the right shape (Analysis)
  // and fetch the associated runs
  loadAnalysis = (data: ApiAnalysis): Promise<Analysis> => {

    data.transformations = [];

    // Extract transformations and contrasts from within block object of response.
    let contrasts;
    let autoContrast;
    let hrfPredictorIds: string[] = [];
    if (data && data.model && data.model.blocks) {
      for (var i = 0; i < data.model.blocks.length; i++) {
        if (data.model.blocks[i].level !== this.state.currentLevel) {
          continue;
        }
        if (data.model.blocks[i].transformations) {
          data.transformations = data.model.blocks[i].transformations!.filter((x) => {
            return x.name !== 'ConvolveHRF' as TransformName;
          });
          let hrfTransforms = data.model.blocks[i].transformations!.filter((x) => {
            return x.name === 'ConvolveHRF' as TransformName;
          });
          if (hrfTransforms.length > 0) {
            hrfTransforms.map(x => x.input ? x.input.map(y => hrfPredictorIds.push(y)) : null);
          }
        }
        if (data.model.blocks[i].contrasts) {
          data.contrasts = data.model.blocks[i].contrasts;
        }
        if (data.model.blocks[i].auto_contrasts) {
          autoContrast = data.model.blocks[i].auto_contrasts;
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
      datasetId: data.dataset_id.toString(),
      runIds: data.runs ? data.runs : [],
      predictorIds: data.predictors ? data.predictors : [],
      hrfPredictorIds: hrfPredictorIds,
      config: data.config || defaultConfig,
      transformations: data.transformations,
      contrasts: data.contrasts || [],
      model: data.model,
      autoContrast: autoContrast
    };

    if (analysis.runIds.length > 0) {
      jwtFetch(`${domainRoot}/api/runs/${analysis.runIds[0]}`)
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
        // saveAnalysis({ compile: false})();
        saveAnalysis({ compile: true })();
      }
    });
  };

  generateButton = () => {
      return (
        <Button
          hidden={!this.state.analysis.analysisId}
          onClick={this.confirmSubmission}
          type={'primary'}
          disabled={!this.submitEnabled()}
        >
          {this.state.unsavedChanges ? 'Save & Generate' : 'Generate'}
        </Button>
      );
  };

  nextTab = (direction = 1) => {
    return (e) => {
      let nextIndex = tabOrder.indexOf(this.state.activeTab) + direction;
      let nextTab = tabOrder[nextIndex];
      let update = {activeTab: nextTab as TabName};
      update[nextTab + 'Active' ] = true;
      if (nextTab === 'review' && this.state.analysis.status === 'DRAFT') {
        this.saveAnalysis({compile: false})();
      }
      if (this.state.activeTab === 'overview') {
        // need name and runids
        if (this.state.analysis.name.length < 1) {
          // how
        }
        if (this.state.analysis.runIds.length < 1) {
        }
      }
      this.setState(update);
      this.tabChange(nextTab);
    };
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

  updateStatus = (status: string): void => {
    this.setState({
      analysis: { ...this.state.analysis, status: (status as AnalysisStatus)},
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

  runIdsFromModel = (availableRuns: Run[], input: ImageInput) => {
    let runIds: Run[] = availableRuns;
    if (!this.state.model || !this.state.model.input) {
      return [];
    }
    let keys = ['subject', 'session', 'run'];
    keys.map(key => {
      if (!input[key]) {return; }
      runIds = runIds.filter((x) => {
        if ((key !== 'run' && x[key] === undefined) || (key === 'run' && x.number === undefined)) {
          return true;
        }
        if (key === 'run') {
          return input[key]!.indexOf(parseInt(x.number, 10)) > -1;
        }
        return input[key].indexOf(x[key]) > -1;
      });
    });
    return runIds.map(x => x.id);
  }

  /* Main function to update application state. May split this up into
   smaller pieces if it gets too complex.

   When keepClean is true, don't set unsavedChanges to true. This is useful in situations
   like loading a new analysis (loadAnalysis function) where updateState is called but
   since state changes aren't really user edits we don't want to set unsavedChanges.
  */
  updateState = (attrName: keyof Store, keepClean = false) => (value: any) => {
    const { analysis, availableRuns, availablePredictors, datasets } = this.state;
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
            let availTasks = getTasks(datasets, updatedAnalysis.datasetId);

            if (updatedAnalysis.model && updatedAnalysis.model.input) {
              updatedAnalysis.runIds = this.runIdsFromModel(data, updatedAnalysis.model.input);
            } else {
              updatedAnalysis.runIds = data.map(x => x.id);
            }

            if (availTasks.length === 1) {
              this.setState({
                selectedTaskId: availTasks[0].id,
                predictorsLoad: true,
              });
            }

            this.setState({
              availableRuns: data,
              availablePredictors: [],
              selectedPredictors: []
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
        runIds: availableRuns.filter(r => r.task === value).map(r => r.id)
      });
    }

    stateUpdate[attrName] = value;
    if (!keepClean) stateUpdate.unsavedChanges = true;

    this.setState(stateUpdate);
  };

  tabChange = (activeKey) => {
    const analysis = this.state.analysis;
    if (activeKey === 'review') {
      // this.updateState('analysis')({ ...analysis, model: this.buildModel()});
      this.setState({model: this.buildModel()});
    }

    if (activeKey === 'overview' || this.state.predictorsLoad === false) {
      return;
    }

    jwtFetch(`${domainRoot}/api/predictors?run_id=${analysis.runIds}`)
    .then((data: Predictor[]) => {
      const selectedPredictors = data.filter(
        p => analysis.predictorIds.indexOf(p.id) > -1
      );

      let selectedHRFPredictors: Predictor[] = [];
      if (analysis.hrfPredictorIds) {
        selectedHRFPredictors = data.filter(
          p => analysis.hrfPredictorIds.indexOf(p.name) > -1
        );
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

  nextButton = (disabled = false) => {
    return (
      <Button type="primary" onClick={this.nextTab()} className="nextButton" disabled={disabled}>
        Next
      </Button>
    );
  }

  navButtons = (disabled = false) => {
    return (
      <div>
        <Button type="primary" onClick={this.nextTab(-1)}>
          Previous
        </Button>
        {this.nextButton(disabled)}
      </div>
    );
  }

  componentDidUpdate(prevProps, prevState) {
    // we really only need a valid JWT when creating the analysis
    if (this.state.analysis.status === 'DRAFT') {
      authActions.checkJWT();
    }
  }

  render() {
    let {
      predictorsActive,
      transformationsActive,
      contrastsActive,
      hrfActive,
      reviewActive,
      submitActive,
      modelingActive,
      activeTab,
      analysis,
      datasets,
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
    // Jump to submit/results tab if no longer a draft.
    if (analysis.status !== 'DRAFT' && activeTab === 'overview') {
      activeTab = 'submit';
    }
    let isDraft = analysis.status === 'DRAFT';
    return (
      <div className="App">
          <Prompt
            when={unsavedChanges}
            message={'You have unsaved changes. Are you sure you want leave this page?'}
          />
      <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
        <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
        <h3>

              <Button
                onClick={this.saveAnalysis({ compile: false })}
                disabled={!this.saveEnabled()}
                type={'primary'}
              >
                Save
              </Button>

                {`ID: ${analysis.analysisId || 'n/a'}`}

              </h3>
              <br />
            </Col>
          </Row>
          <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
            <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
              <Tabs
                activeKey={activeTab}
                onTabClick={newTab => this.setState({ activeTab: newTab })}
                onChange={this.tabChange}
                className="builderTabs"
                tabPosition="left"
              >
                {isDraft && <TabPane tab="Overview" key="overview" disabled={!isDraft}>
                  <OverviewTab
                    analysis={analysis}
                    datasets={datasets}
                    availableRuns={availableRuns}
                    selectedTaskId={selectedTaskId}
                    predictorsActive={predictorsActive}
                    updateAnalysis={this.updateState('analysis')}
                    updateSelectedTaskId={this.updateState('selectedTaskId')}
                  />
                  {this.nextButton(!(!!this.state.analysis.name && this.state.analysis.runIds.length > 0))}
                  <br/>
                </TabPane>}
                {isDraft && <TabPane tab="Predictors" key="predictors" disabled={!predictorsActive || !isDraft}>
                  <PredictorSelector
                    availablePredictors={availablePredictors}
                    selectedPredictors={selectedPredictors}
                    updateSelection={this.updatePredictorState}
                    predictorsLoad={this.state.predictorsLoad}
                  />
                  <br/>
                  {this.navButtons(!(selectedPredictors.length > 0))}
                  <br/>
                </TabPane>}
                {isDraft && <TabPane
                  tab="Transformations"
                  key="transformations"
                  disabled={!transformationsActive || !isDraft}
                >
                  <XformsTab
                    predictors={selectedPredictors}
                    xforms={analysis.transformations.filter(x => x.name !== 'ConvolveHRF')}
                    onSave={xforms => this.updateTransformations(xforms)}
                  />
                  <br/>
                  {this.navButtons()}
                  <br/>
                </TabPane>}
                {isDraft && <TabPane tab="HRF" key="hrf" disabled={!hrfActive || !isDraft}>
                  <PredictorSelector
                    availablePredictors={selectedPredictors}
                    selectedPredictors={selectedHRFPredictors}
                    updateSelection={this.updateHRFPredictorState}
                    selectedText="to be convolved with HRF "
                  />
                  <br/>
                  {this.navButtons()}
                  <br/>
                </TabPane>}
                {isDraft && <TabPane tab="Contrasts" key="contrasts" disabled={!contrastsActive || !isDraft}>
                  <ContrastsTab
                    analysis={analysis}
                    contrasts={analysis.contrasts}
                    predictors={selectedPredictors}
                    onSave={this.updateContrasts}
                    updateAnalysis={this.updateState('analysis')}
                  />
                  <br/>
                  {this.navButtons()}
                  <br/>
                </TabPane>}
                <TabPane tab="Review" key="review" disabled={((!reviewActive || !analysis.analysisId) && isDraft)}>
                  {this.state.model &&
                    <div>
                      <Report
                        analysisId={analysis.analysisId}
                        runIds={analysis.runIds}
                        postReports={this.state.postReports}
                      />
                      <Review
                        model={this.state.model}
                        unsavedChanges={this.state.unsavedChanges}
                        availablePredictors={this.state.availablePredictors}
                      />
                      <br/>
                      {isDraft ? this.navButtons() : this.nextButton()}
                      <br/>
                    </div>
                  }
                </TabPane>
                <TabPane tab={isDraft ? 'Run' : 'Results'} key="submit" disabled={!submitActive && isDraft}>
                  <Results
                    status={analysis.status}
                    analysisId={analysis.analysisId}
                    confirmSubmission={this.confirmSubmission}
                    private={analysis.private || false}
                    updateStatus={this.updateStatus}
                  />
                </TabPane>
              </Tabs>
            </Col>
          </Row>
        </div>
    );
  }
}
