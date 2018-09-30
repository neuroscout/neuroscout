import * as React from 'react';
import { message, Button, Collapse, Card, Icon, Tag } from 'antd';
import { config } from './config';

import {
  Store,
  Analysis,
  Dataset,
  Task,
  Run,
  Predictor,
  ApiDataset,
  ApiAnalysis,
  AnalysisConfig,
  Transformation,
  Contrast,
  Block,
  BlockModel,
  BidsModel,
  ImageInput,
  TransformName
} from './coretypes';

import { displayError, jwtFetch, alphaSort } from './utils';

const domainRoot = config.server_url;

const Panel = Collapse.Panel;

class Status extends React.Component<{status?: string, analysisId?: string}, {}> {

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
        <div>
          <span>
            <Tag color={color}>
              {status === 'DRAFT' ? <Icon type="unlock" /> : <Icon type="lock" />}
              {' ' + status}
            </Tag>
          </span>
          <br/>
          <span>
            <a href={bundleLink}>Download</a>
          </span>
        </div>
      );
    }
}

let getSub = (x: string) => {
  let subRe = /sub-([a-zA-Z0-9]+)/;
  let sub = '';
  let _sub = subRe.exec(x);
  if (_sub !== null) {
    sub = _sub[0];
  }
  return sub;

};

class Plots extends React.Component<{plots: string[]}, {}> {
    render() {
      let display: any[] = [];
      let plots = this.props.plots.map((x) => {
        let url = x;
        let sub = getSub(x);
        if (x.indexOf('None') === 0) {
          url = x.slice(4);
        }
        url = domainRoot + url;
        display.push(<Panel header={sub} key={url}><img src={url}/></Panel>);
      });
      return(
        <Collapse>
          {display}
        </Collapse>
      );
    }
}

class Matrices extends React.Component<{matrices: string[]}, {}> {
    render() {
      let display: any[] = [];
      let matrices = this.props.matrices.map((x) => {
        let url = x;
        let sub = getSub(x);
        if (x.indexOf('None') === 0) {
          url = x.slice(4);
        }
        url = domainRoot + url;
        display.push(<li key={url}>{sub}: <a href={url}>{url}</a><br/></li>);
      });
      return(
        <ul>{display}</ul>
      );
    }
}

class Tracebacks extends React.Component<{reportTraceback: string, compileTraceback: string}, {}> {
    render() {
      return(
      <div>
        {this.props.reportTraceback}<br />
        {this.props.compileTraceback}
      </div>
      );
    }
}

interface ReportProps {
  analysisId?: string;
}

interface ReportState {
  matrices: string[];
  plots: string[]; 
  reportTimestamp: string;
  reportTraceback: string;
  compileTraceback: string;
  reportsLoaded: boolean;
  compileLoaded: boolean;
  status?: string;
}

export class Report extends React.Component<ReportProps, ReportState> {
  constructor(props) {
    super(props);
    let state: ReportState = {
      matrices: [],
      plots: [],
      reportTimestamp: '', 
      reportsLoaded: false,
      compileLoaded: false,
      reportTraceback: '',
      compileTraceback: ''
    };
    this.state = state;
  }

  componentDidMount() {
    let id = this.props.analysisId;
    if (this.state.reportsLoaded === false) {
      let state = {...this.state};
      jwtFetch(`${domainRoot}/api/analyses/${id}/report`)
      .then((res) => {
        if (res.status === 'OK') {
          if (res.result === undefined) {
            return;
          }
          state.matrices = res.result.design_matrix;
          state.plots = res.result.design_matrix_plot;
          state.reportTimestamp = res.generated_at;
          if (res.traceback) {
            state.reportTraceback = res.traceback;
          } 
        } else if (res.status === 'FAILED') {
          state.reportTraceback = res.traceback;
        } else {
          return;
        }
        state.reportsLoaded = true;
        this.setState({...state});
      });
    }
    if (this.state.compileLoaded === false) {
      let state = {...this.state};
      jwtFetch(`${domainRoot}/api/analyses/${id}/compile`)
      .then((res) => {
        state.status = res.status;
        state.compileLoaded = true;
        if (res.compile_traceback) {
          state.compileTraceback = res.compile_traceback;
        }
          
        this.setState({...state});
      });
    }
  }

  render() {
    return (
      <Card>
        <Status status={this.state.status} analysisId={this.props.analysisId} />
        <Collapse>
        <Panel header="Matrix Design Plots" key="plots"><Plots plots={this.state.plots} /></Panel>
        <Panel header="Matrix Design Downloads" key="matrices"><Matrices matrices={this.state.matrices} /></Panel>
        </Collapse>
        <br/>
        {(this.state.reportTraceback || this.state.compileTraceback) &&
        <Card title="Errors" key="errors">
          <Tracebacks
            reportTraceback={this.state.reportTraceback}
            compileTraceback={this.state.compileTraceback}
          />
      </Card>}
      </Card>
    );
  }
}
