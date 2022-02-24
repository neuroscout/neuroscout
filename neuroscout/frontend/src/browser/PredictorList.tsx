import React, { useState, useEffect } from 'react'
import { Col, Collapse, Divider, Row, Space, Tag } from 'antd'
import { Predictor } from '../coretypes'
import { Header, MainCol, PredictorLink } from '../HelperComponents'
import { api } from '../api'
import { modalityColor } from '../utils'

const { Panel } = Collapse

const ModalityColorIndex = (): JSX.Element => (
  <>
    <Divider orientation="left">Modality Color Key</Divider>
    <Space direction="horizontal">
      {Object.keys(modalityColor).map(key => (
        <Tag key={key} color={modalityColor[key]}>
          {key}
        </Tag>
      ))}
    </Space>
  </>
)

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

const NestedCollapse = (props: {
  predictors: Record<string, Predictor[]>
  descriptions?: Record<string, string>
}): JSX.Element => {
  const { predictors, descriptions } = props
  return (
    <Collapse style={{ width: '100%' }} ghost>
      {Object.keys(predictors)
        .sort()
        .map(key => (
          <Panel key={key} header={`${key} (${predictors[key].length})`}>
            <Space direction="vertical">
              {descriptions && descriptions[key]}
              <PredictorTagList predictors={predictors[key]} />
            </Space>
          </Panel>
        ))}
    </Collapse>
  )
}

export const PredictorByExtractorList = (props: {
  predictors: Predictor[]
}): JSX.Element => {
  const [extractorDescriptions, setExtractorDescriptions] = useState<
    Record<string, string>
  >({})
  useEffect(() => {
    api.getExtractorDescriptions().then(data => {
      setExtractorDescriptions(data)
    })
  }, [])
  const extractors = {}
  const extractor_descriptions = {}
  const collections = {}
  const sources = {}
  props.predictors.map(predictor => {
    let ef_name = 'none'
    let source = 'none'
    if (predictor.extracted_feature?.extractor_name) {
      source = 'extracted'
      ef_name = predictor.extracted_feature.extractor_name
      extractors[ef_name]
        ? extractors[ef_name].push(predictor)
        : (extractors[ef_name] = [predictor])
    } else if (predictor.source) {
      source = predictor.source
      if (source.startsWith('Collection:')) {
        collections[source]
          ? collections[source].push(predictor)
          : (collections[source] = [predictor])
      } else {
        source = predictor.source
        sources[source]
          ? sources[source].push(predictor)
          : (sources[source] = [predictor])
      }
    }
    return
  })

  return (
    <Collapse style={{ width: '100%' }} ghost>
      <Panel key="extracted" header="Extracted Features">
        <NestedCollapse
          predictors={extractors}
          descriptions={extractorDescriptions}
        />
      </Panel>
      <Panel key="collections" header="Uploaded Collections">
        <NestedCollapse predictors={collections} />
      </Panel>
      <Panel key="other" header="Regressors">
        <NestedCollapse predictors={sources} />
      </Panel>
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

  console.log(predictors)
  return (
    <div className="App">
      <Row justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          <Header title="All Predictors" subtitle="grouped by source" />
          <PredictorByExtractorList predictors={predictors} />
          <ModalityColorIndex />
        </MainCol>
      </Row>
    </div>
  )
}
