import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import AnalysisList, { AnalysisListProps } from './AnalysisList';

const Browse = (props: AnalysisListProps) => {
  const listProps: AnalysisListProps = { ...props, publicList: true };
  return (
    <div>
      <Row type="flex" justify="center">
        <Col span={16}>
          <h2>{'Public Analyses'}</h2>
          <br />
        </Col>
      </Row>
      <AnalysisList {...listProps} />
    </div>
  );
};
export default Browse;