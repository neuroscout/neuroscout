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

interface TaskPredictors {
  task: Task
  predictors: Predictor[]
}

export const DatasetDetailView = (props: Dataset): JSX.Element => {
  const [taskPredictors, setTaskPredictors] = useState<TaskPredictors[]>([])
  useEffect(() => {
    setTaskPredictors([] as TaskPredictors[])
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
  console.log(taskPredictors)
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
