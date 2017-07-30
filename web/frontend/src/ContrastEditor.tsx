import * as React from 'react';
import { Form, Input, Button } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, Predictor, Contrast } from './coretypes';
import { PredictorSelector } from './Predictors';
import { Space } from './HelperComponents';

const FormItem = Form.Item;

interface ContrastEditorProps {
  contrast?: Contrast;
  onSave: (contrast: Contrast) => void;
  onCancel: () => void;
  availablePredictors: Predictor[];
}

interface ContrastEditorState extends Contrast {}

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
      contrastType: 'T'
    };
  }

  onSave = (): void => {
    const newContrast: Contrast = { ...this.state };
    this.props.onSave(newContrast);
  };

  updatePredictors = (predictors: Predictor[]): void => {
    this.setState({ predictors });
  };

  updateWeight = (index: number, value: number) => {
    let weights = [...this.state.weights];
    weights[index] = value;
    this.setState({ weights });
  };

  render() {
    const { name, predictors, weights } = this.state;
    const { availablePredictors } = this.props;
    return (
      <div>
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
        <Form layout="horizontal">
          {predictors.map((predictor, i) =>
            <FormItem
              label={predictor.name}
              key={i}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 10 }}
            >
              <Input
                value={weights[i]}
                type="number"
                onChange={(event: React.FormEvent<HTMLInputElement>) =>
                  this.updateWeight(i, parseInt(event.currentTarget.value))}
              />
            </FormItem>
          )}
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
