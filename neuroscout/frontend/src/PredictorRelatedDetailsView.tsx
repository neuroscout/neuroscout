import React, { useState, useEffect } from 'react'
import { Row } from 'antd'
import { MainCol, datasetColumns } from './HelperComponents'
import { api } from './api'
import { Link, Redirect } from 'react-router-dom'
import { PredictorRelatedDetails, ApiAnalysis, Dataset } from './coretypes'
import { AnalysisListTable } from './AnalysisList'
import { setDatasetNames } from './App'

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
  }
  return (
    <div>
      <Row justify="center">
        <MainCol>
          <Row>
            <span className="viewTitle">{name}</span>
          </Row>
          <Row>
            <p>{description}</p>
          </Row>
          <Row>
            <AnalysisListTable {...analysisListProps} />
          </Row>
        </MainCol>
      </Row>
    </div>
  )
}

export default PredictorRelatedDetailsView
