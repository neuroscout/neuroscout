/*
This module comtains the following components:
 - XformsTab: parent component implementing the transformation tab of the analysis builder.
 - XformDisplay: component to display a single transformation
 - XformEditor: component to add/edit a transformtion
*/
import * as React from 'react';
import { Table, Input, Button, Row, Col, Form, Select, Checkbox, Icon } from 'antd';
import {
  Analysis,
  Predictor,
  Parameter,
  Transformation,
  TransformName,
  XformRules,
} from './coretypes';
import { displayError, moveItem } from './utils';
import { Space } from './HelperComponents';
import { PredictorSelector } from './Predictors';
import transformDefinititions from './transforms';
const Option = Select.Option;

let xformRules: XformRules = {};
for (const item of transformDefinititions) {
  xformRules[item.name] = item;
}

const FormItem = Form.Item;

interface XformDisplayProps {
  index: number;
  xform: Transformation;
  onDelete: (name: TransformName) => void;
  enableUp: boolean;
  enableDown: boolean;
  onMove: (index: number, direction: 'up' | 'down') => void;
}

// if (!(key in reserved)) { 

function renderParamItems(xform: Transformation) {
    let reserved = ['input', 'name', 'output']; 
    let paramItems: any = [];
    Object.keys(xform).map(key => {
      if (reserved.includes(key)) {
        return;
      }
      paramItems.push(
        <li key={key}>{key + ': ' + xform[key]}</li>
      );
    });
    return paramItems;
}

const XformDisplay = (props: XformDisplayProps) => {
  const { xform, index, onDelete, onMove, enableUp, enableDown } = props;
  const input = xform.input || [];
  return (
    <div>
      <h3>{`${index + 1}: ${xform.name}`}</h3>
      <p>{`Inputs: ${input!.join(', ')}`}</p>
      <p>Parameters:</p>
      <ul>
        {renderParamItems(xform)}
      </ul>
      {enableUp &&
        <Button onClick={() => onMove(index, 'up')}>
          <Icon type="arrow-up" />
        </Button>}
      {enableDown &&
        <Button onClick={() => onMove(index, 'down')}>
          <Icon type="arrow-down" />
        </Button>}
      <Button type="danger" onClick={() => onDelete(xform.name)}>
        <Icon type="delete" />
      </Button>
      <br />
      <br />
    </div>
  );
};

interface XformEditorProps {
  xformRules:  XformRules;
  onSave: (xform: Transformation) => void;
  onCancel: () => void;
  availableInputs: Predictor[];
  xform: Transformation;
}

interface XformEditorState {
  input:  Predictor[];
  name: TransformName | '';
  transformation: Transformation;
}

interface ParameterFieldProps {
  name:  string;
  kind: string;
  options?: Object[];
  value?: any;
  onChange: (value: any) => void;
}

class ParameterField extends React.Component<ParameterFieldProps> {
  BooleanField = () => {
    const { name, value, onChange } = this.props;
    return (
      <div>
        <Checkbox checked={value} onChange={() => onChange(!value)}>
          {name}
        </Checkbox>
        <br />
      </div>
    );
  }; 

  WrtField = () => {
    const {name,  onChange, value, options } = this.props;
    // const selectedPredictors = (options as Predictor[] || []).filter(p => value.indexOf(p.id) > -1);
    const wrtSet = new Set(value as string[]);
    const selectedPredictors = ((options as Predictor[]) || []).filter(p => wrtSet.has(p.id));
    return (
      <div>
        <p>
          {'Select predictors you\'d like to orthogonalize against:'}
        </p>
        <PredictorSelector
          availablePredictors={options as Predictor[]}
          selectedPredictors={selectedPredictors}
          updateSelection={predictors => onChange(predictors.map(x => x.id))}
        />
        <br />
      </div>
    );
  };

  render() {
    const {kind, name} = this.props;
    return (
      <span>
        {kind === 'boolean' && this.BooleanField()}
        {name === 'wrt' && this.WrtField()}
      </span>
    );
  }
}

class XformEditor extends React.Component<XformEditorProps, XformEditorState> {
  updateParameter = (name: string, value: any) => {
    const { transformation } = this.state;
    let updatedXform = transformation;
    updatedXform[name] = value;
    this.setState({
      transformation: updatedXform
    });
  }; 

  constructor(props: XformEditorProps) {
    super(props); 
    const {xform,  availableInputs } = props;
    this.state = {
      transformation: xform,
      input: [],
      name: xform ? xform.name : '',
    };
  }

  updateInputs = (input: Predictor[]) => {
    // In the special case of the orthogonalize transformation if new inputs are selected
    // we need to make sure we remove them from the 'wrt' parameter if they've already been added there
    const {transformation} = this.state;
    const inputIds = new Set(input.map(x => x.id));
    let newXform = transformation;
    if (transformation.name === 'orthogonalize') {
        if (transformation.wrt) {
          newXform.wrt = transformation.wrt.filter(x => !inputIds.has(x));
        }
    }
    newXform.input = Array.from(inputIds);
    this.setState({input,  transformation: newXform});
  };

  updateXformType = (name: TransformName) => {
    // tslint:disable-next-line:no-shadowed-variable
    const {xformRules} = this.props;
    const transformation = JSON.parse(JSON.stringify(xformRules[name]));
    this.setState({name,  transformation});
  };

  onSave = () => {
    const {xform} = this.props;
    const {name,  input, transformation} = this.state;
    if (!name) {
      displayError(new Error('Please select a transformation')); 
      return;
    }
    this.props.onSave(transformation);
  };

  render() {
    // tslint:disable-next-line:no-shadowed-variable
    const {xform,  xformRules, availableInputs } = this.props;
    const {name,  transformation, input } = this.state;
    const editMode = !!xform;
    const allowedXformNames = Object.keys(xformRules);
    const availableParameters = name ? Object.keys(xformRules[name]) : undefined;
    return (
      <div>
        <Form layout="horizontal">
          <FormItem label="Transformation:">
            <Select style={{ width: 120 }} value={name} onChange={this.updateXformType}>
              {allowedXformNames.map(x =>
                <Option value={x} key={x}>
                  {x}
                </Option>
              )}
            </Select>
          </FormItem>
          {name &&
            <div>
              <p>Select inputs:</p>
              <PredictorSelector
                availablePredictors={availableInputs}
                selectedPredictors={input}
                // tslint:disable-next-line:no-shadowed-variable
                updateSelection={input => this.updateInputs(input)}
              />
              <br />
              {availableParameters &&
                availableParameters.map(param => {
                  let options: Predictor[] = [];
                  if (transformation.name === 'orthogonalize') {
                    // Special case for wrt parameter: in 'options' exclude predictors
                    // that were selected for 'inputs'
                    const inputIds = new Set(input.map(x => x.id));
                    options = availableInputs.filter(x => !inputIds.has(x.id));
                  }
                  return (
                    <div key={param}>
                      {(param !== 'other' || input.length > 0) &&
                        <ParameterField
                          name={param}
                          value={transformation[param]}
                          kind={typeof(transformation[param])}
                          options={options}
                          onChange={value => this.updateParameter(param, value)}
                        />}
                    </div>
                  );
                })}
              <br />
            </div>}
          <Button type="primary" onClick={this.onSave}>
            OK{' '}
          </Button>
          <Space />
          <Button onClick={this.props.onCancel}>Cancel </Button>
        </Form>
      </div>
    );
  }
}

interface XformsTabProps {
  predictors:  Predictor[];
  xforms: Transformation[];
  onSave: (xforms: Transformation[]) => void;
}

interface XformsTabState {
  mode:  'add' | 'edit' | 'view';
}

export class XformsTab extends React.Component<XformsTabProps,  XformsTabState> {
  constructor(props:  XformsTabProps) {
    super(props); 
    this.state = {mode:  'view' };
  }

  onAddXform = (xform: Transformation) => {
    let newXforms = [...this.props.xforms, ...[xform]];
    this.props.onSave(newXforms);
    this.setState({mode:  'view' });
  };

  onDeleteXform = (name: TransformName) => {
    const newXforms = this.props.xforms.filter(x => x.name !== name);
    this.props.onSave(newXforms);
  };

  onMoveXform = (index: number, direction: 'up' | 'down') => {
    const newXforms = moveItem(this.props.xforms, index, direction);
    this.props.onSave(newXforms);
  };

  render() {
    const {xforms,  predictors } = this.props;
    const {mode} = this.state;
    const AddMode = () => (
      <div>
        <h2>
          {'Add a new transformation:'}
        </h2>
        <XformEditor
          xformRules={xformRules}
          onSave={xform => this.onAddXform(xform)}
          onCancel={() => this.setState({ mode: 'view' })}
          availableInputs={predictors}
          xform={xformRules[0]}
        />
      </div>
    );

    const ViewMode = () => (
      <div>
        <h2>
          {'Transformations'}
        </h2>
        <br />
        {xforms.length
          ? xforms.map((xform, index) =>
              <XformDisplay
                key={index}
                index={index}
                xform={xform}
                onDelete={this.onDeleteXform}
                onMove={this.onMoveXform}
                enableUp={index > 0}
                enableDown={index < xforms.length - 1}
              />
            )
          : <p>
              {'You haven\'t created any transformations'}
            </p>}
        <br />
        <Button type="primary" onClick={() => this.setState({ mode: 'add' })}>
          Add new transformation
        </Button>
      </div>
    );

    return (
      <div>
        {mode === 'view' && ViewMode()}
        {mode === 'add' && AddMode()}
      </div>
    );
  }
}
