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
                  href="/public"
                >
                  Browse public analyses
                </Button>{' '}
                <Button
                  size="large"
                  className="splashButton"
                  type="default"
                  href="/predictors"
                >
                  Browse predictors
                </Button>
                <Button
                  size="large"
                  className="splashButton"
                  type="default"
                  href="/datasets"
                >
                  Browse datasets
                </Button>
                <br />
                {this.props.loggedIn === false && (
                  <Button
                    size="large"
                    className="splashButton"
                    type="primary"
                    onClick={e => this.props.update({ openSignup: true })}
                  >
                    Sign up to create analyses!
                  </Button>
                )}
              </div>
            </div>
            <Divider />
          </MainCol>
        </Row>
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}
          >
            <div className="stat-container">
              <div className="stat-title">Active datasets</div>
              <div className="stat-value">13</div>
            </div>
          </Col>
          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}
          >
            <div className="stat-container">
              <div className="stat-title">Number of tasks</div>
              <div className="stat-value">40</div>
            </div>
          </Col>
        </Row>
        <br />
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <Col
            xxl={{ span: 5 }}
            xl={{ span: 6 }}
            lg={{ span: 7 }}
            xs={{ span: 8 }}
          >
            <Card
              title="Re-use public data"
              headStyle={titleStyle}
              bordered={false}
            >
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
            xs={{ span: 8 }}
          >
            <Card
              title="Design your analysis"
              headStyle={titleStyle}
              bordered={false}
            >
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
            xs={{ span: 8 }}
          >
            <Card
              title="Execute and share"
              headStyle={titleStyle}
              bordered={false}
            >
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
                href="https://neuroscout.github.io/neuroscout/"
              >
                <BookOutlined />
                Learn more
              </Button>
            </div>
          </MainCol>
        </Row>
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <Card
              title="Support provided by"
              headStyle={titleStyle}
              bordered={false}
            >
              <Row justify="center">
                <Col span={5}>
                  <img className="instLogo2" src="/static/utlogo.png" />
                </Col>
                <Col span={5} offset={3}>
                  <img className="instLogo2" src="/static/nihlogo.png" />
                </Col>
              </Row>
            </Card>
          </MainCol>
        </Row>
        <Row justify="center" style={{ background: '#fff', padding: 0 }}>
          <MainCol>
            <div className="footerText">
              <p>
                Supported by NIH award R01MH109682-03. Icons by Smashicons from
                www.flaticon.com
              </p>
            </div>
          </MainCol>
        </Row>
      </div>
    )
  }
}

export default Home
