import * as React from 'react';
import { LockOutlined, UnlockOutlined } from '@ant-design/icons';
import { Alert, Col, Divider, Row, Tag, Tooltip } from 'antd';
import { createBrowserHistory } from 'history';

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

// Make status strings pretty and color coded
export class StatusTag extends React.Component<{status?: string, analysisId?: string}, {}> {
  render() {
    let { status } = this.props;
    if (status === undefined) {
      status = 'DRAFT';
    }
    const color: string = {
      DRAFT: 'blue',
      PENDING: 'orange',
      FAILED: 'red',
      PASSED: 'green'
    }[status];

    return (
      <span>
        <Tag color={color}>
          {status === 'DRAFT' ? <UnlockOutlined /> : <LockOutlined />}
          {' ' + status}
        </Tag>
      </span>
    );
  }
}

export class NotFound extends React.Component<{}, {}> {
  render() {
    const history = createBrowserHistory();
    return (
      <Row justify="center" style={{padding: 0 }}>
        <MainCol>
          <Divider>Not found</Divider>
          The requested URL {history.location.pathname} was not found.
          Go <a onClick={history.goBack}>back</a>?
        </MainCol>
      </Row>
    );
  }
}

export const datasetColumns = [
  {
    title: 'Name',
    dataIndex: 'name',
    width: 130,
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  { title: 'Summary', dataIndex: 'summary'},
  { title: 'Modality', dataIndex: 'modality', width: 130, sorter: (a, b) => a.name.localeCompare(b.name)},
  { title: 'Author(s)', dataIndex: 'authors', width: 200,
    render: (text) => {
      if (text.length > 1) {
        return (<Tooltip title={text.join(', ')}>{text[0]}, et al.</Tooltip>);
      } else {
        return (<>{text[0]}</>);
      }
    }
  }
];

export function DateTag(props) {
    let date = [''];
    if (!!props.modified_at) {
      date = props.modified_at.split('-');
    }
    return (
      <>{!!date[0] && date.length === 3 &&
          <Tag>last modified <Space />{date[2].slice(0, 2)}-{date[1]}-{date[0].slice(2, 4)}</Tag>
        }</>
    );
}
