/*
 This module includes the following components:

 - ContrastsTab: parent component for the contrast tab of the analysis builder
 - ContrastDisplay: component to display a single contrast
*/
import * as React from 'react';
import { Table, Input, Button, Row, Col, Form, Select, Checkbox, Icon } from 'antd';
import { Analysis, Predictor, Contrast } from './coretypes';
import { displayError, moveItem } from './utils';
import { Space } from './HelperComponents';
import { PredictorSelector } from './Predictors';
import ContrastEditor from './ContrastEditor';
const Option = Select.Option;

interface ContrastsTabProps {
  predictors: Predictor[];
  contrasts: Contrast[];
  onSave: (contrasts: Contrast[]) => void;
  analysis: Analysis;
  updateAnalysis: (value: any) => void;
}

interface ContrastsTabState {
  mode: 'add' | 'edit' | 'view';
}

interface ContrastDisplayProps {
  index: number;
  contrast: Contrast;
  onDelete: (index: number) => void;
  enableUp: boolean;
  enableDown: boolean;
  onMove: (index: number, direction: 'up' | 'down') => void;
}

const ContrastDisplay = (props: ContrastDisplayProps) => {
  const { contrast, index, onDelete, onMove, enableUp, enableDown } = props;
  const inputs = contrast.ConditionList || [];
  return (
    <div>
      <h3>{`${index + 1}: ${contrast.Name}`}</h3>
      <p>Weights:</p>
      <ul>
        {contrast.ConditionList && contrast.ConditionList.map((predictor, i) =>
          <li key={i}>
            {predictor + ': ' + contrast.Weights[i]}
          </li>
        )}
      </ul>
      <p>{`Contrast type: ${contrast.ContrastType}`}</p>
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
      <br />
      <br />
    </div>
  );
};

export class ContrastsTab extends React.Component<ContrastsTabProps, ContrastsTabState> {
  constructor(props: ContrastsTabProps) {
    super(props);
    this.state = { mode: 'view' };
  }

  onAdd = (contrast: Contrast) => {
    const newContrasts = [...this.props.contrasts, ...[contrast]];
    this.props.onSave(newContrasts);
    this.setState({ mode: 'view' });
  };

  onDelete = (index: number) => {
    // Delete contrast with index
    const newContrasts = this.props.contrasts.filter((elemm, i) => i !== index);
    this.props.onSave(newContrasts);
  };

  onMoveXform = (index: number, direction: 'up' | 'down') => {
    const newContrasts = moveItem(this.props.contrasts, index, direction);
    this.props.onSave(newContrasts);
  };

  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  };

  render() {
    const { contrasts, predictors } = this.props;
    const { mode } = this.state;
    const AddMode = () => (
      <div>
        <h2>
          {'Add a new contrast:'}
        </h2>
        <ContrastEditor
          onSave={this.onAdd}
          onCancel={() => this.setState({ mode: 'view' })}
          availablePredictors={predictors}
        />
      </div>
    );

    const ViewMode = () => (
      <div>
        <h2>
          {'Contrasts'}
        </h2>
          <Checkbox
            checked={this.props.analysis.autoContrast}
            onChange={() => this.updateAnalysis('autoContrast')(!this.props.analysis.autoContrast)}
          >
            {'Automatically generate identity contrasts'}
          </Checkbox>
        <br />
        {contrasts.length
          ? contrasts.map((contrast, index) =>
              <ContrastDisplay
                key={index}
                index={index}
                contrast={contrast}
                onDelete={this.onDelete}
                onMove={this.onMoveXform}
                enableUp={index > 0}
                enableDown={index < contrasts.length - 1}
              />
            )
          : <p>
              {'You haven\'t added any contrasts'}
            </p>}
        <br />
        <Button type="default" onClick={() => this.setState({ mode: 'add' })}>
          <Icon type="plus" /> Add Contrast
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
