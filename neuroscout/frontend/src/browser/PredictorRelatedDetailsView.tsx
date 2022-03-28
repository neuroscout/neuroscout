import React, { useState, useEffect } from 'react'
import { Divider, Row, Skeleton, Space, Table } from 'antd'
import { Header, MainCol } from '../HelperComponents'
import { api } from '../api'
import { Link, Redirect } from 'react-router-dom'
import { PredictorRelatedDetails, ApiAnalysis, Dataset } from '../coretypes'
import { AnalysisListTable } from './AnalysisList'
import { setDatasetNames } from '../App'

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
  let extractor = <></>
  if (details.predictor?.extracted_feature?.extractor_name) {
    extractor = extractor = (
      <>
        {' '}
        - Extractor:{' '}
        <a href="http://psychoinformaticslab.github.io/pliers/reference.html#module-pliers.extractors">
          {details.predictor.extracted_feature.extractor_name}
        </a>
      </>
    )
  }
  const analysisListProps = {
    loggedIn: false,
    publicList: true,
    analyses: details.analyses,
    datasets: details.datasets,
    showOwner: true,
  }
  const datasets = details.datasets.sort((a, b) => a.name.localeCompare(b.name))
  return (
    <div>
      <Row justify="center">
        <MainCol>
          <Skeleton loading={!details.predictor}>
            <Header title={name} />
            <Row>
              <div>
                {description}
                {extractor}
              </div>
            </Row>
            <Divider />
            <Row>
              <h3>Used in these Analyses</h3>
              <AnalysisListTable {...analysisListProps} />
            </Row>
            <Divider />
            <Row>
              <h3>Present in these Datasets</h3>
            </Row>
            <Row>
              <Space>
                {datasets.map(ds => (
                  <>
                    <Link to={`/dataset/${ds.id}`}>{ds.name}</Link>
                  </>
                ))}
              </Space>
            </Row>
          </Skeleton>
        </MainCol>
      </Row>
    </div>
  )
}

export default PredictorRelatedDetailsView
