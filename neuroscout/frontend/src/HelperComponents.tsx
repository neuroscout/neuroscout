import * as React from 'react';
import { Col } from 'antd';

// Simple space component to seperate buttons, etc.
// tslint:disable-next-line:jsx-self-close
export const Space = (props: {}) => <span> </span>;

export class MainCol extends React.Component<{}, {}> {
  render() {
    return (
      <Col xxl={{span: 16}} xl={{span: 18}} lg={{span: 20}} xs={{span: 24}} className="mainCol">
        {this.props.children}
      </Col>
    );
  }
}
