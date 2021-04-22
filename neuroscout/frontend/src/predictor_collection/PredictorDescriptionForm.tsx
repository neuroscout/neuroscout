import * as React from 'react';
import { Form } from '@ant-design/compatible';
import '@ant-design/compatible/assets/index.css';
import { Input } from 'antd';

type PDFProps = {
  predictors: string[],
  descriptions: string[],
  updateDescription: (index, string) => void
};

export class PredictorDescriptionForm extends React.Component<PDFProps, {} > {
  render() {
    let formList = this.props.predictors.map((predictor, index) => (
        <Form.Item key={`PDF${index}`} label={`Description for predictor ${predictor}`}>
          <Input
            value={this.props.descriptions[index]}
            onChange={(e) => { this.props.updateDescription(index, e.target.value); }}
          />
        </Form.Item>
    ));

    return (
      <Form>
        {formList}
      </Form>
    );
  }
}
