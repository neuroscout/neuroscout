import React, { useState, useEffect } from 'react'
import { Link, Redirect } from 'react-router-dom'
import { Header, MainCol } from '../HelperComponents'
import { Collapse, Descriptions, Row, Table, Tag } from 'antd'
import { AppAnalysis, Dataset, Predictor, Task } from '../coretypes'
import { api } from '../api'
import { predictorColor } from '../utils'
import { AnalysisListTable } from './AnalysisList'
import {
  ModalityColorIndex,
  PredictorByExtractorList,
  PredictorTagList,
} from './PredictorList'

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

interface TaskPredictors {
  task: Task
  predictors: Predictor[]
}

export const DatasetDescription = (props: Dataset): JSX.Element => {
  const rowData: {
    title?: string
    content: string | JSX.Element
    span?: number
  }[] = [
    { content: props.longDescription ? props.longDescription : 'n/a' },
    { title: 'Authors', content: props.authors.join(', ') },
    {
      title: 'Mean Age',
      content: props.meanAge ? props.meanAge.toFixed(1) : 'n/a',
      span: 1,
    },
    {
      title: 'Percent Female',
      content: props.percentFemale
        ? (props.percentFemale * 100).toFixed(1)
        : 'n/a',
      span: 4,
    },
    {
      title: 'References and Links',
      content: React.createElement('a', { href: props.url }, [props.url]),
    },
  ]

  return (
    <Descriptions column={5} size="small">
      {rowData.map((x, i) => (
        <Descriptions.Item label={x.title} key={i} span={x.span ? x.span : 5}>
          {x.content}
        </Descriptions.Item>
      ))}
    </Descriptions>
  )
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
    hideDatasets: true,
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
          data.sort((a, b) => a.name.localeCompare(b.name))
          newTaskPredictors.predictors.push(...data)
          return newTaskPredictors
        })
      }),
    ).then(newTaskPredictors => {
      setTaskPredictors(newTaskPredictors)
    })
  }, [props.id])

  return (
    <Row justify="center">
      <MainCol>
        <Header title={props.name} subtitle="dataset" />
        <DatasetDescription {...props} />
        <Header title="Available Tasks" />
        {taskPredictors.map(taskPredictor => (
          <Row key={taskPredictor.task.id}>
            <Header
              title={taskPredictor.task.name}
              subtitle={taskPredictor.task.summary}
            />
            <PredictorByExtractorList predictors={taskPredictor.predictors} />
          </Row>
        ))}
        <div className="colorIndexPredictorList">
          <ModalityColorIndex />
        </div>
      </MainCol>
    </Row>
  )
}
