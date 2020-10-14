/*
 Home component for the homepage
*/
import * as React from 'react';
import { Divider, Row, Col, Button, Card, Alert } from 'antd';
import { MainCol } from './HelperComponents';

const titleStyle: any = {
  textAlign: ('center' as React.CSSProperties),
  fontSize: '20px',
  padding: '0px 0px 0px 0px'
};

class Home extends React.Component<{}, {}> {
  render() {
    return (

      <div>
        <br/>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
        <div>
         <img className="splashLogo" src="/static/Neuroscout_Simple_Wide.svg"/><br/>
         <div className="splashText">A platform for fast and flexible re-analysis of (naturalistic) fMRI studies</div>
        <Alert
          message="Informational Notes"
          description="Our dataset host (TACC's Corral) is currently down for maintenance, and should be back shortly. "
          type="info"
          showIcon
        />
         <br/><br/>
         <div className="splashButtonParent">
         <Button size="large" className="splashButton" type="primary" href="/public">
            Browse public analyses
         </Button>
         </div>
         </div>
         <br/>
         <Divider />
        </MainCol>
      </Row>

      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Re-use public data" headStyle={titleStyle} bordered={false}>
      <img className="splashLogo" src="/static/browse.svg"/>
      <br/>
      Select from openly available naturalistic fMRI datasets,
      from sources such as
      <a href="https://openneuro.org/"> OpenNeuro</a> and <a href="https://datalad.org/">DataLad</a>.

      </Card>
      </Col>

      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Design your analysis" headStyle={titleStyle} bordered={false}>
      <img className="splashLogo" src="/static/design.svg"/>
      <br/>
      Browse hundreds of annotations automatically extracted from
      stimuli using <strong>state-of-the-art machine learning</strong> algorithms, such as
      Google Cloud Vision, IBM Watson, and more.
      </Card>
      </Col>

      <Col xxl={{span: 5}} xl={{span: 6}} lg={{span: 7}} xs={{span: 8}} >
      <Card title="Execute and share" headStyle={titleStyle} bordered={false}>
      <img className="splashLogo" src="/static/share.svg"/>
      <br/>
      Portable BIDS pipelines enable execution with no configuration.

      Results are automatically uploaded to
      <a href="https://neurovault.org/"> NeuroVault</a> for easy sharing.
      </Card>
      </Col>
      </Row>
      <br/>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <MainCol>
      <div className="splashButtonParent">
      <Button size="large" className="splashButton" href="https://neuroscout.github.io/neuroscout/">
         Learn more
      </Button>
      </div>

      <br/>
      <Divider />
      </MainCol>
      </Row>
      <Row type="flex" justify="center" style={{ background: '#fff', padding: 0 }}>
      <MainCol>
      <div className="footerText">
      <p>
      Created by the Psychoinformatics Lab at the University of Texas at Austin.
      Supported by NIH award R01MH109682-03.<br/>
      Icons by Smashicons from www.flaticon.com
      </p>
      </div>
      </MainCol>
      </Row>
     </div>
    );
  }
}

export default Home;
