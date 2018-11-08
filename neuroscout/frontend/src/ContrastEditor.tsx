/*
 ContrastEditor module for adding/editing a contrast (used in the Contrasts tab)
*/
import * as React from 'react';
import { Form, Input, InputNumber, Button, Radio, message, Modal, Alert } from 'antd';
import { Analysis, Predictor, Contrast } from './coretypes';
import { PredictorSelector } from './Predictors';
import { Space } from './HelperComponents';

const FormItem = Form.Item;
const RadioGroup = Radio.Group;
const CONTRAST_TYPE_OPTIONS: ('T')[] = ['T'];

/*
Contrast editor component to add new contrasts. May extend this in the future 
to also add edit functionality.
*/
interface ContrastEditorProps {
  contrast?: Contrast; // Specify a contrast only when editing an existing one
  onSave: (contrast: Contrast) => void;
  onCancel: () => void;
  availablePredictors: Predictor[];
}

interface ContrastEditorState extends Contrast {
  errors: string[];
  selectedPredictors: Predictor[];
}

export default class ContrastEditor extends React.Component<
  ContrastEditorProps,
  ContrastEditorState
> {
  constructor(props: ContrastEditorProps) {
    super(props);
    const { contrast, availablePredictors } = props;
    this.state = {
      condition_list: [],
      name: contrast ? contrast.name : '',
      weights: contrast ? contrast.weights : [],
      contrastType: 't',
      errors: [],
      selectedPredictors: []
    };
  }

  // Validate and save contrast
  onSave = (): void => {
    const { name, condition_list, weights, contrastType } = this.state;
    let errors: string[] = [];
    if (!name) {
      errors.push('Please specify a name for the contrast');
    }
    if (condition_list.length !== weights.length) {
      errors.push('Please enter a numeric weight for each predictor');
    }
    weights.forEach((value, index) => {
      if (typeof value !== 'number')
        errors.push(`Weight at position ${index} must be a numeric value`);
    });
    if (errors.length > 0) {
      this.setState({ errors });
      return;
    }
    const newContrast: Contrast = { name, condition_list, weights, contrastType };
    this.props.onSave(newContrast);
  };

  updatePredictors = (selectedPredictors: Predictor[]): void => {
    const that = this;
    // Warn user if they have already entered weights but are now changing the predictors
    let updatedPredictors = selectedPredictors.map(x => x.name);
    if (this.state.weights.length > 0) {
      Modal.confirm({
        title: 'Are you sure?',
        content: 'You have already entered some weights. Changing the selection will discard that.',
        okText: 'Yes',
        cancelText: 'No',
        onOk: () => that.setState({ selectedPredictors, weights: [], condition_list: updatedPredictors})
      });
      return;
    }
    this.setState({ selectedPredictors, condition_list: updatedPredictors});
  };

  updateWeight = (index: number, value: number) => {
    let weights = [...this.state.weights];
    weights[index] = value;
    this.setState({ weights });
  };

  parseInput = (val: string) => {
    if (val === '-') { val = '-0'; }
    return parseInt(val, 10);
  }

  render() {
    const { name, condition_list, selectedPredictors, weights, contrastType, errors } = this.state;
    const { availablePredictors } = this.props;
    return (
      <div>
        {errors.length > 0 &&
          <div>
            <Alert
              type="error"
              showIcon={true}
              closable={true}
              message={
                <ul>
                  {errors.map((x, i) =>
                    <li key={i}>
                      {x}
                    </li>
                  )}
                </ul>
              }
            />
            <br />
          </div>}
        <Form>
          <FormItem required={true} label={'Name of Contrast:'}>
            <Input
              placeholder="Name of contrast"
              value={name}
              onChange={(event: React.FormEvent<HTMLInputElement>) =>
                this.setState({ name: event.currentTarget.value })}
              type="text"
              required={true}
              min={1}
            />
          </FormItem>
        </Form>
        <p>Select predictors:</p>
        <PredictorSelector
          availablePredictors={availablePredictors}
          selectedPredictors={selectedPredictors}
          updateSelection={this.updatePredictors}
        />
        <br />
        <p>Enter weights for the selected predictors:</p>
        <br />
        <Form layout="horizontal">
          {condition_list.map((predictor, i) =>
            <FormItem
              label={predictor}
              key={i}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 2 }}
              required={true}
            >
              <InputNumber
                value={weights[i]}
                onChange={(this.updateWeight.bind(this, i))}
                required={true}
              />
            </FormItem>
          )}
          <FormItem label={'Contrast type:'}>
            <RadioGroup
              value={contrastType}
              onChange={(event: any) =>
                this.setState({ contrastType: event.target.value as 't' | 'F' })}
            >
              {CONTRAST_TYPE_OPTIONS.map(x =>
                <Radio key={x} value={x}>
                  {x}
                </Radio>
              )}
            </RadioGroup>
          </FormItem>
        </Form>
        <Button
          type="primary"
          onClick={this.onSave}
          disabled={
            !(this.state.name && this.state.condition_list.length > 0 
            && this.state.condition_list.length === this.state.weights.length)
          }
        >
          OK{' '}
        </Button>
        <Space />
        <Button onClick={this.props.onCancel}>Cancel </Button>
      </div>
    );
  }
}
