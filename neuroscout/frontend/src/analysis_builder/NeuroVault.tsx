import React, { useEffect, useState } from 'react'

import { Alert, Card, Collapse, Tooltip } from 'antd'

import { api } from '../api'
import { NvUploads } from '../coretypes'

const nvLink = (collection_id: string): JSX.Element => {
  const url = `https://neurovault.org/collections/${collection_id}`
  return (
    <a href={url} target="_blank" rel="noreferrer">
      Collection ID: {collection_id}
    </a>
  )
}

const nvCard: React.FC<{ nvUpload: NvUploads }> = props => {
  const { nvUpload } = props
  return (
    <Card
      key={String(nvUpload.id)}
      title={nvLink(String(nvUpload.id))}
      style={{ display: 'inline-block' }}
      size="small"
    >
      <Collapse>
        <Collapse.Panel
          header={
            <>
              Uploaded:{' '}
              {nvUpload.uploaded_at
                ? nvUpload.uploaded_at.split('T')[0]
                : 'n/a'}
            </>
          }
          key={String(nvUpload.id)}
        >
          <p>Estimator: {nvUpload.estimator ? nvUpload.estimator : 'n/a'}</p>
          <p>
            fMRIPrep:{' '}
            {nvUpload.fmriprep_version ? nvUpload.fmriprep_version : 'n/a'}
          </p>
          <p>
            neuroscout-cli:{' '}
            {nvUpload.cli_version ? nvUpload.cli_version : 'n/a'}
          </p>
        </Collapse.Panel>
      </Collapse>
      {nvUpload.pending > 0 && (
        <span>
          <Alert
            message={`${String(nvUpload.pending)}/${String(
              nvUpload.total,
            )} image uploads pending`}
            type="warning"
          />
        </span>
      )}
      {nvUpload.ok > 0 && (
        <Alert
          message={`${String(nvUpload.ok)}/${String(
            nvUpload.total,
          )} image uploads succeeded`}
          type="success"
        />
      )}
      {nvUpload.failed > 0 && (
        <Tooltip
          title={
            <>
              {nvUpload.tracebacks.map((y, i) => (
                <p key={i}>{y}</p>
              ))}
            </>
          }
        >
          <div>
            <Alert
              message={`${String(nvUpload.failed)}/${String(
                nvUpload.total,
              )} image uploads failed`}
              type="error"
            />
          </div>
        </Tooltip>
      )}
    </Card>
  )
}

const NeurovaultLinks: React.FC<{ analysisId: string | undefined }> = props => {
  const [nvUploads, setNvUploads] = useState<NvUploads[]>([] as NvUploads[])
  useEffect(() => {
    if (props.analysisId) {
      void api.getNVUploads(props.analysisId).then(apiNvUploads => {
        if (apiNvUploads !== null) {
          setNvUploads(apiNvUploads)
        }
      })
    }
  }, [props.analysisId])

  const statuses = nvUploads.map(x => nvCard({ nvUpload: x }))

  return <div style={{ display: 'flex', flexWrap: 'wrap' }}>{statuses}</div>
}

export default NeurovaultLinks
