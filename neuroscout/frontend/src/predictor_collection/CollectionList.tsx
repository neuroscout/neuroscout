import * as React from 'react'
import { PlusOutlined, ReloadOutlined } from '@ant-design/icons'
import {
  Button,
  Card,
  Checkbox,
  Collapse,
  Form,
  Input,
  List,
  Modal,
  Row,
  Tabs,
  Table,
  Tag,
  Typography,
  Upload,
} from 'antd'
import { TableRowSelection } from 'antd/lib/table/interface'

import { api } from '../api'
import {
  ApiUser,
  Dataset,
  PredictorCollection,
  Run,
  RunFilters,
} from '../coretypes'
import { datasetColumns, MainCol } from '../HelperComponents'
import { AddPredictorsForm } from './AddPredictorsForm'

const { Text } = Typography

export interface CollectionListProps {
  datasets: Dataset[]
  collections: PredictorCollection[]
  updateUser: (data: any, updateLocal?: boolean) => void
}

export interface CollectionListState {
  formModal: boolean
  user?: ApiUser
  collections?: PredictorCollection[]
  loading: boolean
}

export class PredictorCollectionList extends React.Component<
  CollectionListProps,
  CollectionListState
> {
  constructor(props) {
    super(props)
    this.state = { formModal: false, loading: false }
  }

  // this duplicates code in auth.store but allows us to handle promise more easily and keep
  // loading state local
  loadCollections = () => {
    this.setState({ loading: true })
    api.getPredictorCollections().then(colls => {
      this.setState({ loading: false })
      this.props.updateUser({ predictorCollections: colls })
    })
  }

  componentDidMount() {
    this.loadCollections()
  }

  closeModal = () => {
    this.loadCollections()
    this.setState({ formModal: false })
  }

  render() {
    const datasets = this.props.datasets.filter(x => x.active === true)
    const collectionColumns = [
      {
        title: 'Name',
        dataIndex: 'collection_name',
        sorter: (a, b) => a.collection_name.localeCompare(b.collection_name),
      },
      {
        title: (
          <>
            Status <ReloadOutlined onClick={this.loadCollections} />
          </>
        ),
        dataIndex: 'status',
        sorter: (a, b) => a.status.localeCompare(b.status),
      },
      {
        title: 'Predictors',
        dataIndex: 'predictors',
        render: (predictors, record, index) => {
          if (!record.traceback) {
            return predictors.map(x => x.name).join(', ')
          }
          return <Text type="danger">{record.traceback}</Text>
        },
      },
      {
        title: 'Predictor Visibility',
        dataIndex: 'predictors',
        key: 'pred_visiblity',
        render: (predictors, record, index) => {
          if (!predictors || !predictors.length) {
            return ''
          } else if (predictors.every(x => x.private === true)) {
            return <Tag>Private</Tag>
          } else if (predictors.every(x => x.private === false)) {
            return <Tag color="blue">Public</Tag>
          } else {
            return <Tag color="yellow">Mixed</Tag>
          }
        },
      },
    ]

    return (
      <Row justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          <Row>
            <span className="viewTitle"> My Predictor Collections</span>
            <span style={{ float: 'right' }}>
              <Button onClick={() => this.setState({ formModal: true })}>
                <PlusOutlined /> Add New Predictors
              </Button>
            </span>
          </Row>
          <br />
          {this.state.formModal && (
            <Modal
              title="Upload New Predictors"
              width="70%"
              visible={this.state.formModal}
              onCancel={() => this.setState({ formModal: false })}
              okButtonProps={{ hidden: true }}
              cancelButtonProps={{ hidden: true }}>
              <AddPredictorsForm
                datasets={datasets}
                closeModal={this.closeModal}
              />
            </Modal>
          )}
          {this.props.collections && (
            <Table
              columns={collectionColumns}
              rowKey="id"
              dataSource={this.props.collections}
              loading={this.state.loading}
              locale={{ emptyText: 'No custom predictors uploaded.' }}
            />
          )}
        </MainCol>
      </Row>
    )
  }
}
