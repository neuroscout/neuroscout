
import * as React from 'react';
import { message, Button, Collapse, Card } from 'antd';

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
  Step,
  StepModel,
  BidsModel,
  ImageInput,
  TransformName
} from './coretypes';

import { displayError, jwtFetch, alphaSort } from './utils';

const Panel = Collapse.Panel;

interface ReviewProps {
  model: BidsModel;
  unsavedChanges: boolean;
  availablePredictors: Predictor[];
}

class ModelInput extends React.Component<{model: BidsModel}, {}> {
  render() {
    if (this.props.model.input === undefined) {
      return;
    }
    let input = this.props.model.input;
    let runs = input.run ? input.run.sort().map(x => <li key={x}>{x}</li>) : [];
    let subjects = input.subject ? alphaSort(input.subject).join(', ') : [];
    let sessions = input.session ? alphaSort(input.session).join(', ') : [];

    return (
      <div>
        <Card title="Task" key="task">{input.task ? input.task : ''}</Card>
        {(runs.length > 0) && <Card title="Runs" key="runs"><ul>{runs}</ul></Card>}
        {(subjects.length > 0) && <Card title="Subjects" key="subjects"><p>{subjects}</p></Card>}
        {(sessions.length > 0) && <Card title="Sessions" key="sessions"><p>{sessions}</p></Card>}
      </div>
    );
  }
}

/* Object needs to have name as a key  */
class ReviewObjects extends React.Component<{input: (Transformation | Contrast)[], autoContrasts?: boolean}, {}> {
  render() {
    let input = this.props.input;
    let display: any[] = [];
    if (this.props.autoContrasts !== undefined) {
      display.push(<div key="ac"><h3>Auto Contrasts:</h3>{'' + this.props.autoContrasts}</div>);
    }
    input.map((x, i) => display.push(<div key={i}><h3>{x.name}:</h3><pre>{JSON.stringify(x, null, 2)}</pre></div>));

    return (
      <div>{display}</div>
    );
  }
}

class ModelStep extends React.Component<{step: Step}, {}> {
  render() {
    let step = this.props.step;
    let xforms: any = '';
    if (step.transformations !== undefined) {
        xforms = (
          <ReviewObjects input={step.transformations}/>
        );
    }
    return (
      <div>
        <h3>Transformations</h3>
        {xforms}
      </div>
    );
  }
}

// <Panel header="Steps" key="steps"><ModelSteps steps={steps as Step[]}/></Panel>
// Only displaying run level step right now so this is unused.
class ModelSteps extends React.Component<{steps: Step[]}, {}> {
  render() {
      if (this.props.steps === undefined) {
        return;
      }
      let steps = this.props.steps;
      let display: any[] = [];
      steps.map((x, i) => display.push(
        <Panel header={`${x.level} Level`} key={i.toString()}><ModelStep step={x}/></Panel>)
      );
      return (
        <Collapse>
          {display}
        </Collapse>
      );
  }
}

// In the future this will include the new named outputs from transformations.
class Variables extends React.Component<{model: BidsModel, available: Predictor[]}, {}> {
  render() {
    let { model, available } = this.props;
    let modelVars: string[] = [];
    if (model.steps && model.steps[0] && model.steps[0].model && model.steps[0].model!.variables) {
      modelVars = model.steps[0].model!.variables;
    }
    let displayVars = available.filter(x => modelVars.indexOf('' + x.name) > -1);
    let display: any[] = [];
    displayVars.map((x, i) => display.push(<div key={i}><h3>{x.name}:</h3><pre>{x.description}</pre></div>));
    return (<div>{display}</div>);
  }
}

export class Review extends React.Component<ReviewProps, {}> {
  render() {
    let model = this.props.model;
    let { name, description, steps, input } = model;
    if (model && model.name) { name = model.name; }
    if (model && model.steps) { steps = model.steps; }

    // Only looking at run level transfomraitons right now.
    let xforms: Transformation[] = [];
    if (steps && steps[0] && steps[0].transformations) {
      xforms = steps[0].transformations!;
    }

    // Only looking at run level transfomraitons right now.
    let contrasts: Contrast[] = [];
    if (steps && steps[0] && steps[0].contrasts) {
      contrasts = steps[0].contrasts!;
    }

    let autoContrasts: boolean = false;
    if (steps && steps[0] && steps[0].auto_contrasts) {
      autoContrasts = steps[0].auto_contrasts!;
    }

    return (
      <Card
        title={'Overview of ' + (name ? name : 'No Name')}
      >
        <p>{description ? description : 'No description.'}</p>
        <Collapse>
        <Panel header="Inputs" key="inputs"><ModelInput model={model}/></Panel>
        <Panel header="Variables" key="variables">
          <Variables model={this.props.model} available={this.props.availablePredictors}/>
        </Panel>
        <Panel header="Transformations" key="xforms"><ReviewObjects input={xforms}/></Panel>
        <Panel header="Contrasts" key="contrasts">
          <ReviewObjects input={contrasts} autoContrasts={autoContrasts}/>
        </Panel>
        <Panel header="JSON Model" key="model"><pre>{JSON.stringify(this.props.model, null, 2)}</pre></Panel>
        </Collapse>
      </Card>
    );
  }
}
