import React, { useState, useEffect } from 'react'
import { Predictor } from './coretypes'
import { api } from './api'

const PredictorListView = (): JSX.Element => {
  const [predictors, setPredictors] = useState<Predictor[]>([])
  useEffect(() => {
    api.getPredictors().then(data => {
      setPredictors(data)
    })
  }, [])
  return (<div></div>)
}
