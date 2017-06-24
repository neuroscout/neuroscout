import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import { displayError, Space } from './utils';
import { AppAnalysis } from './commontypes';
import { Link } from 'react-router-dom';

const { Header, Footer, Content } = Layout;

interface HomeProps {
  analyses?: AppAnalysis[];
  cloneAnalysis: (id: string) => void;
  // loginAndNavigate: (string) => void;
  // ensureLoggedIn: () => Promise<{}>;
}

export class Home extends React.Component<HomeProps, {}> {
  render() {
    const { analyses, cloneAnalysis } = this.props;
    return (
      <div>
        <Row type="flex" justify="center">
          <Col span={16}>
            <Card title="">
              <p>Marketing copy explaining Neuroscout...</p>
            </Card>
            <br />
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col span={2} />
          <Col span={4}>
            <Button type="primary" size="large"><Link to="/builder">Create New Analysis</Link></Button>
          </Col>
          <Col span={4}>
            <Button type="primary" size="large"><Link to="/browse">Browse Public Analyses</Link></Button>
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col span={16}>
            {analyses !== undefined && <div><br /><h2>Your saved analyses:</h2><br /></div>}
            {analyses!.map(analysis => (
              <div key={analysis.id} title={analysis.name}>
                <Row>
                  <Col span={8}>
                    <Link to={`/builder/${analysis.id}`}><h4>{analysis.name}</h4></Link>
                    <p>Status: {analysis.status}</p>
                    <p>{analysis.description}</p>
                  </Col>
                  <Col span={6}>
                    <Button
                      type="primary"
                      ghost={true}
                      onClick={() => cloneAnalysis(analysis.id)}
                    >Clone</Button>
                    <Space />
                    <Button
                      type="danger"
                      ghost={true}
                      onClick={() => displayError(Error('Not implemented'))}
                    >Delete</Button>
                  </Col>
                </Row>
                <br />
              </div>
            ))}
          </Col>
        </Row>
      </div>
    );
  }
}

/*export const Home = (props: HomeProps) => (
  <Row type="flex" justify="center">
    <Col span={16}>
      <Button
        type="primary"
        onClick={(ev) => { document.location.href = '/builder' }}
      >Create New Analysis</Button>
      <Button
        type="primary"
      ><a href="/browse">Browse Public Analyses</a></Button>
    </Col>
  </Row>
);*/