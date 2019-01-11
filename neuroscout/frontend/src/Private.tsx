import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import AnalysisList, { AnalysisListProps } from './AnalysisList';
import { MainCol } from './HelperComponents';

// Interface to browse private analyses
const Private = (props: AnalysisListProps) => {
  const listProps: AnalysisListProps = { ...props, publicList: false };
  return (
    <div>
      <Row type="flex" justify="center">
        <MainCol>
        <h3>
          {'Your saved analyses'}
        </h3>
          <br />
          <AnalysisList {...listProps} />
        </MainCol>
      </Row>
    </div>
  );
};

export default Private;
