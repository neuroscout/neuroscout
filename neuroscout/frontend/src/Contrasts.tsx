/*
 This module includes the following components:

 - ContrastsTab: parent component for the contrast tab of the analysis builder
 - ContrastDisplay: component to display a single contrast
*/
import * as React from 'react';
import { Table, Input, Button, Row, Col, Form, Select, Checkbox, Icon, List } from 'antd';
import {
  DragDropContext,
  Draggable,
  Droppable,
  DroppableProvided,
  DraggableLocation,
  DropResult,
  DroppableStateSnapshot, DraggableProvided, DraggableStateSnapshot
} from 'react-beautiful-dnd';
import { Analysis, Predictor, Contrast } from './coretypes';
import { displayError, moveItem, reorder } from './utils';
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
  editIndex: number;
}

interface ContrastDisplayProps {
  index: number;
  contrast: Contrast;
  onDelete: (index: number) => void;
  onEdit: (index: number) => void;
}

const ContrastDisplay = (props: ContrastDisplayProps) => {
  const { contrast, index, onDelete, onEdit } = props;
  const inputs = contrast.ConditionList || [];
  return (
    <div style={{'width': '100%'}}>
      <div  style={{'float': 'right'}}>
        <Button type="primary" onClick={() => onEdit(index)}>
          <Icon type="edit" />
        </Button>
        <Button type="danger" onClick={() => onDelete(index)}>
          <Icon type="delete" />
        </Button>
      </div>
      <div>
        <b>{`${index + 1}: ${contrast.Name}`} </b>{`${contrast.ContrastType} test`}<br/>
        {/*contrast.ConditionList && contrast.ConditionList.map((predictor, i) => {
          return(predictor + ': ' + contrast.Weights[i] + ' ');
        })*/}
      </div>
    </div>
  );
};

export class ContrastsTab extends React.Component<ContrastsTabProps, ContrastsTabState> {
  constructor(props: ContrastsTabProps) {
    super(props);
    this.state = { mode: 'view', editIndex: -1 };
  }

  onSave = (contrast: Contrast) => {
    let { editIndex } = this.state;
    let newContrasts = this.props.contrasts;
    if (editIndex >= 0) {
      newContrasts[editIndex] = contrast;
    } else {
      newContrasts.push(contrast);
    }
    this.props.onSave(newContrasts);
    this.setState({ mode: 'view', editIndex: -1 });
  };

  onDelete = (index: number) => {
    // Delete contrast with index
    const newContrasts = this.props.contrasts.filter((elemm, i) => i !== index);
    if (this.state.editIndex === index) {
      this.setState({editIndex: -1, mode: 'view'});
    }
    this.props.onSave(newContrasts);
  };

  onEdit = (index: number) => {
    this.setState({editIndex: index, mode: 'add'});
  };

  onDragEnd = (result: DropResult): void  => {

    const { source, destination } = result;

    if (!destination) {
      return;
    }

    let newContrasts = reorder(
      this.props.contrasts,
      source.index,
      destination.index
    );

    if (this.state.editIndex === source.index) {
      this.setState({editIndex: destination.index});
    }

    this.props.onSave(newContrasts);
  };

  updateAnalysis = (attrName: string) => (value: any) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = value;
    this.props.updateAnalysis(newAnalysis);
  };

  getStyle = (index: number): string => {
    let style: any = {};
    if (index === this.state.editIndex) {
      return 'selectedXform';
    }
    return 'unselectedXform';
  }

  render() {
    const { contrasts, predictors } = this.props;
    const { mode, editIndex } = this.state;
    let currentEditCont: (Contrast | undefined) = undefined;
    if (editIndex >= 0) {
      currentEditCont = this.props.contrasts[editIndex];
    }
    const AddMode = () => (
      <div>
        {this.state.editIndex === -1 &&
          <h2>
            'Add a new contrast:'
          </h2>
        }
        <ContrastEditor
          onSave={this.onSave}
          onCancel={() => this.setState({ mode: 'view', editIndex: -1 })}
          availablePredictors={predictors}
          contrast={currentEditCont}
          key={editIndex}
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
        {contrasts.length &&
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
                    dataSource={this.props.contrasts}
                    renderItem={(contrast, index) => (
                      <List.Item className={this.getStyle(index)}>
                        <Draggable key={index} draggableId={'' + index} index={index}>
                          {(providedDraggable: DraggableProvided, snapshotDraggable: DraggableStateSnapshot) => (
                              <div 
                                style={{'width': '100%'}}
                                ref={providedDraggable.innerRef}
                                {...providedDraggable.dragHandleProps}
                              >
                                <div {...providedDraggable.draggableProps}>
                                  <ContrastDisplay
                                    key={index}
                                    index={index}
                                    contrast={contrast}
                                    onDelete={this.onDelete}
                                    onEdit={this.onEdit}
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
        }
        {!contrasts.length && <p>{'You haven\'t added any contrasts'}</p>}
        <br />
        <Button type="default" onClick={() => this.setState({ mode: 'add' })}>
          <Icon type="plus" /> Add Contrast
        </Button>
      </div>
    );

    return (
      <div>
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
