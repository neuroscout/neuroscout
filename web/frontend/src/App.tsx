import * as React from 'react';
import { Tabs, Row, Col, Layout, message } from 'antd';
import {
  BrowserRouter as Router,
  Route,
  Link
} from 'react-router-dom';

import './App.css';

import { Home } from './Home';
import { AnalysisBuilder } from './Builder';

const { Footer, Content, Header } = Layout;

const Browse = () => (
  <Row type="flex" justify="center">
    <Col span={16}>
      <h2>Browser Public Analyses</h2>
    </Col>
  </Row>
);

const App = () => (
  <Router>
    <div>
      <Layout>
        <Header style={{ background: '#fff', padding: 0 }}>
          <Row type="flex" justify="center">
            <Col span={16}>
              <h1><a href="/">Neuroscout</a></h1>
            </Col>
          </Row>
        </Header>
        <Content style={{ background: '#fff' }}>
          <Route exact path="/" component={Home} />
          <Route path="/builder" render={(props) => <AnalysisBuilder />} />
          <Route exact path="/browse" component={Browse} />
        </Content>
        <Footer style={{ background: '#fff'}}>
          <Row type="flex" justify="center">
            <Col span={4}>
              <br />
              <p>Neuroscout - Copyright 2017</p>
            </Col>
          </Row>
        </Footer>
      </Layout>
    </div>
  </Router >
);

const init = () => {
  window.localStorage.clear(); // Dev-only, will remove later once there is user/password prompt functionality
};

init();
export default App;
