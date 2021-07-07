/*
 Home component for the homepage
*/
import * as React from 'react'
import { Divider, Row, Col, Button, Card } from 'antd'
import { MainCol } from './HelperComponents'
import { UserStore } from './user'
import { BookOutlined } from '@ant-design/icons'

const titleStyle: any = {
  textAlign: 'center' as React.CSSProperties,
  fontSize: '22px',
  padding: '0px 0px 0px 0px',
}

class Home extends React.Component<UserStore, Record<string, never>> {
  render() {
    return (
      <div>
        <br />
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <div>
              <img
                className="splashLogo"
                src="/static/Neuroscout_Simple_Wide.svg"
              />
              <br />
              <div className="splashText">
                A platform for fast and flexible re-analysis of (naturalistic)
                fMRI studies
              </div>
              <br />
              <br />
              <div className="splashButtonParent">
                <Button
                  size="large"
                  className="splashButton"
                  type="default"
                  href="/public">
                  Browse public analyses
                </Button>{' '}
                {this.props.loggedIn === false && (
                  <Button
                    size="large"
                    className="splashButton"
                    type="primary"
                    onClick={e => this.props.update({ openSignup: true })}>
                    Sign up to get started!
                  </Button>
                )}
              </div>
            </div>
            <br />
            <Divider />
          </MainCol>
        </Row>

        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}>
            <Card
              title="Re-use public data"
              headStyle={titleStyle}
              bordered={false}>
              <img className="splashLogo" src="/static/browse.svg" />
              <br />
              <div className="introCardsText">
                Select from openly available naturalistic fMRI datasets, from
                sources such as
                <a href="https://openneuro.org/"> OpenNeuro</a> and{' '}
                <a href="https://datalad.org/">DataLad</a>.
              </div>
            </Card>
          </Col>

          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}>
            <Card
              title="Design your analysis"
              headStyle={titleStyle}
              bordered={false}>
              <img className="splashLogo" src="/static/design.svg" />
              <br />
              <div className="introCardsText">
                Browse hundreds of annotations automatically extracted from
                stimuli using <strong>state-of-the-art machine learning</strong>{' '}
                platforms, such as Google Cloud Vision, TensorFlow and more.
              </div>
            </Card>
          </Col>

          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}>
            <Card
              title="Execute and share"
              headStyle={titleStyle}
              bordered={false}>
              <img className="splashLogo" src="/static/share.svg" />
              <br />
              <div className="introCardsText">
                Portable BIDS pipelines enable{' '}
                <strong>execution with no configuration</strong>. Results are
                automatically uploaded to
                <a href="https://neurovault.org/"> NeuroVault</a> for easy
                sharing.
              </div>
            </Card>
          </Col>
        </Row>
        <br />
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <div className="splashButtonParent">
              <Button
                size="large"
                className="splashButton"
                href="https://neuroscout.github.io/neuroscout/">
                <BookOutlined />
                Learn more
              </Button>
            </div>

            <br />
            <Divider />
          </MainCol>
        </Row>
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <div className="footerText">
              <p>
                Created by the Psychoinformatics Lab at the University of Texas
                at Austin. Supported by NIH award R01MH109682-03.
                <br />
                Icons by Smashicons from www.flaticon.com
              </p>
            </div>
          </MainCol>
        </Row>
      </div>
    )
  }
}

export default Home
