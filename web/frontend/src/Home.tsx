import * as React from 'react';
import { Tabs, Row, Col, Layout, Button } from 'antd';
import {displayError} from './utils';

const { Header, Footer, Content } = Layout;

interface HomeProps {
  ensureLoggedIn: () => Promise<{}>;
}

export class Home extends React.Component<HomeProps, {}> {
  launchBuilder = (e: any) => {
    this.props.ensureLoggedIn()
      .then(() => document.location.href = '/builder')
      .catch(displayError);
  }

  render() {
    return (
      <Row type="flex" justify="center">
        <Col span={16}>
          <Button
            type="primary"
            onClick={this.launchBuilder}
          >Create New Analysis</Button>
          <Button
            type="primary"
          ><a href="/browse">Browse Public Analyses</a></Button>
        </Col>
      </Row>
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