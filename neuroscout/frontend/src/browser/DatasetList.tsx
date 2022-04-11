import React, { useState, useEffect } from 'react'
import { Collapse, Row, Table } from 'antd'
import { Dataset } from '../coretypes'
import {
  datasetColumns,
  Header,
  MainCol,
  PredictorLink,
} from '../HelperComponents'
import { api } from '../api'
import { DatasetDescription } from './DatasetDetailView'

const DatasetDescriptionExpand = (
  record: Dataset,
  index,
  indent,
  string,
): JSX.Element => <DatasetDescription {...record} />

export const DatasetListView = (props: {
  datasets: Dataset[]
}): JSX.Element => {
  return (
    <div className="App">
      <Row justify="center" style={{ background: '#fff', padding: 0 }}>
        <MainCol>
          <Header title="Datasets" />
          <Table
            className="selectDataset"
            columns={datasetColumns}
            rowKey="id"
            size="small"
            dataSource={props.datasets}
            pagination={false}
            expandedRowRender={DatasetDescriptionExpand}
          />
        </MainCol>
      </Row>
    </div>
  )
}
