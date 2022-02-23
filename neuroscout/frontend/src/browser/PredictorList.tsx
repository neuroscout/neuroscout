import React, { useState, useEffect } from 'react'
import { Collapse, Row } from 'antd'
import { Predictor } from '../coretypes'
import { MainCol, PredictorLink } from '../HelperComponents'
import { api } from '../api'

const { Panel } = Collapse

export const PredictorTagList = (props: {
  predictors: Predictor[]
}): JSX.Element => {
  props.predictors.sort((a, b) => a.name.localeCompare(b.name))
  return (
    <div>
      {props.predictors.map(predictor => (
        <PredictorLink key={predictor.id} {...predictor} />
      ))}
    </div>
  )
}

export const PredictorByExtractorList = (props: {
  predictors: Predictor[]
}): JSX.Element => {
  const extractors = {}
  props.predictors.map(predictor => {
    let ef_name = 'none'
    if (predictor.extracted_feature?.extractor_name) {
      ef_name = predictor.extracted_feature.extractor_name
    } else if (predictor.source) {
      ef_name = predictor.source
    }
    extractors[ef_name]
      ? extractors[ef_name].push(predictor)
      : (extractors[ef_name] = [predictor])
  })
  return (
    <Collapse style={{ width: '100%' }} ghost>
      {Object.keys(extractors)
        .sort()
        .map(key => (
          <Panel key={key} header={`${key} (${extractors[key].length})`}>
            <PredictorTagList predictors={extractors[key]} />
          </Panel>
        ))}
    </Collapse>
  )
}

export const PredictorListView = (): JSX.Element => {
  const [predictors, setPredictors] = useState<Predictor[]>([])
  useEffect(() => {
    api.getPredictors().then(data => {
      setPredictors(data)
    })
  }, [])
  return (
    <div className="App">
      <Row justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          <PredictorByExtractorList predictors={predictors} />
        </MainCol>
      </Row>
    </div>
  )
}
