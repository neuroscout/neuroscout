import * as React from 'react'
import { DownloadOutlined } from '@ant-design/icons'
import { Button, Card, Skeleton } from 'antd'
import { config } from '../config'
import { jwtFetch } from '../utils'
import '../css/Bibliography.css'

const domainRoot = config.server_url
const ButtonGroup = Button.Group

type bibProps = {
  analysisId?: string
}

interface BibState {
  supporting: string[]
  data: string[]
  extraction: string[]
  neuroscout: string[]
  csl_json: string[]
  bibLoaded: boolean
}

const RefList = (props: { refs: string[] }) => {
  const items = props.refs.map((item, key) => (
    <div
      className={'bibStyle'}
      key={key}
      dangerouslySetInnerHTML={{ __html: item }}
    />
  ))

  return <div>{items}</div>
}

type DownloadButtonProps = { data: string[]; title: string; filename: string }
const DownloadButton = (props: DownloadButtonProps) => {
  const formatted =
    'data: text/json;charset=utf-8,' +
    encodeURIComponent(JSON.stringify(props.data))

  return (
    <a href={formatted} download={props.filename}>
      <Button type="primary" icon={<DownloadOutlined />}>
        {props.title}
      </Button>
    </a>
  )
}

export class BibliographyTab extends React.Component<bibProps, BibState> {
  constructor(props: bibProps) {
    super(props)
    const state: BibState = {
      supporting: [],
      neuroscout: [],
      data: [],
      extraction: [],
      csl_json: [],
      bibLoaded: false,
    }
    this.state = state
  }

  loadBib = (): void => {
    const id = String(this.props.analysisId)
    const url = `${domainRoot}/api/analyses/${id}/bibliography`
    const state = { ...this.state }
    void jwtFetch(url, { method: 'GET' }).then((res: BibState) => {
      state.supporting = res.supporting
      state.data = res.data
      state.extraction = res.extraction
      state.neuroscout = res.neuroscout
      state.csl_json = res.csl_json
      state.bibLoaded = true
      this.setState({ ...state })
    })
  }

  componentDidMount() {
    if (this.state.bibLoaded === false) {
      this.loadBib()
    }
  }

  render() {
    const merged = this.state.data.concat(
      this.state.neuroscout.concat(
        this.state.supporting.concat(this.state.extraction),
      ),
    )
    return (
      <div>
        <p>
          Below are the references for the tools, data, and extractors used in
          this analysis. Be sure to cite these references if you publish any
          results stemming from this analysis.
        </p>
        <Card title="Neuroscout">
          <Skeleton loading={this.state.bibLoaded === false}>
            {this.state.neuroscout && <RefList refs={this.state.neuroscout} />}
          </Skeleton>
        </Card>
        <br />
        <Card title="Supporting packages">
          <Skeleton loading={this.state.bibLoaded === false}>
            {this.state.supporting && <RefList refs={this.state.supporting} />}
          </Skeleton>
        </Card>
        <br />
        <Card title="Dataset">
          <Skeleton loading={this.state.bibLoaded === false}>
            {this.state.data && <RefList refs={this.state.data} />}
          </Skeleton>
        </Card>
        <br />
        <Card title="Extraction">
          <Skeleton loading={this.state.bibLoaded === false}>
            {this.state.extraction && <RefList refs={this.state.extraction} />}
          </Skeleton>
        </Card>
        <br />

        <Card title="Export All" bordered={false} style={{ width: 400 }}>
          <ButtonGroup>
            <DownloadButton
              data={merged}
              title="HTML - APA"
              filename={String(this.props.analysisId) + '_refs.html'}
            />
            <DownloadButton
              data={this.state.csl_json}
              title="CSL - JSON"
              filename={String(this.props.analysisId) + '_refs.json'}
            />
          </ButtonGroup>
        </Card>
      </div>
    )
  }
}
