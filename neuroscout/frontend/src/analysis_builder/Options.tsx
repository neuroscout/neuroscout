/*
 Options tab of the analysis builder
*/
import * as React from 'react'
import {
  Row,
  Col,
  Slider,
  InputNumber,
  Collapse,
  Checkbox,
  Select,
  Form,
} from 'antd'
import {
  Analysis,
  AnalysisConfig,
  Predictor,
  PredictorConfig,
} from '../coretypes'
const Panel = Collapse.Panel
const Option = Select.Option

const SMOOTHING_MIN = 0
const SMOOTHING_MAX = 10

interface OptionsTabProps {
  analysis: Analysis
  selectedPredictors: Predictor[]
  updateConfig: (newConfig: AnalysisConfig) => void
  updateAnalysis: (value: any) => void
}

export default class OptionsTab extends React.Component<OptionsTabProps, void> {
  updateGlobalConfig =
    (key: keyof AnalysisConfig) =>
    (value: AnalysisConfig[keyof AnalysisConfig]) => {
      const { analysis, updateConfig } = this.props
      const newConfig = { ...analysis.config, [key]: value }
      updateConfig(newConfig)
    }

  updatePredictorConfig = (
    id: string,
    key: keyof PredictorConfig,
    value: PredictorConfig[keyof PredictorConfig],
  ): void => {
    const { analysis, updateConfig } = this.props
    const newConfig: AnalysisConfig = { ...analysis.config }
    const newPredictorConfig = { ...newConfig.predictorConfigs }
    newPredictorConfig[id][key] = value as never
    newConfig.predictorConfigs = newPredictorConfig
    updateConfig(newConfig)
  }

  updateAnalysis =
    (attrName: string) =>
    (value: Analysis[keyof Analysis]): void => {
      const newAnalysis = { ...this.props.analysis }
      newAnalysis[attrName] = value
      this.props.updateAnalysis(newAnalysis)
    }

  render() {
    const { analysis, selectedPredictors } = this.props
    const { predictorConfigs } = analysis.config
    return (
      <div>
        <Form layout="horizontal">
          <h3>Global Configurations</h3>
          <br />
          <Form.Item label="Smoothing:">
            <Row>
              <Col span={12}>
                <Slider
                  min={SMOOTHING_MIN}
                  max={SMOOTHING_MAX}
                  onChange={this.updateGlobalConfig('smoothing')}
                  value={analysis.config.smoothing}
                />
              </Col>
              <Col span={4}>
                <InputNumber
                  min={SMOOTHING_MIN}
                  max={SMOOTHING_MAX}
                  style={{ marginLeft: 16 }}
                  onChange={this.updateGlobalConfig('smoothing')}
                  value={analysis.config.smoothing}
                />
              </Col>
            </Row>
          </Form.Item>
          <h3>Per-Predictor Configurations</h3>
          <br />
          <Collapse defaultActiveKey={['1']}>
            {selectedPredictors.map(predictor => {
              const { id, name } = predictor
              const { convolution, temporalDerivative, orthogonalize } =
                predictorConfigs[id]
              return (
                <Panel header={name} key={id}>
                  <Form.Item>
                    <span>Convolution: </span>
                    <Select
                      style={{ width: 120 }}
                      value={convolution}
                      onChange={value =>
                        this.updatePredictorConfig(id, 'convolution', value)
                      }
                    >
                      {['Gamma', 'Alpha', 'Beta'].map(conv => (
                        <Option value={conv} key={conv}>
                          {conv}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                  <Checkbox
                    checked={temporalDerivative}
                    onChange={() =>
                      this.updatePredictorConfig(
                        id,
                        'temporalDerivative',
                        !temporalDerivative,
                      )
                    }
                  >
                    {'Temporal Derivative'}
                  </Checkbox>
                  <Checkbox
                    checked={orthogonalize}
                    onChange={() =>
                      this.updatePredictorConfig(
                        id,
                        'orthogonalize',
                        !orthogonalize,
                      )
                    }
                  >
                    {'Orthogonalize'}
                  </Checkbox>
                </Panel>
              )
            })}
          </Collapse>
        </Form>
      </div>
    )
  }
}
