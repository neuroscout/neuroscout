import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import AnalysisList, { AnalysisListProps } from './AnalysisList';

// Interface to browse public analyses
const Browse = (props: AnalysisListProps) => {
  const listProps: AnalysisListProps = { ...props, publicList: true };
  return (
    <div>
      <Row type="flex" justify="center">
        <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
          <br />
          <AnalysisList {...listProps} />
        </Col>
      </Row>
    </div>
  );
};
export default Browse;
