import * as React from 'react';
import { Tabs, Row, Col, Button, Card, Tag, Icon, message } from 'antd';
import { displayError } from './utils';
import { Space } from './HelperComponents';
import { AppAnalysis } from './coretypes';
import Status from './Status';
import { Link } from 'react-router-dom';

export interface AnalysisListProps {
  loggedIn?: boolean;
  publicList?: boolean;
  analyses: AppAnalysis[];
  cloneAnalysis: (id: string) => void;
  onDelete?: (analysis: AppAnalysis) => void;
}

const AnalysisList = (props: AnalysisListProps) => {
  const { analyses, publicList, cloneAnalysis, onDelete } = props;
  return (
    <Row type="flex" justify="center">
      <Col span={18}>
        {analyses!.map(analysis =>
          <div key={analysis.id}>
            <Card title={analysis.name} extra={<Status status={analysis.status} />}>
              <Row>
                <Col span={18}>
                  <p>
                    <strong>Description: </strong>
                    {analysis.description || 'N/A'}
                  </p>
                  <p>
                    <strong>Last modified: </strong>
                    {analysis.modifiedAt}
                  </p>
                  <br />
                </Col>
              </Row>
              <Row>
                <Col span={18}>
                  <Button
                    type="primary"
                    ghost={true}
                    onClick={() =>
                      message.warning(
                        'Analysis viewer not implemented yet. Try the Edit button to open analysis in Builder'
                      )}
                  >
                    View
                  </Button>
                  <Space />
                  {!publicList &&
                    <Button type="primary" ghost={true}>
                      <Link to={`/builder/${analysis.id}`}>Edit</Link>
                    </Button>}
                  <Space />
                  <Button type="primary" ghost={true} onClick={() => cloneAnalysis(analysis.id)}>
                    Clone
                  </Button>
                  <Space />
                  {analysis.status === 'DRAFT' &&
                    !publicList &&
                    <Button type="danger" ghost={true} onClick={() => onDelete!(analysis)}>
                      Delete
                    </Button>}
                </Col>
              </Row>
            </Card>
            <br />
          </div>
        )}
      </Col>
    </Row>
  );
};

export default AnalysisList;
