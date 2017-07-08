import * as React from 'react';
import { Form, Table, Input, Button, Row, Col, Slider, InputNumber, Collapse, Checkbox, Select } from 'antd';
import { TableProps, TableRowSelection } from 'antd/lib/table/Table';
import { Analysis, AnalysisConfig, Predictor, PredictorConfig } from './coretypes';
const FormItem = Form.Item;
const Panel = Collapse.Panel;
const Option = Select.Option;

const SMOOTHING_MIN = 10;
const SMOOTHING_MAX = 100;

interface OptionsTabProps {
  analysis: Analysis;
  selectedPredictors: Predictor[];
  updateConfig: (newConfig: AnalysisConfig) => void;
}

interface OptionsTabState {
}

export default class OptionsTab extends React.Component<OptionsTabProps, OptionsTabState> {
  state = {
  };

  updateGlobalConfig = (key: keyof AnalysisConfig) => (value: any) => {
    const { analysis, updateConfig } = this.props;
    const newConfig: AnalysisConfig = { ...analysis.config };
    newConfig[key] = value;
    updateConfig(newConfig);
  }

  updatePredictorConfig = (id: string, key: keyof PredictorConfig, value: any) => {
    const { analysis, updateConfig } = this.props;
    const newConfig: AnalysisConfig = { ...analysis.config };
    const newPredictorConfig = { ...newConfig.predictorConfigs };
    newPredictorConfig[id][key] = value;
    newConfig.predictorConfigs = newPredictorConfig;
    updateConfig(newConfig);
  }

  render() {
    const { analysis, selectedPredictors } = this.props;
    const { smoothing, predictorConfigs } = analysis.config;
    return (
      <div>
        <Form layout="horizontal">
          <h3>Global Configurations</h3>
          <br />
          <FormItem label="Smoothing:">
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
          </FormItem>
          <h3>Per-Predictor Configurations</h3>
          <br />
          <Collapse defaultActiveKey={['1']}>
            {selectedPredictors.map(predictor => {
              const { id, name } = predictor;
              const { convolution, temporalDerivative, orthogonalize } = predictorConfigs[id];
              return (
                <Panel header={name} key={id}>
                  <FormItem>
                    <span>Convolution: </span>
                    <Select
                      style={{ width: 120 }}
                      value={convolution}
                      onChange={(value) => this.updatePredictorConfig(id, 'convolution', value)}
                    >
                      {['Gamma', 'Alpha', 'Beta'].map(conv => <Option value={conv} key={conv}>{conv}</Option>)}
                    </Select>
                  </FormItem>
                  <Checkbox
                    checked={temporalDerivative}
                    onChange={() => this.updatePredictorConfig(id, 'temporalDerivative', !temporalDerivative)}
                  >{'Temporal Derivative'}
                  </Checkbox>
                  <Checkbox
                    checked={orthogonalize}
                    onChange={() => this.updatePredictorConfig(id, 'orthogonalize', !orthogonalize)}
                  >{'Orthogonalize'}
                  </Checkbox>
                </Panel>
              );
            }
            )}
          </Collapse>
        </Form>
      </div>
    );
  }
}