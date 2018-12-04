/*
This module comtains the following components:
 - XformsTab: parent component implementing the transformation tab of the analysis builder.
 - XformDisplay: component to display a single transformation
 - XformEditor: component to add/edit a transformtion
*/
import * as React from 'react';
import { Table, Input, InputNumber, Button, Row, Col, Form, Select, Checkbox, Icon, Radio } from 'antd';
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
  xformRules[item.Name] = item;
}

const FormItem = Form.Item;
const RadioGroup = Radio.Group;

interface XformDisplayProps {
  index: number;
  xform: Transformation;
  onDelete: (index: number) => void;
  onEdit: (index: number) => void;
  enableUp: boolean;
  enableDown: boolean;
  onMove: (index: number, direction: 'up' | 'down') => void;
}

function renderParamItems(xform: Transformation) {
    let reserved = ['input', 'name', 'output'];
    let paramItems: any = [];
    Object.keys(xform).map(key => {
      if (key === 'weights' && xform && xform.Input) {
        let weightItems: any = [];
        xform.Input.map((elem, index) => {
          if (xform && xform.Weights && xform.Weights[index]) {
            weightItems.push(<li key={index}>{elem + ': ' + xform.Weights[index]}<br/></li>);
          }
        });
        paramItems.push(
          <li key={key}>{key + ':'}<br/><ul>{weightItems}</ul></li>
        );
      } else if (reserved.includes(key)) {
        return;
      } else {
        paramItems.push(
          <li key={key}>{key + ': ' + xform[key]}</li>
        );
      }
    });
    return paramItems;
}

const XformDisplay = (props: XformDisplayProps) => {
  const { xform, index, onDelete, onMove, enableUp, enableDown, onEdit } = props;
  const input = xform.Input || [];
  let paramItems = renderParamItems(xform);
  return (
    <div>
      <h3>{`${index + 1}: ${xform.Name}`}</h3>
      <p>{`Inputs: ${input!.join(', ')}`}</p>
      {(paramItems.length > 0) &&
        <div>
        <p>Parameters:</p>
        <ul>
          {paramItems}
        </ul>
        </div>
      }
      {enableUp &&
        <Button onClick={() => onMove(index, 'up')}>
          <Icon type="arrow-up" />
        </Button>}
      {enableDown &&
        <Button onClick={() => onMove(index, 'down')}>
          <Icon type="arrow-down" />
        </Button>}
      <Button type="danger" onClick={() => onDelete(index)}>
        <Icon type="delete" /> Remove
      </Button>
      <Button onClick={() => onEdit(index)}>
        <Icon type="edit" /> edit
      </Button>
      <br />
      <br />
    </div>
  );
};

interface ParameterFieldProps {
  name:  string;
  kind: string;
  options?: Object[];
  value?: any;
  onChange: (value: any) => void;
}

class ParameterField extends React.Component<ParameterFieldProps> {
  updateWeight = (index: number, value: number) => {
    let weights = [...this.props.value ];
    weights[index] = value;
    return weights;
  };

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

  NumberField = () => {
    const { name, value, onChange } = this.props;
    return (
      <div>
        {name}:
        <InputNumber
          defaultValue={value}
          onChange={(newValue) => newValue ? onChange(newValue) : onChange(0)}
        />
        <br />
      </div>
    );
  };

  WrtField = () => {
    const {name,  onChange, value, options } = this.props;
    // const selectedPredictors = (options as Predictor[] || []).filter(p => value.indexOf(p.id) > -1);
    const wrtSet = new Set(value as string[]);
    const selectedPredictors = ((options as Predictor[]) || []).filter(p => wrtSet.has(p.name));
    return (
      <div>
        <p>
          {'Select predictors you\'d like to orthogonalize with respect to:'}
        </p>
        <PredictorSelector
          availablePredictors={options as Predictor[]}
          selectedPredictors={selectedPredictors}
          updateSelection={predictors => onChange(predictors.map(x => x.name))}
        />
        <br />
      </div>
    );
  };

  ReplaceNAField = () => {
    const { name, value, onChange } = this.props;
    return (
      <div>
      Replace missing values with 0 before/after scaling:<br/>
      <RadioGroup
          onChange={(event) => onChange(event.target.value)}
          value={value}
      >
        <Radio.Button value={'before'}>Before</Radio.Button>
        <Radio.Button value={'after'}>After</Radio.Button>
        <Radio.Button value={undefined}>Don't Replace</Radio.Button>
      </RadioGroup>
      </div>
    );
  };

  render() {
    const {kind, name, onChange } = this.props;
    const options = this.props.options as Predictor[];
    return (
      <span>
        {kind === 'number' && this.NumberField()}
        {kind === 'boolean' && this.BooleanField()}
        {name === 'other' && this.WrtField()}
        {name === 'weights' && options && options.map((x, i) =>
          <Row key={i}>
          <div>
            <Col span={12}>
              <div className="weightName">
                {x.name} weight:
              </div>
            </Col>
            <Col span={4}>
            <InputNumber
              onChange={(newValue) => {
                let newWeights = this.updateWeight(i, newValue as number);
                onChange(newWeights);
              }}
            />
            </Col>
          </div>
          </Row>
        )}
        {name === 'replace_na' && this.ReplaceNAField()}
      </span>
    );
  }
}

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
    let input: Predictor[] = [];
    if (xform !== undefined && xform.Input && xform.Input.length > 0) {
      input = availableInputs.filter(x => xform.Input!.indexOf(x.name) >= 0);
    }
    
    this.state = {
      transformation: xform,
      input: input,
      name: xform ? xform.Name : '',
    };
  }

  updateInputs = (input: Predictor[]) => {
    // In the special case of the orthogonalize transformation if new inputs are selected
    // we need to make sure we remove them from the 'wrt' parameter if they've already been added there
    const {transformation} = this.state;
    const inputIds = new Set(input.map(x => x.name));
    let newXform = transformation;
    if (transformation.Name === 'Orthogonalize') {
        if (transformation.Other) {
          newXform.Other = transformation.Other.filter(x => !inputIds.has(x));
        }
    }
    newXform.Input = Array.from(inputIds);
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
    if (input.length < 1) {
      displayError(new Error('Please select at least one input for the transformation'));
      return;
    }
    transformation.Output = transformation.Input;
    this.props.onSave(transformation);
  };

  render() {
    // tslint:disable-next-line:no-shadowed-variable
    const {xform,  xformRules, availableInputs } = this.props;
    const { name,  transformation, input } = this.state;
    const editMode = !!xform;
    const allowedXformNames = Object.keys(xformRules);
    const availableParameters = name ? Object.keys(xformRules[name]) : undefined;
    return (
      <div>
        <Form layout="horizontal">
          <Row type="flex">
            <Col lg={{span: 16}} xs={{span: 24}}>
              <FormItem label="Transformation:">
                <Select value={name} onChange={this.updateXformType}>
                  {allowedXformNames.map(x =>
                    <Option value={x} key={x}>
                      {x}
                    </Option>
                  )}
                </Select>
              </FormItem>
            </Col>
          </Row>
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
                  let options: Predictor[] = input;
                  if (transformation.Name === 'Orthogonalize') {
                    // Special case for wrt parameter: in 'options' exclude predictors
                    // that were selected for 'inputs'
                    const inputIds = new Set(input.map(x => x.name));
                    options = availableInputs.filter(x => !inputIds.has(x.name));
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
          <Button
            type="primary"
            onClick={this.onSave}
            disabled={!this.state.name || (this.state.input.length < 1)}
          >
            {'Save Transformaiton Changes'}
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
  currentEdit: null | number;
}

export class XformsTab extends React.Component<XformsTabProps,  XformsTabState> {
  constructor(props:  XformsTabProps) {
    super(props);
    this.state = {mode:  'view', currentEdit: null };
  }

  onEditXform = (index: number) => {
    this.setState({mode: 'add', currentEdit: index});
  };

  onEditXformSave = (xform: Transformation) => {
    let newXforms = [...this.props.xforms];
    if (this.state.currentEdit === null) {
      newXforms.push(xform);
    } else {
      newXforms[this.state.currentEdit] = xform;
    }
    this.props.onSave(newXforms);
    this.setState({mode: 'view', currentEdit: null});
  };

  onDeleteXform = (index: number) => {
    this.props.xforms.splice(index, 1);
    const newXforms = this.props.xforms;
    this.props.onSave(newXforms);
  };

  onMoveXform = (index: number, direction: 'up' | 'down') => {
    const newXforms = moveItem(this.props.xforms, index, direction);
    this.props.onSave(newXforms);
  };

  render() {
    const {xforms,  predictors } = this.props;
    const {mode, currentEdit } = this.state;
    const AddMode = () => (
      <div>
        <h2>
          {(currentEdit !== null) && 'Edit transformation:'}
          {currentEdit === null && 'Add a new transformation:'}
        </h2>
        <XformEditor
          xformRules={xformRules}
          onSave={xform => this.onEditXformSave(xform)}
          onCancel={() => this.setState({ mode: 'view', currentEdit: null })}
          availableInputs={predictors}
          xform={
            (currentEdit === null) ? xformRules[0] : xforms[currentEdit]
          }
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
                onEdit={this.onEditXform}
                onMove={this.onMoveXform}
                enableUp={index > 0}
                enableDown={index < xforms.length - 1}
              />
            )
          : <p>
              {'You haven\'t created any transformations'}
            </p>}
        <br />
        <Button type="default" onClick={() => this.setState({ mode: 'add' })}>
          <Icon type="plus" /> Add Transformation
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
