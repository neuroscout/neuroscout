/*
 Home component for the homepage
*/
import * as React from 'react';
import { Tabs, Row, Col, Button, Card } from 'antd';
import { displayError } from './utils';
import { MainCol, Space } from './HelperComponents';
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
        <MainCol>
          <Card title="">
            <p>Welcome to Neuroscout!</p>
          </Card>
          <br />
        </MainCol>
      </Row>
      {loggedIn &&
        <div>
          <Row type="flex" justify="center"style={{ background: '#fff', padding: 0 }}>
            <MainCol>
              {!!analyses &&
                analyses.length > 0 &&
                <div>
                  <br />
                  <h3>Your saved analyses</h3>
                  <br />
                  <AnalysisList {...listProps} />
                </div>}
            </MainCol>
          </Row>
        </div>}
      </div>
    );
  }
}

export default Home;
