/*
 ContrastEditor module for adding/editing a contrast (used in the Contrasts tab)
*/
import * as React from 'react'
import {
  Input,
  InputNumber,
  Button,
  Radio,
  Modal,
  Form,
  RadioChangeEvent,
} from 'antd'
import {
  Predictor,
  Contrast,
  ContrastTypeEnum,
  UpdateBuilderState,
} from '../coretypes'
import { PredictorSelector } from './Predictors'
import { DisplayErrorsInline, Space } from '../HelperComponents'

const FormItem = Form.Item
const RadioGroup = Radio.Group
const CONTRAST_TYPE_OPTIONS: 't'[] = ['t']

export function emptyContrast(): Contrast {
  return {
    ConditionList: [] as string[],
    Name: '',
    Weights: [] as number[],
    Type: 't' as ContrastTypeEnum,
  }
}

export function validateContrast(contrast: Contrast): string[] {
  const { Name, ConditionList, Weights } = contrast
  const errors: string[] = []
  if (!Name) {
    errors.push('Please specify a name for the contrast')
  }
  if (ConditionList.length !== Weights.length) {
    errors.push('Please enter a numeric weight for each predictor')
  }
  Weights.forEach((value, index) => {
    if (typeof value !== 'number')
      errors.push(
        `Weight for '${ConditionList[index]}' must be a numeric value`,
      )
  })
  return errors
}

/*
Contrast editor component to add new contrasts. May extend this in the future
to also add edit functionality.
*/
interface ContrastEditorProps {
  activeContrast: Contrast // Specify a contrast only when editing an existing one
  onSave: (contrast: Contrast) => void
  onCancel: () => void
  availablePredictors: Predictor[]
  contrastErrors: string[]
  updateBuilderState: UpdateBuilderState
}

interface ContrastEditorState extends Contrast {
  selectedPredictors: Predictor[]
}

export class ContrastEditor extends React.Component<
  ContrastEditorProps,
  ContrastEditorState
> {
  constructor(props: ContrastEditorProps) {
    super(props)
    const { activeContrast, availablePredictors } = props
    const state: ContrastEditorState = {
      ...emptyContrast(),
      selectedPredictors: [],
    }
    if (activeContrast) {
      state.selectedPredictors = availablePredictors.filter(
        x => activeContrast.ConditionList.indexOf(x.name) >= 0,
      )
    }
    this.state = state
  }

  // Validate and save contrast
  onSave = (): void => {
    this.props.updateBuilderState('contrastErrors')([] as string[])
    const errors = validateContrast(this.props.activeContrast)
    if (errors.length > 0) {
      this.props.updateBuilderState('contrastErrors')(errors)
      return
    }
    this.props.onSave({ ...this.props.activeContrast })
  }

  updatePredictors = (selectedPredictors: Predictor[]): void => {
    // Warn user if they have already entered Weights but are now changing the predictors
    const updatedPredictors = selectedPredictors.map(x => x.name)
    if (this.props.activeContrast.Weights.length > 0) {
      Modal.confirm({
        title: 'Are you sure?',
        content:
          'You have already entered some Weights. Changing the selection will discard that.',
        okText: 'Yes',
        cancelText: 'No',
        onOk: () => {
          this.props.updateBuilderState('activeContrast')({
            ...this.props.activeContrast,
            Weights: new Array(updatedPredictors.length).fill(1),
            ConditionList: updatedPredictors,
          })
          /* This was in the above state update. Moved on its own due to typing
            issues, but im not sure the builder states selectedPredictors should be updated
            here */
          this.props.updateBuilderState('selectedPredictors')(
            selectedPredictors,
          )
          this.setState({ selectedPredictors })
        },
      })
      return
    }
    this.props.updateBuilderState('activeContrast')({
      ...this.props.activeContrast,
      ConditionList: updatedPredictors,
    })
    this.setState({ selectedPredictors, ConditionList: updatedPredictors })
  }

  updateWeight = (index: number, value: number): void => {
    if (this.props.activeContrast === undefined) {
      // how did we get here with with an index and a value... but the type script gods demand it
      return
    }
    const Weights = [...this.props.activeContrast.Weights]
    Weights[index] = value
    this.props.updateBuilderState('activeContrast')({
      ...this.props.activeContrast,
      Weights,
    })
  }

  parseInput = (val: string): number => {
    if (val === '-') {
      val = '-0'
    }
    return parseInt(val, 10)
  }

  render() {
    const { selectedPredictors } = this.state
    const { Name, ConditionList, Weights, Type } = this.props.activeContrast
    const { availablePredictors } = this.props
    return (
      <div>
        <Form>
          <FormItem required label={'Name of Contrast:'}>
            <Input
              placeholder="Name of contrast"
              value={Name}
              onChange={(event: React.FormEvent<HTMLInputElement>) =>
                this.props.updateBuilderState('activeContrast')({
                  ...this.props.activeContrast,
                  Name: event.currentTarget.value,
                })
              }
              type="text"
              required
              min={1}
            />
          </FormItem>
        </Form>
        <p>Select predictors:</p>
        <PredictorSelector
          availablePredictors={availablePredictors}
          selectedPredictors={selectedPredictors}
          updateSelection={this.updatePredictors}
          compact
        />
        <br />
        <p>Enter Weights for the selected predictors:</p>
        <br />
        <Form layout="horizontal">
          {ConditionList.map((predictor, i) => (
            <FormItem
              label={predictor}
              key={i}
              labelCol={{ span: 4 }}
              wrapperCol={{ span: 2 }}
              required
              className="contrast-type-form-item"
            >
              <InputNumber
                value={Weights[i]}
                onChange={this.updateWeight.bind(this, i)}
                required
              />
            </FormItem>
          ))}
          <FormItem label={'Contrast type:'}>
            <RadioGroup
              value={Type}
              onChange={(event: RadioChangeEvent) =>
                this.props.updateBuilderState('activeContrast')({
                  ...this.props.activeContrast,
                  Type: event.target.value as 't' | 'F',
                })
              }
            >
              {CONTRAST_TYPE_OPTIONS.map(x => (
                <Radio key={x} value={x}>
                  {x}
                </Radio>
              ))}
            </RadioGroup>
          </FormItem>
        </Form>
        <DisplayErrorsInline errors={this.props.contrastErrors} />
        <Space />
        <Button type="primary" onClick={this.onSave}>
          OK{' '}
        </Button>
        <Space />
        <Button onClick={this.props.onCancel}>Cancel </Button>
      </div>
    )
  }
}
