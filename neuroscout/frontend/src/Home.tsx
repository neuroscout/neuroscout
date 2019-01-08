/*
 Home component for the homepage
*/
import * as React from 'react';
import { Divider, Icon, Tabs, Row, Col, Button, Card } from 'antd';
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
    const listProps: AnalysisListProps = { ...this.props, publicList: loggedIn === false };
    return (

      <div>
        <br/>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
        <div>
         <img className="splashLogo" src="/static/Neuroscout_Simple_Wide.svg"/><br/>
         <div className="splashText">A platform for fast and flexible re-analysis of (naturalistic) fMRI studies</div>
         <br/><br/>
         <div className="splashButtonParent">
         <Button size="large" className="splashButton" type="primary" href="/browse">
            Browse public analyses
         </Button>
         </div>
         </div>

        </MainCol>
      </Row>
      <br/>
      <Divider />
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Re-use public data" bordered={false}>
      <img className="splashLogo" src="/static/browse.svg"/>
      <br/>
      Select from openly available naturalistic fMRI datasets,
      from sources such as <strong>OpenNeuro</strong> and <strong>DataLad</strong>.

      </Card>
      </Col>

      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Design your analysis" bordered={false}>
      <img className="splashLogo" src="/static/design.svg"/>
      <br/>
      Browse hundreds of features pre-extracted from
      stimuli using <strong>state-of-the-art machine learning</strong> services and algorithms, such as
      Google Cloud Vision, IBM Watson, and more.
      </Card>
      </Col>

      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Execute and share" bordered={false}>
      <img className="splashLogo" src="/static/share.svg"/>
      <br/>
      Portable BIDS pipelines enable execution with no configuration.

      Results are automatically uploaded to <strong>NeuroVault</strong> for easy sharing.
      </Card>
      </Col>
      </Row>
      <br/>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <MainCol>
      <div className="splashButtonParent">
      <Button size="large" className="splashButton" href="/faq">
         Learn more
      </Button>
      </div>

      </MainCol>
      </Row>

      <br/>
      <Divider />
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <Col xxl={{span: 9}} xl={{span: 9}} lg={{span: 9}} xs={{span: 10}} >
      <p className="footertext">
      Created by the Psychoinformatics Lab at the University of Texas at Austin.<br/>
      Supported by NIH award R01MH109682-03.<br/>
      Icons by Smashicons from www.flaticon.com
      </p>
      </Col>
      </Row>
     </div>
    );
  }
}

export default Home;
