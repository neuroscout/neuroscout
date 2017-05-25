import * as React from 'react';
import { Tabs, Row, Col, Layout, Button } from 'antd';
const { Header, Footer, Content } = Layout;

export const Home = () => (
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
);