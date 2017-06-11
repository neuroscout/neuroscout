import * as React from 'react';
import { Tabs, Row, Col, Layout, Button, Card } from 'antd';
import { displayError } from './utils';
import { Link } from 'react-router-dom';

const { Header, Footer, Content } = Layout;

interface HomeProps {
  analyses?: { id: string, name: string }[];
  // loginAndNavigate: (string) => void;
  // ensureLoggedIn: () => Promise<{}>;
}

export class Home extends React.Component<HomeProps, {}> {
  render() {
    const { analyses } = this.props;
    return (
      <div>
        <Row type="flex" justify="center">
          <Col span={16}>
            <Card title="">
              <p>Marketing copy explaining Neuroscount...</p>
            </Card>
            <br />
            {/*<Button type="primary"><Link to="/builder">Create New Analysis</Link></Button>
            <Button type="primary"><Link to="/browse">Browse Public Analyses</Link></Button>*/}
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col span={2}>
          </Col>
          <Col span={4}>
            <Button type="primary"><Link to="/builder">Create New Analysis</Link></Button>
          </Col>
          <Col span={4}>
            <Button type="primary"><Link to="/browse">Browse Public Analyses</Link></Button>
          </Col>
        </Row>
        <Row type="flex" justify="center">
          <Col span={12}>
          {analyses!.map(analysis => (
            <div>
              <Link to={`/builder/${analysis.id}`}>{ analysis.name}</Link><br/>
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