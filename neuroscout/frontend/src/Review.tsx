
import * as React from 'react';
import { message, Button, Collapse, Card, Icon, Table } from 'antd';

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
  dataset?: Dataset;
}

class DatasetInfo extends React.Component<{dataset: Dataset}, {}> {
  render() {
    let dataset = this.props.dataset;
    return (
      <>
        <p>{dataset.description}</p>
        <p>Authors:<br/> {dataset.authors}</p>
        <a href={dataset.url} target="_blank" rel="noopener">{dataset.url}</a>
      </>
    );
  }
}

class ModelInput extends React.Component<{model: BidsModel}, {}> {
  render() {
    if (this.props.model.Input === undefined) {
      return;
    }
    let input = this.props.model.Input;
    let runs = input.Run ? input.Run.sort().map(x => <li key={x}>{x}</li>) : [];
    let subjects = input.Subject ? alphaSort(input.Subject).join(', ') : [];
    let sessions = input.Session ? alphaSort(input.Session).join(', ') : [];

    return (
      <div>
        <Card title="Task" key="task">{input.Task ? input.Task : ''}</Card>
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
    input.map((x, i) => display.push(<div key={i}><h3>{x.Name}:</h3><pre>{JSON.stringify(x, null, 2)}</pre></div>));

    return (
      <div>{display}</div>
    );
  }
}

class ModelStep extends React.Component<{step: Step}, {}> {
  render() {
    let step = this.props.step;
    let xforms: any = '';
    if (step.Transformations !== undefined) {
        xforms = (
          <ReviewObjects input={step.Transformations}/>
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

// <Panel header="Steps" key="Steps"><ModelSteps Steps={Steps as Step[]}/></Panel>
// Only displaying run level step right now so this is unused.
class ModelSteps extends React.Component<{Steps: Step[]}, {}> {
  render() {
      if (this.props.Steps === undefined) {
        return;
      }
      let Steps = this.props.Steps;
      let display: any[] = [];
      Steps.map((x, i) => display.push(
        <Panel header={`${x.Level} Level`} key={i.toString()}><ModelStep step={x}/></Panel>)
      );
      return (
        <Collapse bordered={false}>
          {display}
        </Collapse>
      );
  }
}

// In the future this will include the new named outputs from transformations.
class X extends React.Component<{model: BidsModel, available: Predictor[]}, {}> {
  render() {
    let { model, available } = this.props;
    let modelVars: string[] = [];
    if (model.Steps && model.Steps[0] && model.Steps[0].Model && model.Steps[0].Model!.X) {
      modelVars = model.Steps[0].Model!.X;
    }
    let displayVars = available.filter(x => modelVars.indexOf('' + x.name) > -1);
    let display: any[] = [];
    displayVars.map((x, i) => display.push(<div key={i}><h3>{x.name}:</h3><pre>{x.description}</pre></div>));
    displayVars.map((x, i) => { return {name: x.name, description: x.description}; });
    let columns = [{
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
    }, {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
    }];
    return (<Table dataSource={displayVars} columns={columns} />);
  }
}

export class Review extends React.Component<ReviewProps, {}> {
  render() {
    let model = this.props.model;
    let dataset = this.props.dataset;
    let { Name, Description, Steps, Input } = model;
    if (model && model.Name) { Name = model.Name; }
    if (model && model.Steps) { Steps = model.Steps; }

    // Only looking at run level transfomraitons right now.
    let xforms: Transformation[] = [];
    if (Steps && Steps[0] && Steps[0].Transformations) {
      xforms = Steps[0].Transformations!;
    }

    // Only looking at run level transfomraitons right now.
    let contrasts: Contrast[] = [];
    if (Steps && Steps[0] && Steps[0].Contrasts) {
      contrasts = Steps[0].Contrasts!;
    }

    let autoContrasts: boolean = false;
    if (Steps && Steps[0] && Steps[0].AutoContrasts) {
      autoContrasts = Steps[0].AutoContrasts!;
    }

    return (
      <Card
        title={'Overview of ' + (Name ? Name : 'No Name')}
      >
        <p>{Description ? Description : 'No description.'}</p>
        <Collapse bordered={false}>
        {dataset && <Panel header={`Dataset - ${dataset.name}`} key="dataset"><DatasetInfo dataset={dataset}/></Panel>}
        <Panel header="Inputs" key="inputs"><ModelInput model={model}/></Panel>
        <Panel header="X (Variables)" key="X">
          <X model={this.props.model} available={this.props.availablePredictors}/>
        </Panel>
        <Panel header="Transformations" key="xforms"><ReviewObjects input={xforms}/></Panel>
        <Panel header="Contrasts" key="contrasts">
          <ReviewObjects input={contrasts} autoContrasts={autoContrasts}/>
        </Panel>
        <Panel header="BIDS StatsModel" key="model"><pre>{JSON.stringify(this.props.model, null, 2)}</pre></Panel>
        </Collapse>
      </Card>
    );
  }
}
