import React, { useState, useEffect } from 'react'
import { Row, Table } from 'antd'
import { MainCol } from './HelperComponents'
import { api } from './api'
import { Link, Redirect } from 'react-router-dom'
import { PredictorRelatedDetails, ApiAnalysis, Dataset } from './coretypes'
import { AnalysisListTable } from './AnalysisList'
import { setDatasetNames } from './App'

const datasetColumns = [
  {
    title: 'Name',
    dataIndex: 'name',
    width: 130,
    sorter: (a, b) => a.name.localeCompare(b.name),
    render: (text, record) => <Link to={`/dataset/${record.id}`}>{text}</Link>,
  },
  { title: 'Summary', dataIndex: 'summary' },
]

const PredictorRelatedDetailsView = (props: { id: string }): JSX.Element => {
  const [details, setDetails] = useState<PredictorRelatedDetails>({
    analyses: [],
    datasets: [],
  })

  useEffect(() => {
    api.getPredictorRelatedDetails(props.id).then(apiDetails => {
      if (apiDetails) {
        setDatasetNames(apiDetails?.analyses, apiDetails?.datasets)
        setDetails(apiDetails)
      }
    })
  }, [props.id])

  const name = details.predictor ? details.predictor.name : ' '
  const description = details.predictor ? details.predictor.description : ' '
  const analysisListProps = {
    loggedIn: false,
    publicList: true,
    analyses: details.analyses,
    datasets: details.datasets,
    showOwner: true,
  }
  return (
    <div>
      <Row justify="center">
        <MainCol>
          <Row>
            <div className="viewTitle">{name}</div>
            <div className="viewTitleDescriptor"> - {description}</div>
          </Row>
          <Row></Row>
          <h3>Used in these Analyses</h3>
          <Row>
            <AnalysisListTable {...analysisListProps} />
          </Row>
          <h3>Present in these Datasets</h3>
          <Row>
            <Table
              className="selectDataset"
              columns={datasetColumns}
              rowKey="id"
              size="small"
              dataSource={details.datasets}
              pagination={false}
            />
          </Row>
        </MainCol>
      </Row>
    </div>
  )
}

export default PredictorRelatedDetailsView
