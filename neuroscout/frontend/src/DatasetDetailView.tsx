import React, { useState, useEffect } from 'react'
import { MainCol } from './HelperComponents'
import { Row, Table } from 'antd'
import { Dataset, Predictor, Task } from './coretypes'
import { api } from './api'
import { PredictorTagList } from './AnalysisList'

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

/*
export const DatasetListTable = (props: {datasets: Dataset[]}): JSX.Element => {
  return (
}
*/
interface TaskPredictors {
  task: Task
  predictors: Predictor[]
}
export const DatasetDetailView = (props: Dataset): JSX.Element => {
  console.log(props)
  const [taskPredictors, setTaskPredictors] = useState<TaskPredictors[]>([])
  useEffect(() => {
    const newTaskPredictors = [] as TaskPredictors[]
    props.tasks.map(task => {
      const taskPredictors = { task: task, predictors: [] as Predictor[] }
      api.getPredictorsByTask(task.id).then(data => {
        console.log(data)
        taskPredictors.predictors.push(...data)
      })
    })
    setTaskPredictors(newTaskPredictors)
  }, [props.id])
  return (
    <Row justify="center">
      <MainCol>
        {taskPredictors.map(taskPredictor => (
          <Row key={taskPredictor.task.id}>
            <div className="viewTitle">{taskPredictor.task.name}</div>
            <br />
            <PredictorTagList predictors={taskPredictor.predictors} />
          </Row>
        ))}
      </MainCol>
    </Row>
  )
}
