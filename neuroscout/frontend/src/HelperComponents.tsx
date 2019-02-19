import * as React from 'react';
import { Alert, Col } from 'antd';

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

export class DisplayErrorsInline extends React.Component<{errors: string[]}, {}> {
  render() {
    return (
      <>
        {this.props.errors.length > 0 &&
          <div>
            <Alert
              type="error"
              showIcon={true}
              closable={true}
              message={
                <ul>
                  {this.props.errors.map((x, i) =>
                    <li key={i}>
                      {x}
                    </li>
                  )}
                </ul>
              }
            />
            <br />
          </div>}
      </>
    );
  }
}
