 /*
 Top-level AnalysisBuilder component which contains all of the necessary state for editing
 an analysis.
*/
import { RouteComponentProps } from 'react-router';
import { Redirect } from 'react-router-dom';
import { createBrowserHistory } from 'history';
import * as React from 'react';
import {
  Tag, Tabs, Row, Button, Modal, Icon, message, Tooltip, Form, Input, Collapse
} from 'antd';
import { Prompt } from 'react-router-dom';
import Reflux from 'reflux';

import { authActions } from '../auth.actions';
import { AuthStore } from '../auth.store';
import { api } from '../api';
import { OverviewTab } from './Overview';
import { PredictorSelector } from './Predictors';
import { validateContrast } from './ContrastEditor';
import { ContrastsTab } from './Contrasts';
import { XformsTab, validateXform } from './Transformations';
import { Review } from './Review';
import { Report } from './Report';
import { StatusTab } from './Status';
import { BibliographyTab } from './Bibliography';
import {
  Store,
  Analysis,
  Dataset,
  Task,
  Run,
  Predictor,
  ApiAnalysis,
  AnalysisConfig,
  Transformation,
  Contrast,
  Step,
  BidsModel,
  ImageInput,
  TransformName,
  TabName
} from '../coretypes';
import { displayError, jwtFetch, timeout, isDefined } from '../utils';
import { MainCol, Space } from '../HelperComponents';
import { config } from '../config';

const { TabPane } = Tabs;
const Panel = Collapse.Panel;
const FormItem = Form.Item;
const tabOrder = ['overview', 'predictors', 'transformations', 'hrf', 'contrasts', 'review', 'submit'];

const history = createBrowserHistory();

// const logo = require('./logo.svg');
const domainRoot = config.server_url;
const DEFAULT_SMOOTHING = 5;
const editableStatus = ['DRAFT', 'FAILED'];

const defaultConfig: AnalysisConfig = { smoothing: DEFAULT_SMOOTHING, predictorConfigs: {} };

class AnalysisId extends React.Component<{id: undefined | string}, {}> {
  render() {
    return (<div>ID: {this.props.id ? this.props.id : 'n/a'}</div>);
  }
}

// Create initialized app state (used in the constructor of the top-level App component)
let initializeStore = (): Store => ({
  activeTab: 'overview',
  predictorsActive: false,
  predictorsLoad: false,
  loadInitialPredictors: true,
  transformationsActive: false,
  contrastsActive: false,
  hrfActive: false,
  submitActive: false,
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
    dummyContrast: false,
    model: {
      Steps: [{
        Level: 'Run',
        Transformations: [],
        Contrasts: []
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
  currentLevel: 'Run',
  postReports: false,
  model: {
    Steps: [{
      Level: 'Run',
      Transformations: [],
      Contrasts: []
    }]
  },
  poll: true,
  saveFromUpdate: false,
  activeXformIndex: -1,
  activeContrastIndex: -1,
  xformErrors: [],
  contrastErrors: [],
  fillAnalysis: false,
  analysis404: false,
  doTooltip: false,
});

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

type editDetailsProps = {
  name: string,
  description: string,
  updateAnalysis: (value: Partial<Analysis>, unsavedChanges: boolean, save: boolean) => void
};
type editDetailsState = {newName: string, newDescription: string, visible: string[] | string};
class EditDetails extends React.Component<editDetailsProps, editDetailsState> {
  constructor(props: editDetailsProps) {
    super(props);
    this.state = this.init(props);
  }

  init(props: editDetailsProps) {
    return {newName: props.name, newDescription: props.description, visible: []};
  }

  update() {
    this.props.updateAnalysis({name: this.state.newName, description: this.state.newDescription}, false, true);
  }

  onChange = (e: any) => {
    this.setState({visible: e});
  };

  render() {
    return (
      <div>
      <Collapse bordered={false} activeKey={this.state.visible} onChange={this.onChange}>
        <Panel header="Edit Analysis Details" key="1">
          <Form layout="vertical">
            <FormItem label="Name" required={true}>
              <Input
                placeholder="Name your analysis"
                value={this.state.newName}
                onChange={(e) => this.setState({newName: e.currentTarget.value})}
                required={true}
                min={1}
              />
            </FormItem>
            <FormItem label="Description">
              <Input.TextArea
                placeholder="Description of your analysis"
                value={this.state.newDescription}
                autosize={{ minRows: 2, maxRows: 10 }}
                onChange={(e) => this.setState({newDescription: e.currentTarget.value})}
              />
            </FormItem>
          </Form>
          <Button type="primary" onClick={() => {this.update(); this.setState({visible: ''}); }} size={'small'}>
            Save Changes
          </Button>
        </Panel>
      </Collapse>
      </div>
    );
  }
}

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
  userOwns?: boolean;
  doTour?: boolean;
  datasets: Dataset[];
};

export default class AnalysisBuilder extends Reflux.Component<any, BuilderProps & RouteComponentProps<{}>, Store> {
  constructor(props: BuilderProps) {
    super(props);
    this.state = initializeStore();
    this.store = AuthStore;
    // Load analysis from server if an analysis id is specified in the props
    if (!!props.id) {
      jwtFetch(`${domainRoot}/api/analyses/${props.id}`)
      // .then(response => response.json() as Promise<ApiAnalysis>)
      .then((data: ApiAnalysis) => {
        if ((data as any).statusCode === 404) {
          this.setState({analysis404: true});
          return;
        } else {
          this.loadAnalysis(data);
          return data;
        }
      })
      .then((data: ApiAnalysis) => {
        if (this.state.analysis404) { return; }
        if (editableStatus.includes(data.status)) {
          this.setState({model: this.buildModel()});
        } else if (data.model !== undefined) {
          this.setState({model: data.model!});
        }
        if (data.status === 'FAILED') {
          this.setState({activeTab: 'submit'});
        }
      })
      .catch(displayError);
    }
  }

  saveEnabled = (): boolean => this.state.unsavedChanges && editableStatus.includes(this.state.analysis.status);
  submitEnabled = (): boolean => editableStatus.includes(this.state.analysis.status);

  buildModel = (): BidsModel => {

    let availableTasks = getTasks(this.props.datasets, this.state.analysis.datasetId);

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
    let X: string[];
    X = this.state.analysis.predictorIds.map(id => {
      let found = this.state.availablePredictors.find(elem => elem.id === id);
      if (found) {
        return found.name;
      }
      return '';
    });
    X = X.filter(x => x !== '');

    let steps: Step[] = [
      {
        Level: 'Run',
        Transformations: this.state.analysis.transformations,
        Contrasts: this.state.analysis.contrasts,
        Model: {
          X: X,
        }
      }
    ];

    steps.push({
      Level: 'Subject',
      DummyContrasts: {
        Type: 'FEMA'
      }
    });

    steps.push({
      Level: 'Dataset',
      DummyContrasts: {
        Type: 't'
      }
    });

    if (this.state.analysis.hrfPredictorIds) {
      let hrfX: string[];
      hrfX = this.state.analysis.hrfPredictorIds.map(id => {
        let found = this.state.availablePredictors.find(elem => elem.id === id);
        if (found) {
          return found.name;
        }
        return '';
      });
      hrfX = hrfX.filter(x => x !== '');
      if (hrfX.length > 0) {
        let hrfTransforms = {'Name': 'Convolve' as TransformName, 'Input': hrfX};
        // Right now we only want one HRF transform, remove all others to prevent duplicates
        steps[0].Transformations = steps[0].Transformations!.filter(x => x.Name !== 'Convolve');
        steps[0].Transformations!.push(hrfTransforms);
      }
    }

    let imgInput: ImageInput = {};
    if (runs.length > 0) {
      imgInput.Run = runs;
    }

    if (sessions.length > 0) {
      imgInput.Session = sessions;
    }

    if (subjects.length >  0) {
      imgInput.Subject = subjects;
    }

    if (task[0]) {
      imgInput.Task = task[0];
    }

    return {
      Name: this.state.analysis.name,
      Description: this.state.analysis.description,
      Input: imgInput,
      Steps: steps,
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
            this.updateAnalysis({'status': data.status});
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
  saveAnalysis = ({ compile = false, build = true }) => (): Promise<boolean> => {
    /*
    if ((!compile && !this.saveEnabled()) || (compile && !this.submitEnabled())) {
      return;
    }
    */

    const analysis = this.state.analysis;
    if (analysis.datasetId === null) {
      displayError(Error('Analysis cannot be saved without selecting a dataset'));
      return new Promise(() => {return false; });
    }

    if (!analysis.name) {
      displayError(Error('Analysis cannot be saved without a name'));
      return new Promise(() => {return false; });
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

    if (this.state.fillAnalysis === false) {
      apiAnalysis.model = this.buildModel();
    } else {
      apiAnalysis.predictors = [];
    }

    // const method = analysis.analysisId ? 'put' : 'post';
    let method: string;
    let url: string;
    if (compile && analysis.analysisId) {
      if (analysis.analysisId === undefined) {
        return new Promise(() => {return false; });
      }
      // Submit for compilation
      url = `${domainRoot}/api/analyses/${analysis.analysisId}/compile?build=${build}`;
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
    return jwtFetch(url, { method, body: JSON.stringify(apiAnalysis) })
      // .then(response => response.json())
      .then((data: ApiAnalysis & { statusCode: number }) => {
        if (data.statusCode !== 200) {
          if (compile) {
            this.setState({analysis: {...analysis, status: 'DRAFT'}});
          }
          throw new Error('Oops...something went wrong. Analysis was not saved.');
        }
        if (compile) {
          message.success('Analysis submitted for generation');
        }
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
          postReports: analysis.contrasts.length > 0,
          unsavedChanges: false
        });
        // will this mess with /fill workflow?
        // can't remember reason behind having to call this so often
        this.props.updatedAnalysis();

        if (data.hash_id !== undefined) {
          history.push('/builder/' + data.hash_id);
        }
      })
      .then(() => {return true; })
      .catch((err) => {
        displayError(err);
        return false;
      });
  };

  // Decode data returned by '/api/analyses/<id>' (ApiAnalysis) to convert it to the right shape (Analysis)
  // and fetch the associated runs
  loadAnalysis = (data: ApiAnalysis): Promise<Analysis> => {
    if (this.state.analysis404) { return Promise.reject('404'); }
    data.transformations = [];

    // Extract transformations and contrasts from within step object of response.
    let contrasts;
    let dummyContrast;
    let hrfPredictorIds: string[] = [];
    if (data && data.model && data.model.Steps) {
      for (var i = 0; i < data.model.Steps.length; i++) {

        if (data.model.Steps[i].Level !== this.state.currentLevel) {
          continue;
        }

        if (data.model.Steps[i].Transformations) {
          data.transformations = data.model.Steps[i].Transformations!.filter((x) => {
            return x.Name !== 'Convolve' as TransformName;
          });

          let hrfTransforms = data.model.Steps[i].Transformations!.filter((x) => {
            return x.Name === 'Convolve' as TransformName;
          });
          if (hrfTransforms.length > 0) {
            hrfTransforms.map(x => x.Input ? x.Input.map(y => hrfPredictorIds.push(y)) : null);
          }
        }

        if (data.model.Steps[i].Contrasts) {
          data.contrasts = data.model.Steps[i].Contrasts;
        }

        if (data.model.Steps[i].DummyContrasts) {
          dummyContrast = data.model.Steps[i].DummyContrasts;
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
      dummyContrast: dummyContrast,
      private: data.private
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
    this.setActiveTabs(analysis);
    return Promise.resolve(analysis);
  };

  setActiveTabs = (analysis: Analysis) => {
    if (analysis.contrasts.length) {
      this.setState({
        transformationsActive: true,
        contrastsActive: true,
        hrfActive: true,
        reviewActive: true
      });
    }
  }

  confirmSubmission = (build: boolean): void => {
    if (!this.submitEnabled()) return;
    const { saveAnalysis } = this;
    Modal.confirm({
      title: 'Are you sure you want to submit the analysis?',
      content: `Once you submit an analysis you will no longer be able to modify it.
                You will, however, be able to clone it as a starting point for a new analysis.`,
      okText: 'Yes',
      cancelText: 'No',
      onOk() {
        saveAnalysis({ compile: true, build: build })();
      }
    });
  };

  nextTab = (direction = 1) => {
    return (e) => {
      let nextIndex = tabOrder.indexOf(this.state.activeTab) + direction;
      let nextTab = tabOrder[nextIndex];
      let update = {activeTab: nextTab as TabName};
      update[nextTab + 'Active' ] = true;
      if (this.state.activeTab === 'overview') {
        // need name and runids
        if (this.state.analysis.name.length < 1) {
          // how
        }
        if (this.state.analysis.runIds.length < 1) {
        }
      } else if (!this.preTabChange(nextTab as TabName)) {
        return;
      }
      this.setState(update);
      this.postTabChange(nextTab);
    };
  };

  /* we can change tabs by clicking next/back or on tab itself. Before we change some tabs we need to validate their
   * current contents
   */
  onTabClick = (newTab: TabName) => {
    if (!this.preTabChange(newTab)) {
      return;
    }
    this.setState({ activeTab: newTab });
  }

  analysisToApiAnalysis = (analysis): ApiAnalysis => {
    let apiAnalysis: ApiAnalysis = {
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
    return apiAnalysis;
  }

  /* when state.fillAnalysis is true and a tab change occurs this function isn called.
   * First we save the analysis, with state.fillAnalysis true this clears out predictors in
   * the analysis but leaves predictorIds alone in the model, a prerequisite for /fill endpoint
   * to work. We then post to /fill, and attempt to reload the analysis from what /fill returns.
   */
  fillAnalysis = () => {
    let url = `${domainRoot}/api/analyses/${this.state.analysis.analysisId}/fill`;
    this.saveAnalysis({compile: false, build: false})()
    .then((res) => {
      if (res) {
        return jwtFetch(url, { method: 'post', body: {partial: true, dryrun: false}});
      }
      return;
    })
    .then((res) => {
      return this.loadAnalysis(res);
    })
    .then((newAnalysis) => {
      this.updateAnalysis(newAnalysis);
    })
    .catch((err) => {
      // tslint:disable-next-line:no-console
      console.log(`error: ${err}`);
    });
    this.setState({fillAnalysis: false});
  }

  // run any time we attempt to leave tab
  // xform and contrast checks are more or less the same save validate funciton call...
  preTabChange = (nextTab: TabName) => {
    let errors: string[] = [];
    if (this.state.activeTab === 'transformations') {
      if (this.state.activeXform === undefined) {
        return true;
      }
      errors = validateXform(this.state.activeXform);
      if (errors.length > 0) {
        this.setState({xformErrors: errors});
        return false;
      }
      let newXforms = this.state.analysis.transformations;
      if (this.state.activeXformIndex < 0) {
        newXforms.push({...this.state.activeXform});
      } else {
        newXforms[this.state.activeXformIndex] = {...this.state.activeXform};
      }
      this.updateTransformations(newXforms);
    } else if (this.state.activeTab === 'contrasts') {
      if (this.state.activeContrast === undefined) {
        if (this.state.analysis.contrasts.length > 0) {
          return true;
        }
        if (tabOrder.indexOf(nextTab) <= tabOrder.indexOf('contrasts')) {
          return true;
        }
        this.setState({contrastErrors: ['Minimum of one contrast required.']});
        return false;
      }
      errors = validateContrast(this.state.activeContrast);
      if (errors.length > 0) {
        this.setState({contrastErrors: errors});
        return false;
      }
      let newContrasts = this.state.analysis.contrasts;
      if (this.state.activeContrastIndex < 0) {
        newContrasts.push({...this.state.activeContrast});
      } else {
        newContrasts[this.state.activeContrastIndex] = {...this.state.activeContrast};
      }
      this.updateContrasts(newContrasts);
    }
    return true;
  }

  /* The updateAnalysis inside Overview is doing the same as the following updateAnalysis and should be replaced with
      this one. Also the update xforms and contrasts after it could be replaced with this updateAnalysis.
   */
  updateAnalysis = (value: Partial<Analysis>, unsavedChanges = false, save = false) => {
    let updatedAnalysis = { ...this.state.analysis, ...value };
    this.updateState('analysis', false, save)(updatedAnalysis);
  }

  updateTransformations = (xforms: Transformation[]): void => {
    this.setState({
      analysis: { ...this.state.analysis, transformations: xforms },
      activeXform: undefined,
      activeXformIndex: -1,
      unsavedChanges: true
    });
  };

  updateContrasts = (contrasts: Contrast[]): void => {
    this.setState({
      analysis: { ...this.state.analysis, contrasts },
      activeContrast: undefined,
      activeContrastIndex: -1,
      unsavedChanges: true
    });
  };

  updatePredictorState = (value: Predictor[], filteredPredictors: Predictor[], hrf: boolean = false) => {
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
    if (!this.state.model || !this.state.model.Input) {
      return [];
    }
    let keys = ['Subject', 'Session', 'Run'];
    keys.map(key => {
      if (!input[key]) {return; }
      runIds = runIds.filter((x) => {
        if ((key !== 'Run' && !x[key]) || (key === 'Run' && !x.number)) {
          return true;
        }
        if (key === 'Run') {
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
  updateState = (attrName: keyof Store, keepClean = false, saveToAPI = false) => (value: any) => {
    const { analysis, availableRuns, availablePredictors } = this.state;
    const { datasets } = this.props;
    /*
    if (!editableStatus.includes(analysis.status) && !keepClean) {
      message.warning('This analysis is locked and cannot be edited');
      return;
    }
    */
    let stateUpdate: any = {};
    if (attrName === 'analysis') {
      const updatedAnalysis: Analysis = value;
      if (updatedAnalysis.datasetId !== analysis.datasetId) {
        // If a new dataset is selected we need to fetch the associated runs
        jwtFetch(`${domainRoot}/api/runs?dataset_id=${updatedAnalysis.datasetId}`)
          .then((data: Run[]) => {
            let availTasks = getTasks(datasets, updatedAnalysis.datasetId);
            updatedAnalysis.runIds = data.map(x => x.id);
            if (updatedAnalysis.model && updatedAnalysis.model.Input) {
              if (analysis.datasetId !== null) {
                stateUpdate.fillAnalysis = true;
              } else {
                updatedAnalysis.runIds = this.runIdsFromModel(data, updatedAnalysis.model.Input);
              }
            }
            if (availTasks.length === 1) {
              stateUpdate = {
                ...stateUpdate,
                selectedTaskId: availTasks[0].id,
                predictorsLoad: true,
              };
            }

            stateUpdate = {
              ...stateUpdate,
              availableRuns: data,
              availablePredictors: [],
              selectedPredictors: []
            };
            this.setState(stateUpdate);
          })
          .catch(displayError);
      }
      if (updatedAnalysis.runIds.length !== analysis.runIds.length) {
        // If there was any change in selection of runs, fetch the associated predictors
        const runIds = updatedAnalysis.runIds.join(',');
        if (runIds) {
          stateUpdate.predictorsLoad = true;
        } else {
          stateUpdate.availablePredictors = [];
        }
      }
      if (updatedAnalysis.predictorIds.length !== this.state.selectedPredictors.length
          && this.state.availablePredictors.length > 0) {
        stateUpdate.selectedPredictors = this.state.availablePredictors.filter((x) => {
          return updatedAnalysis.predictorIds.includes(x.id);
        });
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
    if (saveToAPI) stateUpdate.saveFromUpdate = true;

    this.setState(stateUpdate);
  };

  postTabChange = (activeKey) => {
    const analysis = this.state.analysis;
    if (this.state.fillAnalysis) {
      this.fillAnalysis();
    } else if (editableStatus.includes(this.state.analysis.status)) {
      this.setState({model: this.buildModel()});
      if (editableStatus.includes(this.state.analysis.status) && this.state.unsavedChanges) {
        this.saveAnalysis({compile: false})();
      }
    }

    if (activeKey === 'overview' || this.state.predictorsLoad === false) {
      return;
    } else {
      this.loadPredictors();
    }
  }

  loadPredictors = () => {
    let analysis = this.state.analysis;
    let runIds = this.state.analysis.runIds;
    api.getPredictors(runIds)
    .then((data: (Predictor[] | null)) => {
      if (data === null) {
        return;
      }

      // If there is a statusCode we do not have a list of predictors
      if ((data as any).statusCode === undefined) {
        this.setState({
          predictorsLoad: false
        });
        return;
      }

      // merge predictor collection predictors into available predictors
      if (this.state.auth && this.state.auth.predictorCollections) {
        let userPredictors = this.state.auth.predictorCollections.filter(x => {
          return x.predictors !== undefined &&
          x.predictors.length > 0 &&
          x.predictors[0].dataset_id + '' === this.state.analysis.datasetId;
        }).map(x => x.predictors).filter(isDefined).flat().map(predictor => {
          if (!data.some((elem => elem.id === predictor.id))) {
            data.push(predictor);
          }
        });
      }

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

  nextbackButtons = (disabled = false, prev = true) => {
    return (
      <Button.Group style={{'float': 'right'}}>
        {prev &&
          <Button type="primary" onClick={this.nextTab(-1)}>
            Previous
          </Button>
        }
        <Button type="primary" onClick={this.nextTab()} className="nextButton" disabled={disabled}>
          Next
        </Button>
      </Button.Group>
    );
  }

  navButtons = (disabled = false, prev = true) => {
    let analysisId: string | undefined = undefined;
    if (this.state.analysis && this.state.analysis.analysisId) {
      analysisId = this.state.analysis.analysisId;
    }
    return (
      <div>
        <Button
          onClick={this.saveAnalysis({ compile: false })}
          disabled={!this.saveEnabled()}
          type={'primary'}
        >
          Save
        </Button>
        <Space/>
        <Tag><AnalysisId id={analysisId}/></Tag>
        {this.nextbackButtons(disabled, prev)}
      </div>
    );
  }

  addAllHRF = () => {
    // create HRF convolution transform for all variables that aren't from fmriprep
    let predictors = this.state.selectedPredictors.filter(x => x.source !== 'fmriprep');
    this.updatePredictorState(predictors, this.state.selectedPredictors, true);
  }

  componentDidUpdate(prevProps, prevState) {
    // we really only need a valid JWT when creating the analysis
    if (editableStatus.includes(this.state.analysis.status)) {
      authActions.checkJWT();
    }

    if (this.state.saveFromUpdate) {
      this.saveAnalysis({compile: false})();
      this.setState({saveFromUpdate: false});
    }
    if ((this.state.loadInitialPredictors === true)
      && (prevState.analysis.runIds.length !== this.state.analysis.runIds.length)) {
      this.loadPredictors();
      this.setState({loadInitialPredictors: false});
    }
  }
//
  componentDidMount() {
    if (this.props.doTour) {
      this.setState({doTooltip: true});
    }
  }

  componentWillUnmount() {
    this.setState({doTooltip: false});
  }

  render() {
    if (this.state.analysis404) {
      return <Redirect to="/builder/" />;
    }
    let {
      predictorsActive,
      transformationsActive,
      contrastsActive,
      hrfActive,
      reviewActive,
      submitActive,
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

    let isDraft = (analysis.status === 'DRAFT');
    let isFailed = (analysis.status === 'FAILED');
    let isEditable = editableStatus.includes(analysis.status);
    // Jump to submit/status tab if no longer editable.
    if (!isEditable && activeTab === 'overview') {
      activeTab = 'review';
      this.postTabChange(activeTab);
    }

    return (
      <div className="App">
          <Prompt
            when={unsavedChanges}
            message={'You have unsaved changes. Are you sure you want leave this page?'}
          />
          <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
            <MainCol>
              <Tabs
                activeKey={activeTab}
                onTabClick={newTab => this.onTabClick(newTab)}
                onChange={this.postTabChange}
                className="builderTabs"
                tabPosition="left"
              >
                {isEditable && <TabPane tab="Overview" key="overview" disabled={!isEditable}>
                  <h2>Overview</h2>
                  <OverviewTab
                    analysis={analysis}
                    datasets={this.props.datasets}
                    availableRuns={availableRuns}
                    selectedTaskId={selectedTaskId}
                    predictorsActive={predictorsActive}
                    updateAnalysis={this.updateState('analysis')}
                    updateSelectedTaskId={this.updateState('selectedTaskId')}
                  />
                  {this.navButtons(!(!!this.state.analysis.name && this.state.analysis.runIds.length > 0), false)}
                  <br/>
                </TabPane>}
                {isEditable &&
                <TabPane
                  tab="Predictors"
                  key="predictors"
                  disabled={(!predictorsActive || !isEditable) && !isFailed}
                >
                  <h2>Select Predictors&nbsp;&nbsp;
                  {this.state.activeTab === ('predictors' as TabName) &&
                  <Tooltip
                   title={'Use the search bar to find and select predictors to add to your analysis.\
                   For example, try searching for "face" or "fmriprep"'}
                   defaultVisible={this.state.doTooltip && this.state.activeTab === ('predictors' as TabName)}
                  >
                    <Icon type="info-circle" style={{ fontSize: '15px'}}/>
                  </Tooltip>
                  }
                  </h2>
                  <PredictorSelector
                    availablePredictors={availablePredictors}
                    selectedPredictors={selectedPredictors}
                    updateSelection={this.updatePredictorState}
                    predictorsLoad={this.state.predictorsLoad || this.state.fillAnalysis}
                  />
                  <br/>
                  {this.navButtons(!(selectedPredictors.length > 0))}
                  <br/>
                </TabPane>}
                {isEditable && <TabPane
                  tab="Transformations"
                  key="transformations"
                  disabled={(!transformationsActive || !isEditable) && !isFailed}
                >
                  <h2>Add Transformations&nbsp;&nbsp;
                  {this.state.activeTab === ('transformations' as TabName) &&
                  <Tooltip
                   title={'Add transformations to sequentially modify your predictors \
                   prior to constructing the final design matrix.'}
                   defaultVisible={this.state.doTooltip && this.state.activeTab === ('transformations' as TabName)}
                  >
                    <Icon type="info-circle" style={{ fontSize: '15px'}}/>
                  </Tooltip>
                  }
                  </h2>
                  <XformsTab
                    predictors={selectedPredictors}
                    xforms={analysis.transformations.filter(x => x.Name !== 'Convolve')}
                    onSave={xforms => this.updateTransformations(xforms)}
                    activeXformIndex={this.state.activeXformIndex}
                    activeXform={this.state.activeXform}
                    xformErrors={this.state.xformErrors}
                    updateBuilderState={this.updateState}
                  />
                  <br/>
                  {this.navButtons()}
                  <br/>
                </TabPane>}
                {isEditable && <TabPane tab="HRF" key="hrf" disabled={(!hrfActive || !isEditable) && !isFailed}>
                  <h2>HRF Convolution&nbsp;&nbsp;
                  {this.state.activeTab === ('hrf' as TabName) &&
                  <Tooltip
                   title={'Select which variables to convolve with the hemodynamic response function. \
                   To convolve all variables that are not fMRIPrep confounds, \
                   click "Select All Non-Confounds"'}
                   defaultVisible={this.state.doTooltip && this.state.activeTab === ('hrf' as TabName)}
                  >
                    <Icon type="info-circle" style={{ fontSize: '15px'}}/>
                  </Tooltip>
                  }
                  </h2>
                  <PredictorSelector
                    availablePredictors={selectedPredictors}
                    selectedPredictors={selectedHRFPredictors}
                    updateSelection={this.updateHRFPredictorState}
                  />
                  <br/>
                  <p>
                  <Button type="default" onClick={this.addAllHRF}>
                    <Icon type="plus" /> Select All Non-Confounds
                  </Button>
                  </p>
                  {this.navButtons()}
                  <br/>
                </TabPane>}
                {isEditable && <TabPane
                  tab="Contrasts"
                  key="contrasts"
                  disabled={(!contrastsActive || !isEditable) && !isFailed}
                >
                  <h2>Add Contrasts&nbsp;&nbsp;
                  {this.state.activeTab === ('contrasts' as TabName) &&
                  <Tooltip
                   title={'Here you can define statistical contrasts to compute from the fitted parameter estimates.\
                   To create identity contrasts [1, 0] for each predictor, use "Generate Automatic Contrasts"'}
                   defaultVisible={this.state.doTooltip && this.state.activeTab === ('contrasts' as TabName)}
                  >
                    <Icon type="info-circle" style={{ fontSize: '15px'}}/>
                  </Tooltip>
                  }
                  </h2>
                  <ContrastsTab
                    analysis={analysis}
                    contrasts={analysis.contrasts}
                    predictors={selectedPredictors}
                    onSave={this.updateContrasts}
                    updateAnalysis={this.updateState('analysis')}
                    activeContrastIndex={this.state.activeContrastIndex}
                    activeContrast={this.state.activeContrast}
                    contrastErrors={this.state.contrastErrors}
                    updateBuilderState={this.updateState}
                  />
                  <br/>
                  {this.navButtons(!(this.state.analysis.contrasts.length > 0))}
                  <br/>
                </TabPane>}
                <TabPane tab="Review" key="review" disabled={((!reviewActive || !analysis.analysisId) && isDraft)}>
                  {this.state.model && this.state.activeTab === ('review' as TabName) &&
                    <div>
                      <Report
                        analysisId={analysis.analysisId}
                        runIds={analysis.runIds}
                        postReports={this.state.activeTab === ('review' as TabName)}
                        defaultVisible={this.state.doTooltip && this.state.activeTab === ('review' as TabName)}
                      />
                      <Review
                        model={this.state.model}
                        unsavedChanges={this.state.unsavedChanges}
                        availablePredictors={this.state.availablePredictors}
                        dataset={this.props.datasets.find((x => x.id === this.state.analysis.datasetId))}
                      />
                      <br/>
                      {isEditable && this.navButtons(false, isEditable)}
                      <br/>
                    </div>
                  }
                </TabPane>
                <TabPane
                  tab={isEditable ? 'Run' : 'Status'}
                  key="submit"
                  disabled={!submitActive && isDraft}
                >
                  <h2>Finalize and Run</h2>
                  <StatusTab
                    status={analysis.status}
                    analysisId={analysis.analysisId}
                    confirmSubmission={this.confirmSubmission}
                    private={analysis.private || false}
                    updateAnalysis={this.updateAnalysis}
                    userOwns={this.props.userOwns}
                  >
                  {this.props.userOwns && !isDraft &&
                      <EditDetails
                        name={analysis.name}
                        description={analysis.description}
                        updateAnalysis={this.updateAnalysis}
                      />
                  }
                  </StatusTab>
                </TabPane>
                {!isEditable &&  <TabPane
                  tab="Bibliography"
                  key="bib"
                >
                  <h2>Bibliography</h2>
                  <BibliographyTab
                    analysisId={analysis.analysisId}
                  />
                </TabPane>}
              </Tabs>
            </MainCol>
          </Row>
        </div>
    );
  }
}
