import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import AnalysisList, { AnalysisListProps } from './AnalysisList';
import { MainCol } from './HelperComponents';

// Interface to browse public analyses
const Public = (props: AnalysisListProps) => {
  const listProps: AnalysisListProps = { ...props, publicList: true };
  return (
    <div>
      <Row type="flex" justify="center">
        <MainCol>
        <h3>
          {'Public analyses'}
        </h3>
          <br />
          <AnalysisList {...listProps} />
        </MainCol>
      </Row>
    </div>
  );
};

export default Public;
