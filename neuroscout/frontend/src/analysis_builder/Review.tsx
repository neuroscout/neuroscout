import * as React from 'react'
import { Collapse, Card, Table, Tag, Space } from 'antd'
import { Link } from 'react-router-dom'

import {
  Dataset,
  Predictor,
  Transformation,
  Contrast,
  BidsModel,
} from '../coretypes'
import { alphaSort } from '../utils'
import NeurovaultLinks from './NeuroVault'

const Panel = Collapse.Panel

interface ReviewProps {
  model: BidsModel
  analysisId?: string
  unsavedChanges: boolean
  availablePredictors: Predictor[]
  dataset?: Dataset
  user_name?: string
}

class DatasetInfo extends React.Component<
  { dataset: Dataset },
  Record<string, never>
> {
  render() {
    const dataset = this.props.dataset
    return (
      <>
        <p>{dataset.summary}</p>
        <p>
          Authors:
          <br /> {dataset.authors.join(', ')}
        </p>
        <a href={dataset.url} target="_blank" rel="noopener noreferrer">
          {dataset.url}
        </a>
      </>
    )
  }
}

class ModelInput extends React.Component<
  { model: BidsModel },
  Record<string, never>
> {
  render() {
    if (this.props.model.Input === undefined) {
      return
    }
    const input = this.props.model.Input
    const runs = input.Run
      ? input.Run.sort().map(x => <li key={x}>{x}</li>)
      : []
    const subjects = input.Subject ? alphaSort(input.Subject).join(', ') : []
    const sessions = input.Session ? alphaSort(input.Session).join(', ') : []

    return (
      <div>
        <Card title="Task" key="task">
          {input.Task ? input.Task : ''}
        </Card>
        {runs.length > 0 && (
          <Card title="Runs" key="runs">
            <ul>{runs}</ul>
          </Card>
        )}
        {subjects.length > 0 && (
          <Card title="Subjects" key="subjects">
            <p>{subjects}</p>
          </Card>
        )}
        {sessions.length > 0 && (
          <Card title="Sessions" key="sessions">
            <p>{sessions}</p>
          </Card>
        )}
      </div>
    )
  }
}

/* Object needs to have name as a key  */
class ReviewObjects extends React.Component<{
  input: (Transformation | Contrast)[]
}> {
  render() {
    const input = this.props.input
    const display: JSX.Element[] = []
    input.map((x, i) =>
      display.push(
        <div key={i}>
          <h3>{x.Name}:</h3>
          <pre>{JSON.stringify(x, null, 2)}</pre>
        </div>,
      ),
    )

    return <div>{display}</div>
  }
}

// <Panel header="Steps" key="Steps"><ModelSteps Steps={Steps as Step[]}/></Panel>
/* Only displaying run level step right now so this is unused.
class ModelStep extends React.Component<{step: Step}, Record<string, never>> {
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

class ModelSteps extends React.Component<{Steps: Step[]}, Record<string, never>> {
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
*/

function getPredictorNames(
  model: BidsModel,
  availablePredictors: Predictor[],
): Predictor[] {
  let modelVars: string[] = []
  if (
    model.Steps &&
    model.Steps[0] &&
    model.Steps[0].Model &&
    model.Steps[0].Model.X
  ) {
    modelVars = model.Steps[0].Model.X
  }
  console.log(modelVars)
  return availablePredictors.filter(x => modelVars.indexOf('' + x.name) > -1)
}
// In the future this will include the new named outputs from transformations.
class X extends React.Component<{ model: BidsModel; available: Predictor[] }> {
  render() {
    const { model, available } = this.props
    const displayVars = getPredictorNames(model, available)
    const display: JSX.Element[] = []
    displayVars.map((x, i) =>
      display.push(
        <div key={i}>
          <h3>{x.name}:</h3>
          <pre>{x.description}</pre>
        </div>,
      ),
    )
    displayVars.map(x => {
      return { name: x.name, description: x.description }
    })
    const columns = [
      {
        title: 'Name',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: 'Description',
        dataIndex: 'description',
        key: 'description',
      },
    ]
    return <Table dataSource={displayVars} columns={columns} />
  }
}

export class Review extends React.Component<
  ReviewProps,
  Record<string, never>
> {
  render(): JSX.Element {
    const model = this.props.model
    const dataset = this.props.dataset
    const predictors = getPredictorNames(model, this.props.availablePredictors)
    const numberOfSubjects = model.Input?.Subject
      ? model.Input.Subject.length
      : 0
    let { Name, Steps } = model
    const { Description } = model

    if (model && model.Name) {
      Name = model.Name
    }
    if (model && model.Steps) {
      Steps = model.Steps
    }

    // Only looking at run level transfomraitons right now.
    let xforms: Transformation[] = []
    if (Steps && Steps[0] && Steps[0].Transformations) {
      xforms = Steps[0].Transformations
    }

    // Only looking at run level transfomraitons right now.
    let contrasts: Contrast[] = []
    if (Steps && Steps[0] && Steps[0].Contrasts) {
      contrasts = Steps[0].Contrasts
    }

    return (
      <Card>
        Author:{' '}
        <Link to={`/profile/${String(this.props.user_name)}`}>
          {' '}
          {this.props.user_name}{' '}
        </Link>
        <p>{Description ? Description : 'No description.'}</p>
        <p>Number of subjects: {numberOfSubjects}</p>
        <p>
          Predictors used: <Space />
          {predictors.map(x => (
            <Tag color="green" key={x.name}>
              {x.name}
            </Tag>
          ))}
        </p>
        Neurovault Links:
        <br />
        <NeurovaultLinks analysisId={this.props.analysisId} />
        <Collapse bordered={false}>
          {dataset && (
            <Panel header={`Dataset - ${dataset.name}`} key="dataset">
              <DatasetInfo dataset={dataset} />
            </Panel>
          )}
          <Panel header="Inputs" key="inputs">
            <ModelInput model={model} />
          </Panel>
          <Panel header="X (Variables)" key="X">
            <X
              model={this.props.model}
              available={this.props.availablePredictors}
            />
          </Panel>
          <Panel header="Transformations" key="xforms">
            <ReviewObjects input={xforms} />
          </Panel>
          <Panel header="Contrasts" key="contrasts">
            <ReviewObjects input={contrasts} />
          </Panel>
          <Panel header="BIDS StatsModel" key="model">
            <pre>{JSON.stringify(this.props.model, null, 2)}</pre>
          </Panel>
        </Collapse>
      </Card>
    )
  }
}
