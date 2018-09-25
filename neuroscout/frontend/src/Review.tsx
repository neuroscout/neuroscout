
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
  Block,
  BlockModel,
  BidsModel,
  ImageInput,
  TransformName
} from './coretypes';

import { displayError, jwtFetch, alphaSort } from './utils';

const Panel = Collapse.Panel;

interface ReviewProps {
  model: BidsModel;
  unsavedChanges: boolean;
  generateButton: any;
}

class ModelInput extends React.Component<{model: BidsModel}, {}> {
  render() {
    if (this.props.model.input === undefined) {
      return;
    }
    let input = this.props.model.input;
    let runs = input.run ? input.run.sort().map(x => <li key={x}>{x}</li>) : [];
    let subjects = input.subject ? alphaSort(input.subject).map(x => <li key={x}>{x}</li>) : [];
    let sessions = input.subject ? alphaSort(input.subject).map(x => <li key={x}>{x}</li>) : [];

    return (
      <Collapse>
        <Panel header="Task" key="task">{input.task ? input.task : ''}</Panel>
        <Panel header="Runs" key="runs"><ul>{runs}</ul></Panel>
        <Panel header="Subjects" key="subjects"><ul>{subjects}</ul></Panel>
        <Panel header="Sessions" key="sessions"><ul>{sessions}</ul></Panel>
      </Collapse>
    );
  }
}

/* Object needs to have name as a key  */
class ReviewObjects extends React.Component<{input: (Transformation | Contrast)[], autoContrasts?: boolean}, {}> {
  render() {
    let input = this.props.input;
    let display: any[] = [];
    if (this.props.autoContrasts !== undefined) {
      display.push(<div key="ac"><h3>Auto Contrasts:</h3>{this.props.autoContrasts}</div>);
    }
    input.map((x, i) => display.push(<div key={i}><h3>{x.name}:</h3><pre>{JSON.stringify(x, null, 2)}</pre></div>));

    return (
      <div>{display}</div>
    );
  }
}

class ModelBlock extends React.Component<{block: Block}, {}> {
  render() {
    let block = this.props.block;    
    let xforms: any = '';
    if (block.transformations !== undefined) {
        xforms = (
          <ReviewObjects input={block.transformations}/>
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

// <Panel header="Blocks" key="blocks"><ModelBlocks blocks={blocks as Block[]}/></Panel>
// Only displaying run level block right now so this is unused.
class ModelBlocks extends React.Component<{blocks: Block[]}, {}> {
  render() {
      if (this.props.blocks === undefined) {
        return;
      }
      let blocks = this.props.blocks;
      let display: any[] = [];
      blocks.map((x, i) => display.push(
        <Panel header={`${x.level} Level`} key={i.toString()}><ModelBlock block={x}/></Panel>)
      );
      return (
        <Collapse>
          {display}
        </Collapse>
      );
  }
}

export class Review extends React.Component<ReviewProps, {}> {
  render() {
    let model = this.props.model;
    let { name, description, blocks, input } = model;
    if (model && model.name) { name = model.name; }
    if (model && model.blocks) { blocks = model.blocks; }

    // Only looking at run level transfomraitons right now.
    let xforms: Transformation[] = [];
    if (blocks && blocks[0] && blocks[0].transformations) {
      xforms = blocks[0].transformations!;
    }

    // Only looking at run level transfomraitons right now.
    let contrasts: Contrast[] = [];
    if (blocks && blocks[0] && blocks[0].contrasts) {
      contrasts = blocks[0].contrasts!;
    }

    let autoContrasts: boolean = false;
    if (blocks && blocks[0] && blocks[0].auto_contrasts) {
      autoContrasts = blocks[0].auto_contrasts!;
    }

    return (
      <Card
        title={name ? name : 'No Name'}
        extra={this.props.generateButton}
      >
        <p>{description ? description : 'No description.'}</p>
        <Collapse>
        <Panel header="Inputs" key="inputs"><ModelInput model={model}/></Panel>
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
