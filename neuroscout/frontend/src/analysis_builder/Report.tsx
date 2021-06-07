import * as React from 'react'
import { QuestionCircleTwoTone } from '@ant-design/icons'
import {
  Alert,
  Button,
  Tabs,
  Collapse,
  Card,
  Tooltip,
  Select,
  Spin,
  Switch,
  Popconfirm,
  Tag,
} from 'antd'
import { VegaEmbed } from 'react-vega'

import { OptionProps } from 'antd/lib/select'

import { config } from '../config'
import { jwtFetch, timeout } from '../utils'
import { DateTag, Space } from '../HelperComponents'

import { Run, TabName } from '../coretypes'
const domainRoot = config.server_url

const TabPane = Tabs.TabPane
const Panel = Collapse.Panel
const { Option } = Select

/*
class VegaPlot extends React.Component<{spec: string}, Record<string, never>> {
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
*/

class Warnings extends React.Component<{ warnings: string[] }> {
  render() {
    const alerts: any[] = []
    this.props.warnings.map((x, i) => {
      alerts.push(
        <Alert message="Warning" description={x} type="warning" showIcon />,
      )
    })
    return (
      <div>
        <br />
        {alerts}
      </div>
    )
  }
}

interface PlotsProps {
  matrices: string[]
  plots: any[]
  corr_plots: any[]
  runTitles: string[]
  scale?: boolean
  updateScale: () => void
}

class Plots extends React.Component<PlotsProps, Record<string, never>> {
  plotContainer
  constructor(props) {
    super(props)
    this.plotContainer = React.createRef()
  }

  render() {
    const display: any[] = []
    this.props.plots.map((x, i) => {
      const spec = x
      display.push(
        <TabPane tab={this.props.runTitles[i]} key={String(i)}>
          <Collapse bordered defaultActiveKey={['dm']}>
            <Panel header="Design Matrix" key="dm">
              <div style={{ float: 'right' }}>
                <Tooltip
                  title={
                    'Scale variables in the design matrix plot (only for visual purposes)'
                  }>
                  Scale Design Matrix <QuestionCircleTwoTone />
                  <Space />
                  <Switch
                    onChange={this.props.updateScale}
                    checked={this.props.scale}
                  />
                </Tooltip>
              </div>
              <VegaEmbed spec={this.props.plots[i]} />
              <br />
              <a href={this.props.matrices[i]}>Download Design Matrix</a>
            </Panel>
            <Panel header="Correlation Matrix" key="cm">
              <VegaEmbed spec={this.props.plots[i]} />
            </Panel>
          </Collapse>
        </TabPane>,
      )
    })
    return <Tabs type="card">{display}</Tabs>
  }
}

export class Tracebacks extends React.Component<{
  traceback: string
  message: string
}> {
  render() {
    const display: any[] = []
    if (this.props.traceback) {
      display.push(
        <Alert
          message={this.props.message}
          description={
            <div>
              <p>{this.props.traceback}</p>
              If you don&apos;t know what this error means, feel free to ask on{' '}
              <a href="https://neurostars.org/">NeuroStars</a>.<br />
              If you believe this is a bug, please open an issue on open an
              <a href="https://github.com/neuroscout/neuroscout/issues">
                {' '}
                issue on GitHub
              </a>
              .
            </div>
          }
          type="error"
          showIcon
        />,
      )
    }
    return <div>{display}</div>
  }
}

interface ReportProps {
  analysisId?: string
  modified_at?: string
  runs: Run[]
  postReports: boolean
  defaultVisible: boolean
  activeTab: TabName
}

interface ReportState {
  compileLoaded: boolean
  corr_plots: string[]
  matrices: string[]
  plots: string[]
  reportTimestamp: string
  reportTraceback: string
  reportsLoaded: boolean
  reportsPosted: boolean
  runTitles: string[]
  scale?: boolean
  selectedRunIds: string[]
  status?: string
  warnings: string[]
  warnVisible: boolean
}

export class Report extends React.Component<ReportProps, ReportState> {
  constructor(props) {
    super(props)
    this._timer = null
    const state: ReportState = {
      matrices: [],
      plots: [],
      corr_plots: [],
      warnings: [],
      reportTimestamp: '',
      reportsLoaded: false,
      reportsPosted: false,
      compileLoaded: false,
      reportTraceback: '',
      selectedRunIds: [String(this.props.runs[0].id)],
      runTitles: [this.formatRun(this.props.runs[0])],
      warnVisible: false,
    }
    this.state = state
  }

  _timer: any = null

  generateReport = (scale?: boolean): void => {
    const id = this.props.analysisId
    let scale_param = ''
    if (scale === undefined) {
      scale_param =
        this.state.scale === undefined
          ? ''
          : `&scale=${String(this.state.scale)}`
    } else {
      scale_param = `&scale=${String(scale)}`
    }
    const url = `${domainRoot}/api/analyses/${String(
      id,
    )}/report?run_id=${String(this.state.selectedRunIds)}${scale_param}`
    void jwtFetch(url, { method: 'POST' }).then(res => {
      // Not sure what we want to do on failure here.
    })
  }

  checkReportStatus = () => {
    if (this._timer === null) {
      this._timer = setInterval(() => {
        if (this.state.reportsLoaded) {
          clearInterval(this._timer)
          this._timer = null
        } else {
          this.loadReports()
        }
      }, 4000)
    }
  }

  loadReports = () => {
    const id = this.props.analysisId

    // can't load anything without an ID
    if (id === undefined) {
      return
    }
    if (this.state.reportsLoaded === true) {
      return
    }

    const state = { ...this.state }
    void jwtFetch(
      `${domainRoot}/api/analyses/${id}/report?run_id=${String(
        this.state.selectedRunIds,
      )}`,
    ).then(res => {
      if (res.warnings) {
        state.warnings = res.warnings
      } else {
        state.warnings = []
      }

      if (res.status === 'OK') {
        if (res.result === undefined) {
          return
        }
        let scale = false
        if (this.state.scale !== undefined) {
          scale = this.state.scale
        } else if (res.scale !== null) {
          scale = res.scale
        }
        state.scale = scale

        state.matrices = res.result.design_matrix
        state.plots = res.result.design_matrix_plot
        state.corr_plots = res.result.design_matrix_corrplot
        state.reportTimestamp = res.generated_at
        if (res.traceback) {
          state.reportTraceback = res.traceback
        } else {
          state.reportTraceback = ''
        }
      } else if (res.status === 'FAILED') {
        state.reportTraceback = res.traceback
        this.setState({ reportsPosted: true })
      } else if (res.statusCode === 404 && !this.state.reportsPosted) {
        this.generateReport(false)
        this.setState({ reportsPosted: true, reportsLoaded: false })
        return
      } else {
        return
      }
      state.reportsLoaded = true
      this.setState({ ...state })
    })
  }

  updateSelectedRunIds = (values: string[]) => {
    this.setState({
      selectedRunIds: values,
    })
  }

  componentDidMount() {
    if (this.state.reportsLoaded === false) {
      void this.checkReportStatus()
    }

    if (this.state.compileLoaded === false) {
      const id = this.props.analysisId
      const state = { ...this.state }
      void jwtFetch(
        `${domainRoot}/api/analyses/String(${String(id)})/compile`,
      ).then(res => {
        state.status = res.status
        state.compileLoaded = true
        this.setState({ ...state })
      })
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (prevProps.postReports === false && this.props.postReports === true) {
      this.setState({
        reportsLoaded: false,
        reportsPosted: false,
      })
      void this.checkReportStatus()
    }
    if (
      prevState.reportsLoaded === true &&
      this.state.reportsLoaded === false
    ) {
      void this.checkReportStatus()
    }
  }

  componentWillUnmount() {
    clearInterval(this._timer)
    this._timer = null
  }

  updateReports = () => {
    const runTitles = this.props.runs
      .filter(x => {
        return this.state.selectedRunIds.includes(String(x.id))
      })
      .map(x => this.formatRun(x))

    this.setState({
      reportsLoaded: false,
      reportsPosted: false,
      runTitles: runTitles,
    })
  }

  // proper type used by antd coming from rc-select FilterFunc
  filterRuns: any = (
    inputValue: string,
    option: React.ReactElement<OptionProps>,
  ): boolean => {
    if (option.props.children) {
      return String(option.props.children).includes(inputValue)
    }
    return false
  }

  formatRun = (run: Run) => {
    let ret = ''
    if (run.subject !== undefined) {
      ret = ret.concat('subject - ', String(run.subject), ' ')
    }
    if (run.session !== undefined) {
      ret = ret.concat('Session - ', String(run.session), ' ')
    }
    if (run.number !== undefined) {
      ret = ret.concat('Run - ', String(run.number), ' ')
    }
    if (ret === '') {
      ret = run.id
    }
    return ret
  }

  handleVisibleChange = visible => {
    if (!visible) {
      this.setState({ warnVisible: visible })
      return
    }
    if (this.state.selectedRunIds.length < 3) {
      this.confirm()
    } else {
      this.setState({ warnVisible: visible })
    }
  }

  confirm = () => {
    this.setState({ warnVisible: false })
    this.updateReports()
  }

  cancel = () => {
    this.setState({ warnVisible: false })
  }

  updateScale = () => {
    this.setState({ scale: !this.state.scale })
    this.generateReport(!this.state.scale)
    this.updateReports()
  }

  render() {
    const runIdsOptions: JSX.Element[] = []
    this.props.runs.map(x =>
      runIdsOptions.push(
        <Option key={String(x.id)} value={String(x.id)}>
          {this.formatRun(x)}
        </Option>,
      ),
    )
    const cardTitle = <>Design Reports</>

    const cardExtra = (
      <>
        <DateTag modified_at={this.props.modified_at} />
        <Tooltip
          title={
            'Here you can preview the final design and correlation matrices. \
          \nClick on the design matrix columns to view the timecourse in detail.'
          }
          defaultVisible={this.props.defaultVisible}>
          <QuestionCircleTwoTone style={{ fontSize: '17px' }} />
        </Tooltip>
      </>
    )

    // eslint-disable-next-line
    console.log(this.state)

    return (
      <div>
        <Card title={cardTitle} extra={cardExtra} key="plots">
          <Spin spinning={!this.state.reportsLoaded}>
            <div className="plotRunSelectorContainer">
              <Select
                mode="multiple"
                onChange={this.updateSelectedRunIds}
                filterOption={this.filterRuns}
                defaultValue={this.state.selectedRunIds}
                className="plotRunSelector">
                {runIdsOptions}
              </Select>
              <Popconfirm
                visible={this.state.warnVisible}
                title="Loading too many reports at once may affect performance."
                onVisibleChange={this.handleVisibleChange}
                onConfirm={this.confirm}
                onCancel={this.cancel}
                okText="Ok"
                cancelText="Cancel">
                <Button
                  loading={!this.state.reportsLoaded}
                  type="primary"
                  className="plotRunSelectorBtn">
                  Get Reports
                </Button>
              </Popconfirm>
            </div>

            <Plots
              matrices={this.state.matrices}
              plots={this.state.plots}
              corr_plots={this.state.corr_plots}
              runTitles={this.state.runTitles}
              scale={this.state.scale}
              updateScale={this.updateScale}
            />

            {this.state.warnings.length > 0 && (
              <Warnings warnings={this.state.warnings} />
            )}

            {this.state.reportTraceback && (
              <div>
                <br />
                <Tracebacks
                  message="Report failed to generate"
                  traceback={this.state.reportTraceback}
                />
                <br />
              </div>
            )}
          </Spin>
        </Card>
        <br />
      </div>
    )
  }
}
