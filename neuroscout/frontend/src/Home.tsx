/*
 Home component for the homepage
*/
import * as React from 'react';
import { Tabs, Row, Col, Button, Card } from 'antd';
import { displayError } from './utils';
import { Space } from './HelperComponents';
import { AppAnalysis } from './coretypes';
import { Link } from 'react-router-dom';
import AnalysisList, { AnalysisListProps } from './AnalysisList';

interface HomeProps extends AnalysisListProps {
  loggedIn: boolean;
}

class Home extends React.Component<HomeProps, {}> {
  render() {
    const { analyses, cloneAnalysis, onDelete, loggedIn, publicList } = this.props;
    const listProps: AnalysisListProps = { ...this.props, publicList: false };
    return (
      <div>

      <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
        <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
          <Card title="">
            <p>Welcome to Neuroscout!</p>
          </Card>
          <br />
        </Col>
      </Row>
      {loggedIn &&
        <div>
          <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
            <Col xxl={{span: 14}} xl={{span: 16}} lg={{span: 18}} xs={{span: 24}} className="mainCol">
              {!!analyses &&
                analyses.length > 0 &&
                <div>
                  <br />
                  <h2>Your saved analyses:</h2>
                  <br />
                  <AnalysisList {...listProps} />
                </div>}
            </Col>
          </Row>
        </div>}
      </div>
    );
  }
}

export default Home;
