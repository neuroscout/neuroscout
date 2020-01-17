import * as React from 'react';
import { Alert, Col, Divider, Icon, Row, Tag, Tooltip } from 'antd';
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

    return(
      <span>
        <Tag color={color}>
          {status === 'DRAFT' ? <Icon type="unlock" /> : <Icon type="lock" />}
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

export const datasetColumns = [
  {
    title: 'Name',
    dataIndex: 'name',
    width: 130,
    sorter: (a, b) => a.name.localeCompare(b.name),
  },
  { title: 'Modality', dataIndex: 'modality' },
  { title: 'Description', dataIndex: 'description'},
  { title: 'Author(s)', dataIndex: 'authors', width: 280,
    render: (text) => {
      if (text.length > 1) {
        return (<Tooltip title={text.join(', ')}>{text[0]} ... {text[1]}</Tooltip>);
      } else {
        return (<>{text[0]}</>);
      }
    }
  }
];
