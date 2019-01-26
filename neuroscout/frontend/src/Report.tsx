import * as React from 'react';
import { message, Button, Collapse, Card, Icon, Spin, Tag } from 'antd';
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
  Step,
  StepModel,
  BidsModel,
  ImageInput,
  TransformName
} from './coretypes';

import { displayError, jwtFetch, alphaSort, timeout } from './utils';

const domainRoot = config.server_url;

const Panel = Collapse.Panel;

let getSub = (x: string, pre: string) => {
  let subRe = new RegExp(`${pre}-([a-zA-Z0-9]+)`);
  let sub = '';
  let _sub = subRe.exec(x);
  if (_sub !== null) {
    sub = _sub[1];
  }
  return sub;
};

class Plots extends React.Component<{plots: string[]}, {}> {
    render() {
      let display: any[] = [];
      let plots = this.props.plots.map((x, i) => {
        let url = x;
        let sub = getSub(x, 'sub');
        let run = getSub(x, 'run');
        // urls generated for localhost have None instead of localhost in url
        if (x.indexOf('None') === 0) {
          url = x.slice(4);
          url = domainRoot + url;
        }
        display.push(
          <Panel header={<a href={url}>{`Subject ${sub} Run ${run}`}</a>} key={'' + i}>
            <img src={url} className="designMatrix"/>
          </Panel>
        );
      });
      return(
        <Collapse defaultActiveKey={['0']}>
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
        let sub = getSub(x, 'sub');
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
        <p>{this.props.reportTraceback}</p>
        <p>{this.props.compileTraceback}</p>
      </div>
      );
    }
}

interface ReportProps {
  analysisId?: string;
  runIds: string[];
  postReports: boolean;
}

interface ReportState {
  matrices: string[];
  plots: string[];
  reportTimestamp: string;
  reportTraceback: string;
  compileTraceback: string;
  reportsLoaded: boolean;
  reportsPosted: boolean;
  compileLoaded: boolean;
  status?: string;
  selectedRunIds: string[];
}

export class Report extends React.Component<ReportProps, ReportState> {
  constructor(props) {
    super(props);
    let state: ReportState = {
      matrices: [],
      plots: [],
      reportTimestamp: '',
      reportsLoaded: false,
      reportsPosted: false,
      compileLoaded: false,
      reportTraceback: '',
      compileTraceback: '',
      selectedRunIds: [this.props.runIds[0]]
    };
    this.state = state;
  }

  generateReport = (): void => {
    let id = this.props.analysisId;
    let url = `${domainRoot}/api/analyses/${id}/report?run_id=${this.state.selectedRunIds}`;
    jwtFetch(url, { method: 'POST' })
    .then((res) => {
    });
  };

  checkReportStatus = async () => {
    while (!this.state.reportsLoaded) {
      this.loadReports();
      await timeout(3000);
    }
  };

  loadReports = () => {
    let id = this.props.analysisId;

    // can't load anything without an ID
    if (id === undefined) {
      return;
    }
    if (this.state.reportsLoaded === true) {
      return;
    }
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
        } else {
          state.reportTraceback = '';
        }
      } else if (res.status === 'FAILED') {
        state.reportTraceback = res.traceback;
      } else if (res.statusCode === 404 && !this.state.reportsPosted) {
        this.generateReport();
        this.setState({reportsPosted: true});
        return;
      } else {
        return;
      }
      state.reportsLoaded = true;
      this.setState({...state});
    });
  }

  componentDidMount() {
    if (this.state.reportsLoaded === false) {
      this.checkReportStatus();
    }

    if (this.state.compileLoaded === false) {
      let id = this.props.analysisId;
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

  componentWillReceiveProps(nextProps: ReportProps) {
    if (nextProps.postReports) {
      this.setState(
        {
          reportsLoaded: false,
          reportsPosted: false,
        },
        () => this.checkReportStatus()
      );
    }
  }

  render() {
    return (
      <div>
        <Card title="Design Matrix" key="plots">
          <Spin spinning={!this.state.reportsLoaded}>
            <Plots plots={this.state.plots} />
          </Spin>
        </Card>
        <br/>
        {(this.state.reportTraceback || this.state.compileTraceback) &&
        <Card title="Errors" key="errors">
          <Tracebacks
            reportTraceback={this.state.reportTraceback}
            compileTraceback={this.state.compileTraceback}
          />
        </Card>}
      </div>
    );
  }
}
// <Status status={this.state.status} analysisId={this.props.analysisId} />
