import * as React from 'react';
import { Form, Input, Button, Radio, message, Modal, Alert } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor, Contrast } from './coretypes';
import { PredictorSelector } from './Predictors';
import { Space } from './HelperComponents';

const FormItem = Form.Item;
const RadioGroup = Radio.Group;
const CONTRAST_TYPE_OPTIONS: ('T' | 'F')[] = ['T', 'F'];

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
}

export default class ContrastEditor extends React.Component<
  ContrastEditorProps,
  ContrastEditorState
> {
  constructor(props: ContrastEditorProps) {
    super();
    const { contrast, availablePredictors } = props;
    this.state = {
      predictors: [],
      name: contrast ? contrast.name : '',
      weights: contrast ? contrast.weights : [],
      contrastType: 'T',
      errors: []
    };
  }

  // Validate and save contrast
  onSave = (): void => {
    const { name, predictors, weights, contrastType } = this.state;
    let errors: string[] = [];
    if (!name) {
      errors.push('Please specify a name for the contrast');
    }
    if (predictors.length !== weights.length) {
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
    const newContrast: Contrast = { name, predictors, weights, contrastType };
    this.props.onSave(newContrast);
  };

  updatePredictors = (predictors: Predictor[]): void => {
    const that = this;
    // Warn user if they have already entered weights but are now changing the predictors
    if (this.state.weights.length > 0) {
      Modal.confirm({
        title: 'Are you sure?',
        content: 'You have already entered some weights. Changing the selection will discard that.',
        okText: 'Yes',
        cancelText: 'No',
        onOk: () => that.setState({ predictors, weights: [] })
      });
      return;
    }
    this.setState({ predictors });
  };

  updateWeight = (index: number, value: number) => {
    let weights = [...this.state.weights];
    weights[index] = value;
    this.setState({ weights });
  };

  render() {
    const { name, predictors, weights, contrastType, errors } = this.state;
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
                  {errors.map(x =>
                    <li>
                      {x}
                    </li>
                  )}
                </ul>
              }
            />
            <br />
          </div>}
        <Form>
          <FormItem>
            <Input
              placeholder="Name of contrast"
              value={name}
              onChange={(event: React.FormEvent<HTMLInputElement>) =>
                this.setState({ name: event.currentTarget.value })}
              type="text"
            />
          </FormItem>
        </Form>
        <p>Select predictors:</p>
        <PredictorSelector
          availablePredictors={availablePredictors}
          selectedPredictors={predictors}
          updateSelection={this.updatePredictors}
        />
        <br />
        <p>Enter weights for the selected predictors:</p>
        <br />
        <Form layout="horizontal">
          {predictors.map((predictor, i) =>
            <FormItem
              label={predictor.name}
              key={i}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 2 }}
            >
              <Input
                value={weights[i]}
                type="number"
                onChange={(event: React.FormEvent<HTMLInputElement>) =>
                  this.updateWeight(i, parseInt(event.currentTarget.value))}
              />
            </FormItem>
          )}
          <FormItem>
            <RadioGroup
              value={contrastType}
              onChange={(event: any) =>
                this.setState({ contrastType: event.target.value as 'T' | 'F' })}
            >
              {CONTRAST_TYPE_OPTIONS.map(x =>
                <Radio key={x} value={x}>
                  {x}
                </Radio>
              )}
            </RadioGroup>
          </FormItem>
        </Form>
        <Button type="primary" onClick={this.onSave}>
          OK{' '}
        </Button>
        <Space />
        <Button onClick={this.props.onCancel}>Cancel </Button>
      </div>
    );
  }
}
