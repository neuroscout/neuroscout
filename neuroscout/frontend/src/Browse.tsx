import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import AnalysisList, { AnalysisListProps } from './AnalysisList';

// Interface to browse public analyses
const Browse = (props: AnalysisListProps) => {
  const listProps: AnalysisListProps = { ...props, publicList: true };
  return (
    <div>
      <Row type="flex" justify="center">
        <Col span={18}>
          <h2>
            {'Public Analyses'}
          </h2>
          <br />
          <AnalysisList {...listProps} />
        </Col>
      </Row>
    </div>
  );
};
export default Browse;
