/*
Resuable AnalysisList component used for displaying a list of analyses, e.g. on
the home page or on the 'browse public analysis' page
*/
import * as React from 'react'
import { Button, Row, Table, Tag, Input } from 'antd'
import { CheckCircleTwoTone } from '@ant-design/icons'
import { MainCol, Space, StatusTag } from './HelperComponents'
import { AppAnalysis, AnalysisResources, Dataset } from './coretypes'
import { api } from './api'
import { Link, Redirect } from 'react-router-dom'
import { ColumnsType } from 'antd/es/table'
import { predictorColor } from './utils'

import memoize from 'memoize-one'

class AnalysisResourcesDisplay extends React.Component<
  { analysisId: string },
  { resources?: AnalysisResources }
> {
  constructor(props: { analysisId: string }) {
    super(props)
    this.state = { resources: undefined }
  }
  componentDidMount() {
    api.getAnalysisResources(this.props.analysisId).then(res => {
      this.setState({ resources: res })
    })
  }
  render() {
    if (!this.state.resources) {
      return <div>Loading...</div>
    }
    return (
      <div>
        Predictors:
        {this.state.resources.predictors.map(predictor => (
          <Tag key={predictor.name} color={predictorColor(predictor)}>
            {' '}
            {predictor.name}
          </Tag>
        ))}
      </div>
    )
  }
}
const tableLocale = {
  filterConfirm: 'Ok',
  filterReset: 'Reset',
  emptyText: 'No Analyses',
}

export interface AnalysisListProps {
  loggedIn?: boolean
  publicList?: boolean
  analyses: AppAnalysis[] | null
  cloneAnalysis: (id: string) => Promise<string>
  onDelete?: (analysis: AppAnalysis) => void
  children?: React.ReactNode
  datasets: Dataset[]
  loading?: boolean
  showOwner?: boolean
}

export class AnalysisListTable extends React.Component<
  AnalysisListProps,
  {
    redirectId: string
    owners: string[]
    searchText: string
    ownersWidth: number
  }
> {
  constructor(props: AnalysisListProps) {
    super(props)
    let owners: string[] = []
    let ownersWidth = 10

    if (props.analyses !== null && props.analyses.length > 0) {
      owners = [
        ...new Set(
          props.analyses.filter(x => x.user_name).map(x => x.user_name),
        ),
      ].sort() as string[]
      ownersWidth = Math.max(...owners.map(x => (x ? x.length : 0))) + 4
    }
    this.state = {
      redirectId: '',
      owners: owners,
      searchText: '',
      ownersWidth: ownersWidth,
    }
  }

  componentDidUpdate(prevProps: AnalysisListProps): void {
    const length = prevProps.analyses ? prevProps.analyses.length : 0
    if (
      this.props.showOwner &&
      this.props.analyses &&
      length !== this.props.analyses.length
    ) {
      const owners = [
        ...new Set(
          this.props.analyses.filter(x => x.user_name).map(x => x.user_name),
        ),
      ].sort() as string[]

      /* no science behind adding 4, just a bit of buffer */
      const ownersWidth = Math.max(...owners.map(x => (x ? x.length : 0))) + 4
      this.setState({ owners, ownersWidth })
    }
  }

  onInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    this.setState({ searchText: String(e.target.value) })
  }

  applySearch = memoize((searchText: string, length: number) => {
    if (searchText.length < 2 || !this.props.analyses) {
      return this.props.analyses
    }
    return this.props.analyses.filter(
      x =>
        x.name.toLowerCase().includes(searchText.toLowerCase()) ||
        x.dataset_name.toLowerCase().includes(searchText.toLowerCase()),
    )
  })

  render(): React.ReactNode {
    if (this.state.redirectId !== '') {
      return <Redirect to={'/builder/' + this.state.redirectId} />
    }
    const { analyses, datasets, publicList, onDelete, showOwner } = this.props

    const datasetFilters = datasets.map(x => {
      return { text: x.name, value: x.name }
    })
    const datasetWidth =
      Math.max(...datasets.map(x => (x.name ? x.name.length : 0))) + 4

    // Define columns of the analysis table
    // Open link: always (opens analysis in Builder)
    // Delete button: only if not a public list and analysis is in draft mode
    // Clone button: any analysis
    const analysisTableColumns: ColumnsType<AppAnalysis> & {
      textWrap?: string
    } = [
      {
        title: 'ID',
        dataIndex: 'id',
        sorter: (a, b) => a.id.localeCompare(b.id),
        width: '6ch',
      },
      {
        title: 'Name',
        render: (text, record: AppAnalysis) => (
          <Link to={`/builder/${record.id}`}>
            <div className="recordName">
              {record.name ? record.name : 'Untitled'}
            </div>
          </Link>
        ),
        sorter: (a, b) => a.name.localeCompare(b.name),
      },
      {
        title: 'Status',
        dataIndex: 'status',
        render: (text, record) => <StatusTag status={record.status} />,
        sorter: (a, b) => a.status.localeCompare(b.status),
        width: '14ch',
      },
      {
        title: 'Modified at',
        dataIndex: 'modified_at',
        defaultSortOrder: 'descend' as const,
        sorter: (a, b) =>
          a.modified_at?.localeCompare(String(b.modified_at)) ?? 0,
        render: (text: string) => {
          const date = text.split('-')
          return (
            <>
              {date[2].slice(0, 2)}-{date[1]}-{date[0].slice(2, 4)}
            </>
          )
        },
        width: '14ch',
      },
      {
        title: 'Dataset',
        dataIndex: 'dataset_name',
        sorter: (a, b) => a.dataset_name.localeCompare(b.dataset_name),
        filters: datasetFilters,
        onFilter: (value, record) => record.dataset_name === value,
        width: `${datasetWidth}ch`,
        textWrap: 'break-word',
      },
    ]

    if (showOwner) {
      analysisTableColumns.push({
        title: 'Author',
        dataIndex: 'user_name',
        sorter: (a, b) =>
          String(a.user_name).localeCompare(String(b.user_name)),
        render: (text, record) => (
          <Link to={`/profile/${String(record.user_name)}`}>
            {' '}
            {record.user_name}{' '}
          </Link>
        ),
        filters: this.state.owners.map(x => {
          return { text: x, value: x }
        }),
        onFilter: (value, record) => record.user_name === value,
        width: `${this.state.ownersWidth}ch`,
      })
    }
    analysisTableColumns.push({
      title: 'NeuroVault',
      dataIndex: 'nv_count',
      width: '2ch',
      sorter: (a, b) => Number(a.nv_count) - Number(b.nv_count),
      render: (text, record: AppAnalysis) => {
        if (record.nv_count) {
          return <CheckCircleTwoTone twoToneColor="#52c41a" />
        }
        return
      },
    })
    if (publicList) {
      analysisTableColumns.splice(2, 1)
    }

    if (this.props.loggedIn) {
      analysisTableColumns.push({
        title: 'Actions',
        render: (text, record: AppAnalysis) => (
          <span>
            {record.status === 'PASSED' && (
              <>
                <Button
                  type="primary"
                  ghost
                  onClick={() => {
                    void this.props.cloneAnalysis(record.id).then(id => {
                      this.setState({ redirectId: id })
                    })
                  }}
                >
                  Clone
                </Button>
                <Space />
              </>
            )}
            {!publicList && ['DRAFT', 'FAILED'].includes(record.status) && (
              <Button danger ghost onClick={() => onDelete!(record)}>
                Delete
              </Button>
            )}
          </span>
        ),
        width: '15ch',
      })
    }
    const length = analyses ? analyses.length : 0
    const dataSource = this.applySearch(this.state.searchText, length)

    return (
      <>
        <Input.Search
          placeholder="Search by analyses name or dataset name..."
          value={this.state.searchText}
          onChange={this.onInputChange}
          className="analysisListSearch"
        />
        <Table
          columns={analysisTableColumns}
          rowKey="id"
          size="small"
          dataSource={dataSource === null ? [] : dataSource}
          loading={analyses === null || !!this.props.loading}
          expandedRowRender={record => (
            <AnalysisResourcesDisplay analysisId={record.id} />
          )}
          pagination={
            analyses !== null && analyses.length > 20
              ? { position: ['bottomRight'] }
              : false
          }
          locale={tableLocale}
          className="analysisListTable"
        />
      </>
    )
  }
}

// wrap table in components for use by itself as route
const AnalysisList = (props: AnalysisListProps): JSX.Element => {
  return (
    <div>
      <Row justify="center">
        <MainCol>
          <div className="analysisListRouteWrapper">
            <div className="analysisListTitle">
              {props.publicList ? 'Public analyses' : 'Your saved analyses'}
            </div>
            <AnalysisListTable {...props} />
          </div>
        </MainCol>
      </Row>
    </div>
  )
}

export default AnalysisList
