import * as React from 'react';
import { Table, Input, Button, Row, Col, Form, Select, Checkbox } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import {
  Analysis, Predictor, Parameter,
  Transformation, TransformName, XformRules
} from './coretypes';
import { displayError, Space } from './utils';
import { PredictorSelector } from './Predictors';
import transformDefinititions from './transforms';
const Option = Select.Option;


let xformRules: XformRules = {};
for (const item of transformDefinititions) {
  xformRules[item.name] = item;
}

const FormItem = Form.Item;

const XformDisplay = (props: { xform: Transformation }) => {
  const xform = props.xform;
  return (
    <div>
      <h3>{xform.name}</h3>
      <p>{`Inputs: ${xform.inputs!.join(', ')}`}</p>
      <p>Parameters:</p>
      <ul>
        {xform.parameters.map(param =>
          <li>{param.name + ': ' + param.value}</li>
        )}
      </ul>
      <br />
    </div>
  );
}

interface XformsTabProps {
  predictors: Predictor[];
  xforms: Transformation[];
  onSave: (xforms: Transformation[]) => void;
}

interface XformsTabState {
  mode: 'add' | 'edit' | 'view';
}

export class XformsTab extends React.Component<XformsTabProps, XformsTabState>{
  constructor(props: XformEditorProps) {
    super();
    this.state = { mode: 'view' };
  }

  onAddXform = (xform: Transformation) => {
    const newXforms = [...this.props.xforms, ...[xform]];
    this.props.onSave(newXforms);
    this.setState({ mode: 'view' });
  }

  render() {
    const { xforms, predictors } = this.props;
    const { mode } = this.state;
    const AddMode = () => (
      <div>
        <h2>{'Add a new transformation:'}</h2>
        <XformEditor
          xformRules={xformRules}
          onSave={xform => this.onAddXform(xform)}
          onCancel={() => this.setState({ mode: 'view' })}
          availableInputs={predictors}
        />
      </div>
    )

    const ViewMode = () => (
      <div>
        <h2>{'Transformations'}</h2>
        <br />
        {xforms.length ?
          xforms.map(xform => <XformDisplay xform={xform} />) :
          <p>{"You haven't created any transformations"}</p>
        }
        <br />
        <Button
          type="primary"
          onClick={() => this.setState({ mode: 'add' })}
        >Add new transformation
        </Button>
      </div>
    )

    return (
      <div>
        {mode === 'view' && ViewMode()}
        {mode === 'add' && AddMode()}
      </div>
    );
  }
}

interface XformEditorProps {
  xformRules: XformRules;
  onSave: (xform: Transformation) => void;
  onCancel: () => void;
  availableInputs: Predictor[];
  xform?: Transformation;
}

interface XformEditorState {
  inputs: Predictor[];
  name: TransformName | '';
  parameters: Parameter[];
}

class XformEditor extends React.Component<XformEditorProps, XformEditorState>{
  updateParameter = (name: string, value: any) => {
    const { parameters } = this.state;
    // let newParameters: Parameter[];
    // let index = parameters.map(p => p.name).indexOf(name);
    // if (index < 0) {
    //   const newParam = { name, value } as Parameter;
    //   newParameters = parameters.concat([newParam]);
    // } else {
    //   newParameters = parameters.map(param => param.name === name ? { ...param, value } : param);
    // }
    // this.setState({ parameters: newParameters });
    this.setState({ parameters: parameters.map(param => param.name === name ? { ...param, value } : param) });
  }

  constructor(props: XformEditorProps) {
    super();
    const { xform, availableInputs } = props;
    this.state = {
      inputs: [],
      name: xform ? xform.name : '',
      parameters: xform ? xform.parameters : [],
    };
  }

  updateInputs = (inputs: Predictor[]) => {
    // In the special case of the orthogonalize transformation if new inputs are selected
    // we need to make sure we remove them from the 'wrt' parameter if they've already been added there
    const { name, parameters } = this.state;
    const inputIds = new Set(inputs.map(x => x.id));
    const newParameters = (name === 'orthogonalize') ?
      parameters.map(param =>
        param.kind === 'predictors' ?
          { ...param, value: param.value.filter(x => !inputIds.has(x)) } :
          param
      ) :
      parameters;
    this.setState({ inputs, parameters: newParameters });
  }

  updateXformType = (name: TransformName) => {
    const { xformRules } = this.props;
    const parameters = [...xformRules[name].parameters];
    this.setState({ name, parameters });
  }

  onSave = () => {
    const { xform } = this.props;
    const { name, inputs, parameters } = this.state;
    if (!name) {
      displayError(new Error('Please select a transformation'));
      return;
    }
    const newXform: Transformation = {
      name, parameters,
      inputs: inputs.map(p => p.id)
    };
    this.props.onSave(newXform);
  }

  render() {
    const { xform, xformRules, availableInputs } = this.props;
    const { name, parameters, inputs } = this.state;
    const editMode = !!xform;
    const allowedXformNames = Object.keys(xformRules);
    const availableParameters = name ? xformRules[name].parameters : undefined;
    return (
      <div>
        <Form layout="horizontal">
          <FormItem label="Transformation:">
            <Select
              style={{ width: 120 }}
              value={name}
              onChange={this.updateXformType}
            >
              {allowedXformNames.map(x => <Option value={x} key={x}>{x}</Option>)}
            </Select>
          </FormItem>
          {name &&
            <div>
              <p>Select inputs:</p>
              <PredictorSelector
                availablePredictors={availableInputs}
                selectedPredictors={inputs}
                updateSelection={inputs => this.updateInputs(inputs)}
              />
              <br />
              {availableParameters && availableParameters.map(param => {
                let options: Predictor[] = [];
                if (param.name === 'wrt') {
                  // Special case for wrt parameter: in 'options' exclude predictors 
                  // that were selected for 'inputs'
                  const inputIds = new Set(inputs.map(x => x.id));
                  options = availableInputs.filter(x => !inputIds.has(x.id));
                }
                return (
                  <div>
                    {(param.name !== 'wrt' || inputs.length > 0) &&
                      <ParameterField
                        name={param.name}
                        value={parameters.filter(x => x.name === param.name)[0].value}
                        kind={param.kind}
                        options={options}
                        onChange={value => this.updateParameter(param.name, value)}
                      />
                    }
                  </div>
                )
              })
              }
              <br />
            </div>
          }
          <Button type="primary" onClick={this.onSave} >OK </Button>
          <Space />
          <Button onClick={this.props.onCancel} >Cancel </Button>
        </Form>
      </div>
    )
  }
}

interface ParameterFieldProps {
  name: string;
  kind: string;
  options?: Object[];
  value?: any;
  onChange: (value: any) => void;
}
class ParameterField extends React.Component<ParameterFieldProps>{
  BooleanField = () => {
    const { name, value, onChange } = this.props;
    return (
      <div>
        <Checkbox
          checked={value}
          onChange={() => onChange(!value)}
        >{name}
        </Checkbox>
        <br />
      </div>
    );
  }

  WrtField = () => {
    const { name, onChange, value, options } = this.props;
    // const selectedPredictors = (options as Predictor[] || []).filter(p => value.indexOf(p.id) > -1);
    const wrtSet = new Set(value as string[]);
    const selectedPredictors = (options as Predictor[] || []).filter(p => wrtSet.has(p.id));
    return (
      <div>
        <p>{"Select predictors you'd like to orthogonzlie against:"}</p>
        <PredictorSelector
          availablePredictors={options as Predictor[]}
          selectedPredictors={selectedPredictors}
          updateSelection={predictors => onChange(predictors.map(x => x.id))}
        />
        <br />
      </div>
    );
  }

  render() {
    const { kind } = this.props;
    return (
      <span>
        {kind === 'boolean' && this.BooleanField()}
        {kind === 'predictors' && this.WrtField()}
      </span>
    );
  }
}