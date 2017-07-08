import * as React from 'react';
import { Table, Input, Button, Row, Col, Form, Select, Checkbox } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor, Transformation, TransformName } from './coretypes';
import { displayError } from './utils';
import transformDefinititions from './transforms';
const Option = Select.Option;

interface XformRules {
  [name: string]: Transformation;
}

let xformRules: XformRules = {};
for (const item of transformDefinititions) {
  xformRules[item.name] = item;
}

const FormItem = Form.Item;

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

  onAddXform(xform: Transformation) {
    const newXforms = this.props.xforms.concat([xform]);
    this.props.onSave(newXforms);
    this.setState({ mode: 'view' });
  }

  render() {
    const { xforms, predictors } = this.props;
    const { mode } = this.state;
    return (
      <div>
        <h2>{'Transformations'}</h2>
        {xforms.map(xform =>
          <p>{xform.name}</p>
        )}
        <Button onClick={() => this.setState({ mode: 'add' })}>Add new transformation</Button>
        {mode === 'add' &&
          <XformEditor
            xformRules={xformRules}
            onSave={xform => this.onAddXform(xform)}
            availableInputs={predictors}
          />
        }
      </div>
    );
  }
}

interface XformEditorProps {
  xformRules: XformRules;
  onSave: (xform: Transformation) => void;
  availableInputs: Predictor[];
  xform?: Transformation;
}

interface XformEditorState {
  inputs: Predictor[];
  name: TransformName | '';
  parameters: object;
}

class XformEditor extends React.Component<XformEditorProps, XformEditorState>{
  updateParameter = (name: string, value: any) => {
    const newParameters = { ...this.state.parameters, name: value };
    this.setState({ parameters: newParameters });
  }

  constructor(props: XformEditorProps) {
    super();
    const { xform, availableInputs } = props;
    this.state = {
      inputs: availableInputs,
      name: xform ? xform.name : '',
      parameters: xform ? xform.parameters : {},
    };
  }

  onSave() {
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
    const { xform, xformRules } = this.props;
    const { name, parameters } = this.state;
    const editMode = !!xform;
    const allowedXformNames = Object.keys(xformRules);
    const customParameters = name ? xformRules[name].parameters : undefined;
    return (
      <div>
        <Form layout="vertical">
          <FormItem label="Transformation:">
            <Select
              style={{ width: 120 }}
              value={''}
              onChange={(value: TransformName) => this.setState({ name: value })}
            >
              {allowedXformNames.map(x => <Option value={x} key={x}>{x}</Option>)}
            </Select>
            <p>Parameters:</p>
            {customParameters && Object.keys(customParameters).map(p =>
              <ParameterField
                name={p}
                kind={customParameters[p]}
                onChange={value => this.updateParameter(p, value)}
              />)}
          </FormItem>
          <Button
            type="primary"
            onClick={this.onSave}
          >Save
          </Button>
        </Form>
      </div>
    )
  }
}

interface ParameterFieldProps {
  name: string;
  kind: string;
  value?: any;
  onChange: (value: any) => void;
}
class ParameterField extends React.Component<ParameterFieldProps>{
  BooleanField() {
    const { name, value, onChange } = this.props;
    return (
      <FormItem>
        <Checkbox
          checked={value}
          onChange={() => onChange(!!value)}
        >{name}
        </Checkbox>
      </FormItem>
    );
  }

  render() {
    const { kind } = this.props;
    return (
      <div>
        {kind === 'boolean' && this.BooleanField()}
      </div>
    );
  }
}