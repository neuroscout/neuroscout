import * as React from 'react';
import { Button, Card, Checkbox, Tag, Icon } from 'antd';
import { config } from './config';
import { displayError, jwtFetch, alphaSort, timeout } from './utils';

const domainRoot = config.server_url;

export class Status extends React.Component<{status?: string, analysisId?: string}, {}> {
  render() {
    let { analysisId, status } = this.props;
    if (status === undefined) {
      status = 'DRAFT';
    }
    const color: string = {
      DRAFT: 'blue',
      PENDING: 'orange',
      FAILED: 'red',
      PASSED: 'green'
    }[status];

    let bundleLink;
    if (status === 'PASSED' && analysisId) {
      bundleLink = `${domainRoot}/analyses/${analysisId}_bundle.tar.gz`;
    }

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

export class DLLink extends React.Component<{status?: string, analysisId?: string}, {}> {
    render() {
      let { analysisId, status } = this.props;
      if (status === undefined) {
        status = 'DRAFT';
      }

      let bundleLink;
      if (status === 'PASSED' && analysisId) {
        bundleLink = `${domainRoot}/analyses/${analysisId}_bundle.tar.gz`;
      }

      return(
          <span>
            <a href={bundleLink}>Download</a>
          </span>
      );
    }
}

type submitProps = {status?: string, analysisId?: string, confirmSubmission: () => void};
export class Submit extends React.Component<submitProps, {tosAgree: boolean}> {
  constructor(props) {
    super(props);
    
    this.state = {
      tosAgree: (status !== 'DRAFT')
    };
  }

  onChange(e) {
    this.setState({tosAgree: e.target.checked});
  }

  render() {
    let { analysisId, status } = this.props;
    if (status === undefined) {
      status = 'DRAFT';
    }
    let onChange = this.onChange.bind(this);
    return(
      <div>
        <h3>Terms for analysis generation:</h3>
        <ul>
          <li>I agree that once I submit my analysis, I will not be able to delete or edit it.</li>
          <li>I agree to use the "clone" feature to create any forked versions of the current analysis</li>
          <li>
            If private: I understand that although my analysis is currently private, anyone with the analysis 
            ID may view this analysis, and subsequent uploaded results.
          </li>
          <li>
            If public: I understand that my analysis is currently public and will be searchable by other users.
          </li>
        </ul>
        <Checkbox onChange={onChange} checked={this.state.tosAgree}>
          I have read and agree to Neuroscout's terms of service.
        </Checkbox>
        <br/>
        <Button
          hidden={!this.props.analysisId}
          onClick={this.props.confirmSubmission}
          type={'primary'}
          disabled={!this.state.tosAgree || status !== 'DRAFT'}
        >
          Generate
        </Button>
      </div>
    );
  }
}

export class Results extends React.Component<submitProps, {compileTraceback: string}> {
  constructor(props) {
    super(props);
    this.state = {
      compileTraceback: ''
    };
    this.getTraceback();
  }

  getTraceback() {
      let id = this.props.analysisId;
      jwtFetch(`${domainRoot}/api/analyses/${id}/compile`)
      .then((res) => {
        if (res.compile_traceback) {
          this.setState({compileTraceback: res.compile_traceback});
        }
      });
  }

  componentWillReceiveProps(nextProps: submitProps) {
    if ((nextProps.status !== this.props.status) && (nextProps.status === 'FAILED')) {
      this.getTraceback();
    }
  }

  render() {
    return(
      <div>
      {(this.props.status === 'PASSED') && 
        <div>
          <h3>Analysis Passed</h3>
          <DLLink status={this.props.status} analysisId={this.props.analysisId}/>
        </div>
      }
      {(this.props.status === 'DRAFT') &&
        <Submit
          status={this.props.status}
          analysisId={this.props.analysisId}
          confirmSubmission={this.props.confirmSubmission}
        />
      }
      {(this.props.status === 'FAILED') &&
        <div>
          <h3>Analysis Failed to Compile</h3>
          <Card title="Errors" key="errors">
            <pre>{this.state.compileTraceback}</pre>
          </Card>
        </div>
      }
      </div>
    );
  }
}
