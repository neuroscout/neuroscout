import * as React from 'react';
import { Button, Tabs, Collapse, Card, Tooltip, Icon, Select, Spin } from 'antd';
import vegaEmbed from 'vega-embed';

import { config } from '../config';
import { jwtFetch, timeout } from '../utils';

import { Run } from '../coretypes';
const domainRoot = config.server_url;

const TabPane = Tabs.TabPane;
const Panel = Collapse.Panel;
const { Option } = Select;

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

class Plots extends React.Component<{plots: any[], corr_plots: any[], runTitles: string[]}, {}> {
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
          <TabPane tab={this.props.runTitles[i]} key={'' + i}>
            <Collapse bordered={false} defaultActiveKey={['dm']}>
             <Panel header="Design Matrix" key="dm">
              <VegaPlot spec={this.props.plots[i]}/>
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
  runs: Run[];
  postReports: boolean;
  defaultVisible: boolean;
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
  runTitles: string[];
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
      selectedRunIds: ['' + this.props.runs[0].id],
      runTitles: [this.formatRun(this.props.runs[0])]
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
    jwtFetch(`${domainRoot}/api/analyses/${id}/report?run_id=${this.state.selectedRunIds}`)
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
        this.setState({reportsPosted: true});
      } else if (res.statusCode === 404 && !this.state.reportsPosted) {
        this.generateReport();
        this.setState({reportsPosted: true, reportsLoaded: false});
        return;
      } else {
        return;
      }
      
      state.reportsLoaded = true;
      this.setState({...state});
    });
  }

  updateSelectedRunIds = (values: string[]) => {
    let runTitles =  this.props.runs.filter(x => values.includes('' + x.id)).map(x => this.formatRun(x));
    this.setState({
      selectedRunIds: values,
      runTitles: runTitles
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

  componentDidUpdate(prevProps, prevState) {
    if (prevProps.postReports === false && this.props.postReports === true) {
      this.setState(
        {
          reportsLoaded: false,
          reportsPosted: false,
        },
      );
      this.checkReportStatus();
    }
    if (prevState.reportsLoaded === true && this.state.reportsLoaded === false) {
      this.checkReportStatus();
    }
  }

  updateReports = () => {
    this.setState(
      {
        reportsLoaded: false,
        reportsPosted: false
      }
    );
  }
 
  formatRun = (run: Run) => {
    let ret = '';
    if (!!run.number) {
      ret = ret.concat('Run - ', run.number, ' ');
    }
    if (!!run.session) {
      ret = ret.concat('Session - ', run.session, ' ');
    }
    if (!!run.subject) {
      ret = ret.concat('subject - ', run.subject, ' ');
    }
    if (ret === '') {
      ret = run.id;
    }
    return ret;
  }

  render() {
    const runIdsOptions: JSX.Element[] = [];
    this.props.runs.map(x => runIdsOptions.push(<Option key={'' + x.id}>{this.formatRun(x)}</Option>));
    const cardTitle = (
      <>
          Design Reports
      </>
    );
    const cardExtra = (
      <>
        <Tooltip
          title={'Here you can preview the final design and correlation matrices. \
          \nClick on the design matrix columns to view the timecourse in detail.'}
          defaultVisible={this.props.defaultVisible}
        >
          <Icon type="info-circle" style={{ fontSize: '15px'}}/>
        </Tooltip>
      </>
    );

    return (
      <div>
        <Card
         title={cardTitle}
         extra={cardExtra}
         key="plots"
        >
          <Spin spinning={!this.state.reportsLoaded}>
            <div className="plotRunSelectorContainer">
              <Select
                mode="multiple"
                onChange={this.updateSelectedRunIds}
                defaultValue={this.state.selectedRunIds}
                className="plotRunSelector"
              >
                {runIdsOptions}
              </Select>
              <Button
                onClick={this.updateReports}
                loading={!this.state.reportsLoaded}
                type="primary"
                className="plotRunSelectorBtn"
              >
                Get Reports
              </Button>
            </div>

            <Plots plots={this.state.plots} corr_plots={this.state.corr_plots} runTitles={this.state.runTitles}/>
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
