import * as React from 'react'
import { Alert, Button, Card, Checkbox, Modal, Tooltip, Switch } from 'antd'
import memoize from 'memoize-one'

import { config } from '../config'
import { jwtFetch } from '../utils'
import { Analysis, NvUploads } from '../coretypes'
import { DateTag, StatusTag } from '../HelperComponents'
import { api } from '../api'
import { Tracebacks } from './Report'
import NeurovaultLinks from './NeuroVault'

const domainRoot = config.server_url

export class DLLink extends React.Component<{
  status?: string
  analysisId?: string
}> {
  render(): JSX.Element {
    let status = this.props.status
    const analysisId = this.props.analysisId
    if (status === undefined) {
      status = 'DRAFT'
    }

    let bundleLink = ''
    if (status === 'PASSED' && analysisId) {
      bundleLink = `${domainRoot}/analyses/${analysisId}_bundle.tar.gz`
    }

    return (
      <span>
        <a href={bundleLink}>Download</a>
      </span>
    )
  }
}

type PubAccessProps = {
  private: boolean | undefined
  updateAnalysis?: (
    value: Partial<Analysis>,
    unsavedChanges: boolean,
    save: boolean,
  ) => void
}
class PubAccess extends React.Component<PubAccessProps, Record<string, never>> {
  render() {
    return (
      <Tooltip title="Should this analysis be private (only visible to you) or public?">
        <Switch
          checked={!this.props.private}
          checkedChildren="Public"
          unCheckedChildren="Private"
          onChange={checked => {
            if (this.props.updateAnalysis) {
              this.props.updateAnalysis({ private: !checked }, false, true)
            }
          }}
        />
      </Tooltip>
    )
  }
}

type submitProps = {
  status?: string
  analysisId?: string
  name?: string
  modified_at?: string
  confirmSubmission: (build: boolean) => void
  private: boolean
  updateAnalysis?: (value: Partial<Analysis>) => void
  userOwns?: boolean
}

export class Submit extends React.Component<
  submitProps,
  { tosAgree: boolean; validate: boolean }
> {
  constructor(props: submitProps) {
    super(props)

    this.state = {
      tosAgree: this.props.status !== 'DRAFT',
      validate: true,
    }
  }

  onChange(e): void {
    this.setState({ tosAgree: e.target.checked })
  }

  validateChange(e): void {
    const setState = this.setState.bind(this)
    if (!e.target.checked) {
      Modal.confirm({
        title: 'Disable validation of model?',
        content: `Disabling validation of the model will speed up bundle generation
          but can lead to unexpected errors at runtime. Use at your own risk!`,
        onOk() {
          setState({ validate: e.target.checked })
        },
      })
    } else {
      this.setState({ validate: e.target.checked })
    }
  }

  render(): JSX.Element {
    let { status } = this.props
    if (status === undefined) {
      status = 'DRAFT'
    }
    const onChange = this.onChange.bind(this)
    const validateChange = this.validateChange.bind(this)
    return (
      <div className="statusTOS">
        {!this.props.name && (
          <span>
            <br />
            <Alert
              message="Analysis needs name to be generated"
              type="warning"
              showIcon
              closable
            />
          </span>
        )}
        <br />
        <h3>Terms for analysis generation:</h3>
        <ul>
          <li>
            I agree that once I submit my analysis, I will not be able to delete
            or edit it.
          </li>
          <li>
            I agree if I publish results stemming from this analysis, I must
            make public, and cite all relevant analyses.
          </li>
          <li>
            {' '}
            I understand that the statistical maps generated by this analysis
            will be automatically uploaded to the NeuroVault website by default
            (users may opt-out at run-time).
          </li>
          {this.props.private && (
            <li>
              I understand that although my analysis is currently private,
              anyone with the analysis ID may view this analysis, and subsequent
              uploaded results.
            </li>
          )}
          {!this.props.private && (
            <li>
              I understand that my analysis is currently public and will be
              searchable by other users.
            </li>
          )}
        </ul>
        <Checkbox onChange={validateChange} checked={this.state.validate}>
          Validate design matrix construction for all runs (reduces the chance
          of run-time errors, but can substantially increase bundle compilation
          time.)
        </Checkbox>
        <br />
        <Checkbox onChange={onChange} checked={this.state.tosAgree}>
          I have read and agree to Neuroscout&apos;s terms of service
        </Checkbox>
        <br />
        <Button
          hidden={!this.props.analysisId}
          onClick={this.props.confirmSubmission.bind(this, this.state.validate)}
          type={'primary'}
          disabled={
            !this.state.tosAgree ||
            !['DRAFT', 'FAILED'].includes(status) ||
            !this.props.name
          }
        >
          Generate
        </Button>
      </div>
    )
  }
}

type statusTabState = {
  compileTraceback: string
  nvUploads?: NvUploads[]
  imageVersion: string
}

export class StatusTab extends React.Component<submitProps, statusTabState> {
  constructor(props: submitProps) {
    super(props)
    this.state = {
      compileTraceback: '',
      imageVersion: '',
    }
  }

  componentDidMount(): void {
    void api.getImageVersion().then(version => {
      if (version) {
        this.setState({ imageVersion: `:${version}` })
      }
    })
  }

  getTraceback(id: number | string | undefined): void {
    if (id === undefined) {
      return
    }
    void jwtFetch(`${domainRoot}/api/analyses/${String(id)}/compile`).then(
      (res: { traceback?: string }) => {
        if (res.traceback) {
          this.setState({ compileTraceback: res.traceback })
        }
      },
    )
  }

  newlyFailed = memoize(status => {
    if (status === 'FAILED') {
      this.getTraceback(this.props.analysisId)
    }
  })

  render(): JSX.Element {
    this.newlyFailed(this.props.status)
    return (
      <div>
        <div className="statusHeader">
          {this.props.userOwns && (
            <>
              <PubAccess
                private={this.props.private}
                updateAnalysis={this.props.updateAnalysis}
              />
              <span> </span>
            </>
          )}
          <DateTag
            modified_at={this.props.modified_at ? this.props.modified_at : ''}
          />
          <StatusTag
            status={this.props.status}
            analysisId={this.props.analysisId}
          />
        </div>
        {this.props.children}
        {this.props.status === 'PASSED' && (
          <div>
            <h3>Analysis Passed</h3>
            <p>
              {this.props.userOwns && (
                <Alert
                  message="Passed"
                  description="Your analysis has been validated and compiled."
                  type="success"
                  showIcon
                />
              )}
              <br />
              Run the analysis with this this command, replacing
              &apos;/local/outputdirectory&apos; with a local directory. See the{' '}
              <a href="https://neuroscout.github.io/neuroscout/cli/">
                neuroscout-cli documentation{' '}
              </a>
              for a complete user guide.
            </p>
            <pre>
              <code>
                docker run --rm -it -v /local/outputdirectory:/out
                {` neuroscout/neuroscout-cli${this.state.imageVersion}`} run
                {this.props.analysisId} /out
              </code>
            </pre>
            <Card
              size="small"
              title="System Requirements"
              style={{ width: 400 }}
            >
              <p>
                OS: Windows/Linux/Mac OS with{' '}
                <a href="https://docs.docker.com/install/">Docker</a>
              </p>
              <p>RAM: 8GB+ RAM</p>
              <p>Disk space: 4GB + ~1 GB/subject</p>
            </Card>
            <br />
          </div>
        )}
        {(this.props.status === 'DRAFT' || this.props.status === 'FAILED') && (
          <Submit
            status={this.props.status}
            name={this.props.name}
            analysisId={this.props.analysisId}
            confirmSubmission={this.props.confirmSubmission}
            private={this.props.private}
          />
        )}
        {this.props.status === 'FAILED' && (
          <div>
            <br />
            <Tracebacks
              message="Analysis failed to compile"
              traceback={this.state.compileTraceback}
            />
            <br />
          </div>
        )}
        {(this.props.status === 'PENDING' ||
          this.props.status === 'SUBMITTING') && (
          <div>
            <br />
            <h3>Analysis Pending Generation</h3>
            <p>
              Analysis generation may take some time. This page will update when
              complete.
            </p>
          </div>
        )}
      </div>
    )
  }
}
