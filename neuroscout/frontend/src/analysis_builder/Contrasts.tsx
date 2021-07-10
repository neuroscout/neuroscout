/*
 This module includes the following components:

 - ContrastsTab: parent component for the contrast tab of the analysis builder
 - ContrastDisplay: component to display a single contrast
*/
import * as React from 'react'
import { DeleteOutlined, EditOutlined, PlusOutlined } from '@ant-design/icons'
import { Button, Row, Col, List } from 'antd'
import {
  DragDropContext,
  Draggable,
  Droppable,
  DroppableProvided,
  DropResult,
  DraggableProvided,
  DraggableStateSnapshot,
} from 'react-beautiful-dnd'

import { Analysis, Predictor, Contrast, UpdateBuilderState } from '../coretypes'
import { reorder } from '../utils'
import { DisplayErrorsInline } from '../HelperComponents'
import { ContrastEditor, emptyContrast } from './ContrastEditor'

interface ContrastDisplayProps {
  index: number
  contrast: Contrast
  onDelete: (index: number) => void
  onEdit: (index: number) => void
}

const ContrastDisplay = (props: ContrastDisplayProps) => {
  const { contrast, index, onDelete, onEdit } = props
  return (
    <div style={{ width: '100%' }}>
      <div style={{ float: 'right' }}>
        <Button type="primary" onClick={() => onEdit(index)}>
          <EditOutlined />
        </Button>
        <Button danger onClick={() => onDelete(index)}>
          <DeleteOutlined />
        </Button>
      </div>
      <div>
        <b>{`${contrast.Name}`} </b>
        {`${contrast.Type} test`}
        <br />
        {/* contrast.ConditionList && contrast.ConditionList.map((predictor, i) => {
          return(predictor + ': ' + contrast.Weights[i] + ' ');
        })*/}
      </div>
    </div>
  )
}

interface ContrastsTabProps {
  predictors: Predictor[]
  contrasts: Contrast[]
  onSave: (contrasts: Contrast[]) => void
  analysis: Analysis
  updateAnalysis: (value: Analysis) => void
  activeContrastIndex: number
  activeContrast?: Contrast
  contrastErrors: string[]
  updateBuilderState: UpdateBuilderState
}

interface ContrastsTabState {
  mode: 'add' | 'edit' | 'view'
}

export class ContrastsTab extends React.Component<
  ContrastsTabProps,
  ContrastsTabState
> {
  constructor(props: ContrastsTabProps) {
    super(props)
    this.state = { mode: 'view' }
  }

  onSave = (contrast: Contrast): void => {
    const { activeContrastIndex } = this.props
    const newContrasts = this.props.contrasts
    if (activeContrastIndex >= 0) {
      newContrasts[activeContrastIndex] = contrast
    } else {
      newContrasts.push(contrast)
    }
    this.props.onSave(newContrasts)
    this.props.updateBuilderState('activeContrastIndex')(-1)
    this.props.updateBuilderState('activeContrast')(undefined)
    this.setState({ mode: 'view' })
  }

  onDelete = (index: number) => {
    // Delete contrast with index
    const newContrasts = this.props.contrasts.filter((elemm, i) => i !== index)
    if (this.props.activeContrastIndex === index) {
      this.setState({ mode: 'view' })
      this.props.updateBuilderState('activeContrastIndex')(-1)
    }
    this.props.onSave(newContrasts)
  }

  onEdit = (index: number) => {
    this.props.updateBuilderState('activeContrastIndex')(index)
    this.props.updateBuilderState('activeContrast')({
      ...this.props.contrasts[index],
    })
    this.props.updateBuilderState('contrastErrors')([] as string[])
    this.setState({ mode: 'add' })
  }

  onCancel = () => {
    this.props.updateBuilderState('activeContrastIndex')(-1)
    this.props.updateBuilderState('activeContrast')(undefined)
    this.props.updateBuilderState('contrastErrors')([] as string[])
    this.setState({ mode: 'view' })
  }

  onDragEnd = (result: DropResult): void => {
    const { source, destination } = result

    if (!destination) {
      return
    }

    const newContrasts = reorder(
      this.props.contrasts,
      source.index,
      destination.index,
    )

    if (this.props.activeContrastIndex === source.index) {
      this.props.updateBuilderState('activeContrastIndex')(destination.index)
    }

    this.props.onSave(newContrasts)
  }

  updateAnalysis = (attrName: string) => (value: Analysis[keyof Analysis]) => {
    const newAnalysis = { ...this.props.analysis }
    newAnalysis[attrName] = value
    this.props.updateAnalysis(newAnalysis)
  }

  addDummyContrasts = () => {
    const predictors = this.props.predictors
    const newContrasts = [...this.props.contrasts]
    predictors.map(x => {
      if (x.source === 'fmriprep') {
        return
      }
      if (
        newContrasts.filter(y => {
          return (
            y.Name === x.name &&
            y.ConditionList.length === 1 &&
            y.ConditionList[0] === x.name
          )
        }).length > 0
      ) {
        return
      }
      const newContrast = emptyContrast()
      newContrast.Name = `${x.name}`
      newContrast.ConditionList = [x.name]
      newContrast.Weights = [1]
      newContrasts.push(newContrast)
    })
    this.props.onSave(newContrasts)
  }

  removeDummyContrasts = () => {
    const predictors = this.props.predictors
    const newContrasts = this.props.contrasts.filter(
      x => predictors.map(y => y.name).indexOf(x.Name) === -1,
    )
    this.props.onSave(newContrasts)
  }

  getStyle = (index: number): string => {
    if (index === this.props.activeContrastIndex) {
      return 'selectedXform'
    }
    return 'unselectedXform'
  }

  render() {
    const { predictors, activeContrastIndex, activeContrast } = this.props
    const { mode } = this.state

    const AddMode = () => (
      <div>
        {activeContrastIndex === -1 && <h2>Add a new contrast:</h2>}
        <ContrastEditor
          onSave={this.onSave}
          onCancel={this.onCancel}
          availablePredictors={predictors}
          activeContrast={activeContrast ? activeContrast : emptyContrast()}
          updateBuilderState={this.props.updateBuilderState}
          contrastErrors={this.props.contrastErrors}
          key={activeContrastIndex}
        />
      </div>
    )

    const ViewMode = () => (
      <div>
        <br />
        {mode !== 'add' && (
          <DisplayErrorsInline errors={this.props.contrastErrors} />
        )}
        <DragDropContext onDragEnd={this.onDragEnd}>
          <Droppable droppableId="droppable">
            {(provided: DroppableProvided) => (
              // eslint-disable-next-line @typescript-eslint/unbound-method
              <div ref={provided.innerRef} {...provided.droppableProps}>
                <List
                  size="small"
                  bordered
                  dataSource={this.props.contrasts}
                  locale={{ emptyText: "You haven't added any contrasts" }}
                  renderItem={(contrast, index) => (
                    <List.Item className={this.getStyle(index)}>
                      <Draggable
                        key={index}
                        draggableId={String(index)}
                        index={index}>
                        {(
                          providedDraggable: DraggableProvided,
                          snapshotDraggable: DraggableStateSnapshot,
                        ) => (
                          <div
                            style={{ width: '100%' }}
                            // eslint-disable-next-line @typescript-eslint/unbound-method
                            ref={providedDraggable.innerRef}
                            {...providedDraggable.dragHandleProps}>
                            <div {...providedDraggable.draggableProps}>
                              <ContrastDisplay
                                key={index}
                                index={index}
                                contrast={contrast}
                                onDelete={this.onDelete}
                                onEdit={this.onEdit}
                              />
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
        <Button type="default" onClick={() => this.setState({ mode: 'add' })}>
          <PlusOutlined /> Add Contrast
        </Button>
        <p />
        <Button type="default" onClick={this.addDummyContrasts}>
          <PlusOutlined /> Generate Dummy Contrasts
        </Button>
      </div>
    )

    return (
      <div>
        <Row>
          <Col md={9}>{ViewMode()}</Col>
          <Col md={1} />
          <Col md={14}>{mode === 'add' && AddMode()}</Col>
        </Row>
      </div>
    )
  }
}
