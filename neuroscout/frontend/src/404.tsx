import * as React from 'react';
import { Divider, Row } from 'antd';
import { MainCol } from './HelperComponents';
import { createBrowserHistory } from 'history';

export default class NotFound extends React.Component<{}, {}> {

  render() {
    const history = createBrowserHistory();
    return (
      <Row type="flex" justify="center" style={{padding: 0 }}>
        <MainCol>
          <Divider>Not found</Divider>
          The requested URL {history.location.pathname} was not found.
          Go <a onClick={history.goBack}>back</a>?
        </MainCol>
      </Row>
    );
  }
}
