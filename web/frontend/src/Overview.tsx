import * as React from 'react';
import { Form, Input, AutoComplete } from 'antd'
const FormItem = Form.Item;

export interface Analysis {
  analysisId: number | null;
  analysisName: string;
  analysisDescription: string;
  datasetId: number | null;
  predictions: string;
}

export interface Dataset {
  name: string;
  value: number;
}

interface OverviewTabProps {
  analysis: Analysis;
  datasets: Dataset[];
  updateAnalysis: (value: any) => void;
}

export class OverviewTab extends React.Component<OverviewTabProps, any>{
  updateAnalysis = (attrName: string) => (event) => {
    let newAnalysis = { ...this.props.analysis };
    newAnalysis[attrName] = event.target.value;
    this.props.updateAnalysis(newAnalysis)
  }

  render() {
    const { analysis, datasets } = this.props;
    return <div>
      <p>Analysis Overview</p>
      <Form layout='vertical'>
        <FormItem label="Analysis name:">
          <Input placeholder="Analysis name"
            value={analysis.analysisName}
            onChange={this.updateAnalysis('analysisName')}
          />
        </FormItem>
        <FormItem label="Description:">
          <Input placeholder="Description of your analysis"
            value={analysis.analysisDescription}
            onChange={this.updateAnalysis('analysisDescription')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>
        <FormItem label="Predictions:">
          <Input placeholder="Enter your preditions about what you expect the results to look like"
            value={analysis.predictions}
            onChange={this.updateAnalysis('predictions')}
            type="textarea"
            autosize={{ minRows: 3, maxRows: 20 }}
          />
        </FormItem>

        <FormItem label="Dataset">
          <AutoComplete
            dataSource={datasets.map(item =>
              ({ value: item.value.toString(), text: item.name }))}
            placeholder="Type dataset name to search"  
          />
        </FormItem>
        {/*<FormItem label="Dataset">
          <Select
            mode="tags"
          >
          {this.props.datasets.map((dataset) => 
            <Option key={dataset.value}>{dataset.name}</Option>
          )}
          </Select>
        </FormItem>*/}
      </Form>
    </div>
  }
}