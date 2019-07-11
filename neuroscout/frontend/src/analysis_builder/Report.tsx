import * as React from 'react';
import { Tabs, Collapse, Card, Tooltip, Icon, Spin } from 'antd';
import vegaEmbed from 'vega-embed';

import { config } from '../config';
import { jwtFetch, timeout } from '../utils';

const domainRoot = config.server_url;

const TabPane = Tabs.TabPane;
const Panel = Collapse.Panel;

class VegaPlot extends React.Component<{spec: string}, {}> {
  vegaContainer;

  constructor(props) {
    super(props);
    this.vegaContainer = React.createRef();
  }

  componentDidMount() {
      vegaEmbed(this.vegaContainer.current, this.props.spec, { renderer: 'svg' });
  }

  render () {
    return(
      <div ref={this.vegaContainer}/>
    );
  }

}

class Plots extends React.Component<{plots: any[], corr_plots: any[]}, {}> {
    plotContainer;
    constructor(props) {
      super(props);
      this.plotContainer = React.createRef();
    }

    render() {
      let display: any[] = [];
      this.props.plots.map((x, i) => {
        let spec = x;
        display.push(
          <TabPane tab="First run" key={'' + i}>
            <Collapse bordered={false} defaultActiveKey={['dm']}>
             <Panel header="Design Matrix" key="dm">
              <VegaPlot spec={spec}/>
             </Panel>
             <Panel header="Correlation Matrix" key="cm">
              <VegaPlot spec={this.props.corr_plots[i]}/>
             </Panel>
            </Collapse>
          </TabPane>
        );
      });
      return(
        <Tabs  type="card">
          {display}
        </Tabs>

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
  corr_plots: string[];
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
      corr_plots: [],
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
        state.corr_plots = res.result.design_matrix_corrplot;
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
        if (res.traceback) {
          state.compileTraceback = res.traceback;
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
        <Card
         title="Design Report"
         extra={
           <Tooltip
            title={'Here you can preview the final design and correlation matrices. \
            \nClick on the design matrix columns to view the timecourse in detail.'}
            defaultVisible={true}
           >
             <Icon type="info-circle" style={{ fontSize: '15px'}}/>
           </Tooltip>
           }
         key="plots"
        >
          <Spin spinning={!this.state.reportsLoaded}>
            <Plots plots={this.state.plots} corr_plots={this.state.corr_plots} />
          </Spin>
        </Card>
        <br/>
        {(this.state.reportTraceback || this.state.compileTraceback) &&
        <div>
        <Card title="Errors" key="errors">
          <Tracebacks
            reportTraceback={this.state.reportTraceback}
            compileTraceback={this.state.compileTraceback}
          />
        </Card><br/></div>}
      </div>
    );
  }
}
// <Status status={this.state.status} analysisId={this.props.analysisId} />
