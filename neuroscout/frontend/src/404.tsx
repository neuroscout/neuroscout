import * as React from 'react';
import { Divider, Row } from 'antd';
import { MainCol } from './HelperComponents';

export default class NotFound extends React.Component<{}, {}> {

  render() {
    return (
      <Row type="flex" justify="center" style={{padding: 0 }}>
        <MainCol>
          <Divider>Page not found</Divider>
        </MainCol>
      </Row>
    );
  }
}
