/*
This module comtains the following components:
 - XformsTab: parent component implementing the transformation tab of the analysis builder.
 - XformDisplay: component to display a single transformation
 - XformEditor: component to add/edit a transformtion
*/
import * as React from 'react';
import {
  Button,
  Checkbox,
  Col,
  Form,
  Icon,
  Input,
  InputNumber,
  List,
  Radio,
  Row,
  Select
} from 'antd';
import {
  DragDropContext,
  Draggable,
  Droppable,
  DroppableProvided,
  DropResult,
  DroppableStateSnapshot, DraggableProvided, DraggableStateSnapshot
} from 'react-beautiful-dnd';

import {
  Predictor,
  Transformation,
  TransformName,
  XformRules,
} from '../coretypes';
import { moveItem, reorder } from '../utils';
import { DisplayErrorsInline, Space } from '../HelperComponents';
import { PredictorSelector } from './Predictors';
import transformDefinitions from './transforms';
const Option = Select.Option;

let xformRules: XformRules = {};
for (const item of transformDefinitions) {
  xformRules[item.Name] = item;
}

const FormItem = Form.Item;
const RadioGroup = Radio.Group;

export function validateXform(xform: Transformation) {
  let errors: string[] = [];
  if (!xform.Name) {
    errors.push('Please select a transformation');
  }
  if (xform.Input === undefined || xform.Input.length < 1) {
    errors.push('Please select at least one input for the transformation');
  }
  if ((xform.Name === 'Orthogonalize') && xform.Input !== undefined) {
    if (xform.Other === undefined || xform.Other.length < 1) {
      errors.push('Must orthoganalize with respect to at least one predictor');
    }
  }

  return errors;
}

interface XformDisplayProps {
  index: number;
  xform: Transformation;
  onDelete: (index: number) => void;
  onEdit: (index: number) => void;
}

const XformDisplay = (props: XformDisplayProps) => {
  const { xform, index, onDelete, onEdit } = props;
  const input = xform.Input || [];
  return (
    <div>
      <div  style={{'float': 'right'}}>
        <Button type="primary" onClick={() => onEdit(index)}>
          <Icon type="edit" />
        </Button>
        <Button type="danger" onClick={() => onDelete(index)}>
          <Icon type="delete" />
        </Button>
      </div>
      <div>
        <b>{`${xform.Name}`} </b><br/>
        {`Inputs: ${input!.join(', ')}`}
      </div>
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
          onChange={(newValue) => {
            if (newValue && !Number.isInteger(newValue as number)) { return; }
            newValue ? onChange(newValue) : onChange(0);
          }}
        />
        <br />
      </div>
    );
  };

  ReplaceField = () => {
    const { name, value, onChange } = this.props;
    let keys = Object.keys(value);
    let predecessor;
    let replacement;
    if (keys.length > 0) {
      predecessor = keys[0];
    }
    if (predecessor !== []) {
      replacement = value[predecessor];
    }
    return (
      <div>
        Old Value:
        <Input
          defaultValue={predecessor}
          onChange={(event) => {
            let x = {};
            x[event.target.value] = replacement;
            onChange(x);
          }}
        />
        New Value:
        <Input
          defaultValue={replacement}
          onChange={(event) => {
            let x = {};
            x[predecessor] = event.target.value;
            onChange(x);
          }}
        />
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
          compact={true}
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
        {name === 'Other' && this.WrtField()}
        {name === 'Replace' && this.ReplaceField()}
        {name === 'Weights' && options && options.map((x, i) =>
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
              defaultValue={this.props.value[i] ? this.props.value[i] : undefined}
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
  xformErrors: string[];
  index: number;
  updateBuilderState: (value: any) => any;
}

interface XformEditorState {
  input:  Predictor[];
  name: TransformName | '';
}

class XformEditor extends React.Component<XformEditorProps, XformEditorState> {
  updateParameter = (name: string, value: any) => {
    let updatedXform = {...this.props.xform};
    updatedXform[name] = value;
    this.props.updateBuilderState('activeXform')(updatedXform);
  };

  constructor(props: XformEditorProps) {
    super(props);
    const {xform,  availableInputs, index} = props;
    let input: Predictor[] = [];
    if (index >= 0 && xform.Input !== undefined && availableInputs !== undefined) {
      input = availableInputs.filter(x => xform.Input!.indexOf(x.name) >= 0);
    }
    this.state = {
      input: input,
      name: xform ? xform.Name : '',
    };
  }

  updateInputs = (input: Predictor[]) => {
    // In the special case of the orthogonalize transformation if new inputs are selected
    // we need to make sure we remove them from the 'wrt' parameter if they've already been added there
    let newXform = {...this.props.xform};
    const inputIds = new Set(input.map(x => x.name));
    if (newXform.Name === 'Orthogonalize') {
        if (newXform.Other) {
          newXform.Other = newXform.Other.filter(x => !inputIds.has(x));
        }
    }
    newXform.Input = Array.from(inputIds);
    this.props.updateBuilderState('activeXform')(newXform);
    this.setState({input});
  };

  updateXformType = (name: (TransformName | '')) => {
    // tslint:disable-next-line:no-shadowed-variable
    const {xformRules} = this.props;
    const xform = JSON.parse(JSON.stringify(xformRules[name]));
    this.props.updateBuilderState('activeXform')(xform);
    this.setState({name});
  };

  onSave = () => {
    const {xform} = this.props;
    const {name,  input} = this.state;
    let errors = validateXform(xform);
    if (errors.length > 0) {
      this.props.updateBuilderState('xformErrors')(errors);
      return;
    }
    xform.Output = xform.Input;
    this.props.onSave(xform);
  };

  render() {
    // tslint:disable-next-line:no-shadowed-variable
    const { xform, xformRules, availableInputs } = this.props;
    const { name, input } = this.state;
    const allowedXformNames = Object.keys(xformRules);
    const availableParameters = name ? Object.keys(xformRules[name]) : undefined;
    return (
      <div>
        <Form layout="horizontal">
          <Row type="flex">
            <Col lg={{span: 24}} xs={{span: 24}}>
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
                compact={true}
              />
              <br />
              {availableParameters &&
                availableParameters.map(param => {
                  let options: Predictor[] = input;
                  if (xform.Name === 'Orthogonalize') {
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
                          value={xform[param]}
                          kind={typeof(xform[param])}
                          options={options}
                          onChange={value => this.updateParameter(param, value)}
                        />}
                    </div>
                  );
                })}
              <br />
            </div>}
          <DisplayErrorsInline errors={this.props.xformErrors} />
          <Space />
          <Button
            type="primary"
            onClick={this.onSave}
            disabled={!this.props.xform.Name}
          >
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
  activeXformIndex: number;
  activeXform?: Transformation;
  xformErrors: string[];
  updateBuilderState: (value: any) => any;
}

interface XformsTabState {
  mode:  'add' | 'edit' | 'view';
}

export class XformsTab extends React.Component<XformsTabProps,  XformsTabState> {
  constructor(props:  XformsTabProps) {
    super(props);
    this.state = {mode:  'view'};
  }

  onAddXform = () => {
    if (this.props.activeXformIndex !== -1) {
      this.props.updateBuilderState('activeXform')({...xformRules[0]});
      this.props.updateBuilderState('activeXformIndex')(-1);
    }
    this.setState({ mode: 'add'});
  }

  onCancel = () => {
    this.props.updateBuilderState('activeXform')(undefined);
    this.props.updateBuilderState('activeXformIndex')(-1);
    this.props.updateBuilderState('xformErrors')([] as string[]);
    this.setState({ mode: 'view' });
  }

  onSaveXform = (xform: Transformation) => {
    if (this.props.activeXformIndex >= 0 && this.props.activeXform !== undefined) {
      let newXforms = this.props.xforms;
      newXforms[this.props.activeXformIndex] = this.props.activeXform;
      this.props.onSave(newXforms);
      this.setState({mode:  'view' });
    } else {
      let newXforms = [...this.props.xforms, ...[xform]];
      this.props.onSave(newXforms);
      this.setState({mode:  'view' });
    }
  };

  onDeleteXform = (index: number) => {
    this.props.xforms.splice(index, 1);
    const newXforms = this.props.xforms;
    this.props.onSave(newXforms);
  };

  onEditXform = (index: number) => {
    this.props.updateBuilderState('activeXformIndex')(index);
    this.props.updateBuilderState('activeXform')({...this.props.xforms[index]});
    this.props.updateBuilderState('xformErrors')([] as string[]);
    this.setState({mode: 'add'});
  };

  onMoveXform = (index: number, direction: 'up' | 'down') => {
    const newXforms = moveItem(this.props.xforms, index, direction);
    this.props.onSave(newXforms);
  };

  onDragEnd = (result: DropResult): void  => {

    const { source, destination } = result;

    if (!destination) {
      return;
    }

    const newXforms = reorder(
      this.props.xforms,
      source.index,
      destination.index
    );
    if (this.props.activeXformIndex === source.index) {
      this.props.updateBuilderState('ActiveXformIndex')(destination.index);
    }

    this.props.onSave(newXforms);
  };

  getStyle = (index: number): string => {
    if (index === this.props.activeXformIndex) {
      return 'selectedXform';
    }
    return 'unselectedXform';
  }

  render() {
    const { predictors, activeXformIndex, activeXform } = this.props;
    const {mode} = this.state;
    const AddMode = () => (
      <div style={{'marginTop': '-14px'}}>
        {activeXformIndex === -1 && (
          <h2>
            Add a new transformation:
          </h2>
        )}
        <XformEditor
          xformRules={xformRules}
          onSave={xform => this.onSaveXform(xform)}
          onCancel={this.onCancel}
          availableInputs={predictors}
          xform={activeXform ? activeXform : {...xformRules[0]}}
          xformErrors={this.props.xformErrors}
          updateBuilderState={this.props.updateBuilderState}
          index={activeXformIndex}
          key={activeXformIndex}
        />
      </div>
    );

    const ViewMode = () => (
      <div>
        <DragDropContext onDragEnd={this.onDragEnd}>
          <Droppable droppableId="droppable">
            {(provided: DroppableProvided, snapshot: DroppableStateSnapshot) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                <List
                  size="small"
                  bordered={true}
                  dataSource={this.props.xforms}
                  locale={{ emptyText: 'You haven\'t added any transformations' }}
                  renderItem={(item, index) => (
                    <List.Item className={this.getStyle(index)}>
                      <Draggable key={index} draggableId={'' + index} index={index}>
                        {(providedDraggable: DraggableProvided, snapshotDraggable: DraggableStateSnapshot) => (
                            <div
                              style={{'width': '100%'}}
                              ref={providedDraggable.innerRef}
                              {...providedDraggable.dragHandleProps}
                            >
                              <div {...providedDraggable.draggableProps}>
                                  <XformDisplay
                                    key={index}
                                    index={index}
                                    xform={item}
                                    onDelete={this.onDeleteXform}
                                    onEdit={this.onEditXform}
                                  />
                                  {providedDraggable.placeholder}
                              </div>
                            </div>
                        )}
                      </Draggable>
                    </List.Item>
                  )}
                />
              </div>
            )}
          </Droppable>
        </DragDropContext>
        <br />
        <Button type="default" onClick={this.onAddXform}>
          <Icon type="plus" /> Add Transformation
        </Button>
      </div>
    );

    return (
      <div>
        <br />
        <Row>
          <Col md={9}>
            {ViewMode()}
          </Col>
          <Col md={1}/>
          <Col md={14}>
            {mode === 'add' && AddMode()}
          </Col>
        </Row>
      </div>
    );
  }
}
