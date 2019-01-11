/*
 ContrastEditor module for adding/editing a contrast (used in the Contrasts tab)
*/
import * as React from 'react';
import { Form, Input, InputNumber, Button, Radio, message, Modal, Alert } from 'antd';
import { Analysis, Predictor, Contrast, ContrastTypeEnum } from './coretypes';
import { PredictorSelector } from './Predictors';
import { Space } from './HelperComponents';

const FormItem = Form.Item;
const RadioGroup = Radio.Group;
const CONTRAST_TYPE_OPTIONS: ('T')[] = ['T'];

export function emptyContrast() {
    return {
        ConditionList: [],
        Name: '',
        Weights:  [],
        ContrastType: 't' as ContrastTypeEnum
    };
}

export function validateContrast(contrast: Contrast): string[] {
    const { Name, ConditionList, Weights, ContrastType } = contrast;
    let errors: string[] = [];
    if (!Name) {
      errors.push('Please specify a name for the contrast');
    }
    if (ConditionList.length !== Weights.length) {
      errors.push('Please enter a numeric weight for each predictor');
    }
    Weights.forEach((value, index) => {
      if (typeof value !== 'number')
        errors.push(`Weight for '${ConditionList[index]}' must be a numeric value`);
    });
    return errors;
}

/*
Contrast editor component to add new contrasts. May extend this in the future
to also add edit functionality.
*/
interface ContrastEditorProps {
  activeContrast: Contrast; // Specify a contrast only when editing an existing one
  onSave: (contrast: Contrast) => void;
  onCancel: () => void;
  availablePredictors: Predictor[];
  contrastErrors: string[];
  updateBuilderState: (value: any) => any;
}

interface ContrastEditorState extends Contrast {
  selectedPredictors: Predictor[];
}

export class ContrastEditor extends React.Component<
  ContrastEditorProps,
  ContrastEditorState
> {
  constructor(props: ContrastEditorProps) {
    super(props);
    const { activeContrast, availablePredictors } = props;
    let state;
    if (activeContrast) {
      state = {
        selectedPredictors: availablePredictors.filter(x => activeContrast.ConditionList.indexOf(x.name) >= 0),
      };
    } else {
      state = {
        selectedPredictors: []
      };
      this.props.updateBuilderState('activeContrast')(emptyContrast());
    }
    this.state = state;
  }

  // Validate and save contrast
  onSave = (): void => {
    let errors = validateContrast(this.props.activeContrast);
    if (errors.length > 0) {
      this.props.updateBuilderState('contrastErrors')(errors);
      return;
    }
    this.props.onSave({...this.props.activeContrast});
  };

  updatePredictors = (selectedPredictors: Predictor[]): void => {
    const that = this;
    // Warn user if they have already entered Weights but are now changing the predictors
    let updatedPredictors = selectedPredictors.map(x => x.name);
    if (this.props.activeContrast.Weights.length > 0) {
      Modal.confirm({
        title: 'Are you sure?',
        content: 'You have already entered some Weights. Changing the selection will discard that.',
        okText: 'Yes',
        cancelText: 'No',
        onOk: () => {
          that.props.updateBuilderState('activeContrast')({
            ...this.props.activeContrast,
            selectedPredictors,
            Weights: new Array(updatedPredictors.length).fill(1),
            ConditionList: updatedPredictors
          });
          this.setState({ selectedPredictors });
        }
      });
      return;
    }
    this.props.updateBuilderState('activeContrast')({...this.props.activeContrast, ConditionList: updatedPredictors});
    this.setState({ selectedPredictors, ConditionList: updatedPredictors});
  };

  updateWeight = (index: number, value: number) => {
    if (this.props.activeContrast === undefined) {
      // how did we get here with with an index and a value... but the type script gods demand it
      return;
    }
    let Weights = [...this.props.activeContrast.Weights];
    Weights[index] = value;
    this.props.updateBuilderState('activeContrast')({...this.props.activeContrast, Weights });
  };

  parseInput = (val: string) => {
    if (val === '-') { val = '-0'; }
    return parseInt(val, 10);
  }

  render() {
    const { selectedPredictors } = this.state;
    let { Name, ConditionList, Weights, ContrastType } = this.props.activeContrast;
    const { availablePredictors } = this.props;
    return (
      <div>
        {this.props.contrastErrors.length > 0 &&
          <div>
            <Alert
              type="error"
              showIcon={true}
              closable={true}
              message={
                <ul>
                  {this.props.contrastErrors.map((x, i) =>
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
              value={Name}
              onChange={(event: React.FormEvent<HTMLInputElement>) =>
                this.props.updateBuilderState('activeContrast')({
                  ...this.props.activeContrast,
                  Name: event.currentTarget.value
                })}
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
          compact={true}
        />
        <br />
        <p>Enter Weights for the selected predictors:</p>
        <br />
        <Form layout="horizontal">
          {ConditionList.map((predictor, i) =>
            <FormItem
              label={predictor}
              key={i}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 2 }}
              required={true}
            >
              <InputNumber
                value={Weights[i]}
                onChange={(this.updateWeight.bind(this, i))}
                required={true}
              />
            </FormItem>
          )}
          <FormItem label={'Contrast type:'}>
            <RadioGroup
              value={ContrastType}
              onChange={(event: any) =>
                this.props.updateBuilderState('activeContrast')({
                  ...this.props.activeContrast,
                  ContrastType: event.target.value as 't' | 'F' }
                )}
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
            !(this.props.activeContrast.Name && this.props.activeContrast.ConditionList.length > 0
            && this.props.activeContrast.ConditionList.length === this.props.activeContrast.Weights.length)
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
