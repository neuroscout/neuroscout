import React, { useState, useEffect } from 'react'
import { Link, Redirect } from 'react-router-dom'
import { MainCol } from '../HelperComponents'
import { Collapse, Row, Table, Tag } from 'antd'
import { AppAnalysis, Dataset, Predictor, Task } from '../coretypes'
import { api } from '../api'
import { predictorColor } from '../utils'
import { AnalysisListTable, PredictorTagList } from './AnalysisList'

const { Panel } = Collapse

/*
export interface Dataset {
  name: string
  id: string
  authors: string[]
  url: string
  summary: string
  longDescription?: string
  tasks: Task[]
  active: boolean
  modality: string
  meanAge?: number
  percentFemale?: number
}
*/

export const PredictorList = (props: {
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
      {Object.keys(extractors).map(key => (
        <Panel key={key} header={key}>
          <PredictorTagList predictors={extractors[key]} />
        </Panel>
      ))}
    </Collapse>
  )
}

interface TaskPredictors {
  task: Task
  predictors: Predictor[]
}

export const DatasetDetailView = (props: Dataset): JSX.Element => {
  const [taskPredictors, setTaskPredictors] = useState<TaskPredictors[]>([])
  const [analyses, setAnalyses] = useState<AppAnalysis[]>([])

  const analysisListProps = {
    loggedIn: false,
    publicList: true,
    analyses: analyses,
    datasets: [props],
    showOwner: true,
  }

  useEffect(() => {
    api.getDatasetAnalyses(props.id).then(data => {
      setAnalyses(data)
    })
    Promise.all(
      props.tasks.map(task => {
        return api.getPredictorsByTask(task.id).then(data => {
          const newTaskPredictors = {
            task: task,
            predictors: [] as Predictor[],
          }
          newTaskPredictors.predictors.push(...data)
          return newTaskPredictors
        })
      }),
    ).then(newTaskPredictors => setTaskPredictors(newTaskPredictors))
  }, [props.id])
  return (
    <Row justify="center">
      <MainCol>
        <Row>
          <h2>{props.name}</h2>
        </Row>
        <Row key="analyses">
          <h3>Used in these Analyses</h3>
          <AnalysisListTable {...analysisListProps} />
        </Row>
        <Row>
          <h3>Predictors Available Per Task</h3>
        </Row>
        {taskPredictors.map(taskPredictor => (
          <Row key={taskPredictor.task.id}>
            <div className="viewTitle">{taskPredictor.task.name}</div>
            <br />
            <PredictorList predictors={taskPredictor.predictors} />
          </Row>
        ))}
      </MainCol>
    </Row>
  )
}
