import * as React from 'react';
import { Button, Card, Checkbox, Modal, Tag, Icon, Tooltip, Switch } from 'antd';
import { config } from './config';
import { displayError, jwtFetch, alphaSort, timeout } from './utils';
import { ApiAnalysis, Analysis } from './coretypes';

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

type PubAccessProps = {
  private: boolean | undefined,
  updateAnalysis: (value: Partial<Analysis>, unsavedChanges: boolean, save: boolean) => void
};
class PubAccess extends React.Component<PubAccessProps, {}> {
  render() {
    return (
      <Tooltip title="Should this analysis be private (only visible to you) or public?">
        <Switch
          checked={!this.props.private}
          checkedChildren="Public"
          unCheckedChildren="Private"
          onChange={checked => this.props.updateAnalysis({'private': !checked}, false, true)}
        />
      </Tooltip>
    );
  }
}

type submitProps = {
  status?: string,
  analysisId?: string,
  confirmSubmission: (build: boolean) => void,
  private: boolean,
  updateAnalysis?: (value: Partial<Analysis>) => void,
  userOwns?: boolean
};

export class Submit extends React.Component<submitProps, {tosAgree: boolean, validate: boolean}> {
  constructor(props) {
    super(props);

    this.state = {
      tosAgree: (this.props.status !== 'DRAFT'),
      validate: true
    };
  }

  onChange(e) {
    this.setState({tosAgree: e.target.checked});
  }

  validateChange(e) {
    let setState = this.setState.bind(this);
    if (!e.target.checked) {
      Modal.confirm({
        title: 'Disable validation of model?',
        content: `Disabling validation of the model will speed up bundle generation
          but can lead to unexpected errors at runtime. Use at your own risk!`,
        onOk() {
          setState({validate: e.target.checked});
        }
      });
    } else {
      this.setState({validate: e.target.checked});
    }
  }

  render() {
    let { analysisId, status } = this.props;
    if (status === undefined) {
      status = 'DRAFT';
    }
    let onChange = this.onChange.bind(this);
    let validateChange = this.validateChange.bind(this);
    return(
      <div>
        <h3>Terms for analysis generation:</h3>
        <ul>
          <li>I agree that once I submit my analysis, I will not be able to delete or edit it.</li>
          <li>I agree if I publish results stemming from this analysis,
          I must make public, and cite all relevant analyses.</li>
            {this.props.private &&
            <li>
              I understand that although my analysis is currently private, anyone with the analysis
              ID may view this analysis, and subsequent uploaded results.
            </li>
            }
            {!this.props.private &&
          <li>
              I understand that my analysis is currently public and will be searchable by other users.
          </li>
            }
        </ul>
        <Checkbox onChange={validateChange} checked={this.state.validate}>
          Validate analysis bundle contents
        </Checkbox>
        <br/>
        <Checkbox onChange={onChange} checked={this.state.tosAgree}>
          I have read and agree to Neuroscout's terms of service
        </Checkbox>
        <br/>
        <Button
          hidden={!this.props.analysisId}
          onClick={this.props.confirmSubmission.bind(this, this.state.validate)}
          type={'primary'}
          disabled={!this.state.tosAgree || status !== 'DRAFT'}
        >
          Generate
        </Button>
      </div>
    );
  }
}

export class StatusTab extends React.Component<submitProps, {compileTraceback: string}> {
  constructor(props) {
    super(props);
    this.state = {
      compileTraceback: '',
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
      <div className="statusHeader">
        {this.props.userOwns &&
          <>
          <PubAccess private={this.props.private} updateAnalysis={this.props.updateAnalysis!} />
          <span>{' '}</span>
          </>}
        <Status status={this.props.status} analysisId={this.props.analysisId} />
      </div>
      {(this.props.status === 'PASSED') &&
        <div>
          <h3>Analysis Passed</h3>
          <p>
            {this.props.userOwns && 'Congratulations!'} The analysis is finished compiling and is ready to be executed.
            Once you have installed neuroscout-cli you may run the analysis with the following command,
            replacing '/local/outputdirectory' with the directory on your local computer where results
            should be stored:
          </p>
          <pre>
            <code>
              docker run --rm -it -v /local/outputdirectory:/out
              neuroscout/neuroscout-cli run /out {this.props.analysisId}
            </code>
          </pre>
          <p>
            See the <a href="https://github.com/neuroscout/neuroscout-cli">neuroscout-cli documentation </a>
             for more information on how to install and run analyses.
          </p>
        </div>
      }
      {(this.props.status === 'DRAFT') &&
        <Submit
          status={this.props.status}
          analysisId={this.props.analysisId}
          confirmSubmission={this.props.confirmSubmission}
          private={this.props.private}
        />
      }
      {(this.props.status === 'FAILED') &&
        <div>
          <h3>Analysis Failed to Compile</h3>
          <p>
            Oh no! It looks like your analysis failed to compile.
            Please clone and edit your analysis to try again.
            If the issue remains, please file a
            <a href="https://github.com/neuroscout/neuroscout/issues"> bugreport</a>.
          </p>
          <Card title="Errors" key="errors">
            <pre>{this.state.compileTraceback}</pre>
          </Card>
        </div>
      }
      {(this.props.status === 'PENDING' || this.props.status === 'SUBMITTING') &&
        <div>
          <h3>Analysis Pending Generation</h3>
          <p>Analysis generation may take some time. This page will update when complete.</p>
        </div>
      }
      {this.props.children}
      </div>
    );
  }
}
