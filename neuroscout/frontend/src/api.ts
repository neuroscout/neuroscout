/*
  calls against the python api may be put in here to help centralize which routes are being called.
 */
import { _fetch, displayError, jwtFetch } from './utils'
import {
  ApiAnalysis,
  ApiDataset,
  ApiUpload,
  ApiUser,
  AppAnalysis,
  AnalysisResources,
  Dataset,
  ExtractorDescriptions,
  Predictor,
  PredictorRelatedDetails,
  Run,
  User,
} from './coretypes'
//  PredictorCollection
import { config } from './config'
const domainRoot = config.server_url

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const dataset: Dataset = {
    authors: d.description.Authors
      ? d.description.Authors
      : ['No authors listed'],
    summary: d.summary,
    url: d.url,
    id: d.id.toString(),
    modality: d.mimetypes.length > 0 ? d.mimetypes[0].split('/')[0] : '',
    name: d.name,
    tasks: d.tasks,
    active: d.active,
  }
  d.mean_age !== null ? (dataset.meanAge = d.mean_age) : null
  d.percent_female !== null ? (dataset.percentFemale = d.percent_female) : null
  d.long_description !== null
    ? (dataset.longDescription = d.long_description)
    : null
  return dataset
}

// Convert analyses returned by API to the shape expected by the frontend
export const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => ({
  id: data.hash_id!,
  name: data.name,
  description: data.description,
  status: data.status,
  dataset_id: data.dataset_id ? String(data.dataset_id) : '',
  created_at: data.modified_at,
  modified_at: data.modified_at,
  user_name: data.user,
  dataset_name: '',
  nv_count: data.nv_count ? data.nv_count : 0,
})

const ef_fields = [
  'description',
  'created_at',
  'resample_frequency',
  'modality',
]

const setPredictorSource = (predictors: Predictor[]): Predictor[] => {
  predictors.map(x => {
    if (x && x.extracted_feature && x.extracted_feature.id) {
      delete x.extracted_feature.id
    }
    ef_fields.map(field => {
      if (
        x.extracted_feature &&
        x.extracted_feature[field] !== undefined &&
        x.extracted_feature[field] !== null
      ) {
        x[field] = x.extracted_feature[field]
      }
    })

    Object.assign(x, x.extracted_feature, x)
    if (x.extracted_feature && x.extracted_feature.extractor_name) {
      x.source = x.extracted_feature.extractor_name
    }
  })
  return predictors
}

export const api = {
  getUser: (): Promise<ApiUser & { statusCode: number }> => {
    return jwtFetch(`${domainRoot}/api/user`)
  },

  getUsers: (): Promise<User[] & { statusCode: number }> => {
    return jwtFetch(`${domainRoot}/api/users`)
  },

  getDatasets: (active_only = true): Promise<Dataset[]> => {
    return jwtFetch(
      `${domainRoot}/api/datasets?active_only=${String(active_only)}`,
    )
      .then(data => {
        const datasets: Dataset[] = data.map(d => normalizeDataset(d))
        return datasets
      })
      .catch(error => {
        displayError(error)
        return [] as Dataset[]
      })
  },

  getPredictorCollections: (): any => {
    return jwtFetch(`${domainRoot}/api/user/collections`)
  },

  postPredictorCollection: (formData: FormData): any => {
    return jwtFetch(
      `${domainRoot}/api/predictors/collection`,
      {
        headers: { accept: 'application/json' },
        method: 'POST',
        body: formData,
      },
      true,
    )
  },

  getPredictor: (id: number): Promise<Predictor | null> => {
    return jwtFetch(`${domainRoot}/api/predictors/${id}`)
  },
  getPredictorRelatedDetails: (
    id: string,
  ): Promise<PredictorRelatedDetails | null> => {
    return jwtFetch(`${domainRoot}/api/predictors/${id}/related`).then(data => {
      const details: PredictorRelatedDetails = { analyses: [], datasets: [] }
      if (data.analyses) {
        details.analyses = data.analyses.map(x => ApiToAppAnalysis(x))
      }
      if (data.datasets) {
        details.datasets = data.datasets
      }
      if (data.predictor) {
        details.predictor = data.predictor
      }
      return details
    })
  },

  getPredictors: (ids?: number[] | string[]): Promise<Predictor[]> => {
    let url = `${domainRoot}/api/predictors`
    if (ids) {
      url = `${domainRoot}/api/predictors?run_id=${String(ids)}`
    }
    return jwtFetch(url).then(data => {
      if (data.statusCode && data.statusCode === 422) {
        return [] as Predictor[]
      }
      return setPredictorSource(data)
    })
  },

  getUserPredictors: (
    ids?: number[] | string[],
  ): Promise<Predictor[] | null> => {
    return jwtFetch(
      `${domainRoot}/api/user/predictors?run_id=${String(ids)}`,
    ).then(data => {
      if (data.statusCode && data.statusCode === 422) {
        return [] as Predictor[]
      }
      return setPredictorSource(data)
    })
  },

  getDataset: (datasetId: number | string): Promise<Dataset | null> => {
    return jwtFetch(`${domainRoot}/api/datasets/${datasetId}`)
      .then(data => {
        return normalizeDataset(data)
      })
      .catch(error => {
        displayError(error)
        return null
      })
  },
  getPredictorsByTask: (taskId: string): Promise<Predictor[]> => {
    return jwtFetch(`${domainRoot}/api/tasks/${taskId}/predictors`)
      .then(data => {
        return data as Predictor[]
      })
      .catch(error => {
        displayError(error)
        return [] as Predictor[]
      })
  },

  // Gets a logged in users own analyses
  getMyAnalyses: (): Promise<AppAnalysis[]> => {
    const url = `${domainRoot}/api/user/myanalyses`
    return jwtFetch(url)
      .then(data => {
        return (data || [])
          .filter(x => !!x.status)
          .map(x => ApiToAppAnalysis(x))
      })
      .catch(error => {
        displayError(error)
        return [] as AppAnalysis[]
      })
  },

  // Gets a logged in users own analyses
  getAnalyses: (user_name: string): Promise<AppAnalysis[]> => {
    const url = `${domainRoot}/api/user/${user_name}/analyses`
    return jwtFetch(url)
      .then(data => {
        return (data || [])
          .filter(x => !!x.status)
          .map(x => ApiToAppAnalysis(x))
      })
      .catch(error => {
        displayError(error)
        return [] as AppAnalysis[]
      })
  },

  getPublicAnalyses: (): Promise<AppAnalysis[]> => {
    return _fetch(`${domainRoot}/api/analyses`)
      .then(response => {
        return response.filter(x => !!x.status).map(x => ApiToAppAnalysis(x))
      })
      .catch(error => {
        displayError(error)
        return [] as AppAnalysis[]
      })
  },

  cloneAnalysis: (id: string): Promise<AppAnalysis | null> => {
    return jwtFetch(`${domainRoot}/api/analyses/${id}/clone`, {
      method: 'post',
    })
      .then((data: ApiAnalysis) => {
        return ApiToAppAnalysis(data)
      })
      .catch(error => {
        displayError(error)
        return null
      })
  },

  deleteAnalysis: (id: string): Promise<boolean> => {
    return jwtFetch(`${domainRoot}/api/analyses/${id}`, { method: 'delete' })
      .then(response => {
        if (response.statusCode === 200) {
          return true
        } else {
          return false
        }
      })
      .catch(error => {
        displayError(error)
        return false
      })
  },

  getRuns: (datasetId: string): Promise<Run[]> => {
    return jwtFetch(`${domainRoot}/api/runs?dataset_id=${datasetId}`)
  },

  getNVUploads: (analysisId: string): Promise<any | null> => {
    return jwtFetch(`${domainRoot}/api/analyses/${analysisId}/upload`)
      .then((data: ApiUpload[]) => {
        const uploads = [] as any[]
        if (data.length === 0) {
          return null
        }

        data.map(collection => {
          const upload = {
            uploaded_at: collection.uploaded_at,
            estimator: collection.estimator,
            fmriprep_version: collection.fmriprep_version,
            failed: 0,
            pending: 0,
            ok: 0,
            total: 0,
            id: 0,
            tracebacks: [] as (string | null)[],
          }
          if (Object.values(collection.files).length > 0) {
            const tracebacks = [
              ...new Set(
                collection.files
                  .filter(x => x.status === 'FAILED')
                  .filter(x => x.traceback !== null)
                  .map(x => x.traceback),
              ),
            ]
            if (tracebacks !== null && tracebacks.length > 0) {
              upload.tracebacks = tracebacks
            }
          }
          upload.total = collection.files.length
          upload.failed = collection.files.filter(
            x => x.status === 'FAILED',
          ).length
          upload.ok = collection.files.filter(x => x.status === 'OK').length
          upload.pending = collection.files.filter(
            x => x.status === 'PENDING',
          ).length
          upload.id = collection.collection_id
          uploads.push(upload)
          return
        })
        return uploads
      })
      .catch(error => {
        displayError(error)
        return null
      })
  },

  updateProfile: (updates): Promise<ApiUser & { statusCode: number }> => {
    return jwtFetch(`${domainRoot}/api/user`, {
      headers: { accept: 'application/json' },
      method: 'put',
      body: JSON.stringify(updates),
    })
  },
  getPublicProfile: (
    user_name: string,
  ): Promise<ApiUser & { statusCode: number }> => {
    return jwtFetch(`${domainRoot}/api/user/${user_name}`)
  },
  getExtractorDescriptions: (): Promise<ExtractorDescriptions> => {
    return jwtFetch(`${domainRoot}/api/extractors`).then(response => {
      const descriptions = {}
      response.map(elem => {
        descriptions[elem.name] = elem.description
      })
      return descriptions
    })
  },
  getImageVersion: (): Promise<string> => {
    return jwtFetch(`${domainRoot}/api/image_version`).then(res => {
      if (res.version) {
        return res.version
      }
      return ''
    })
  },
  getAnalysisResources: (id: string): Promise<AnalysisResources> => {
    return jwtFetch(`${domainRoot}/api/analyses/${id}/resources`, {
      method: 'get',
    })
  },
  getDatasetAnalyses: (id: string): Promise<AppAnalysis[]> => {
    return jwtFetch(`${domainRoot}/api/datasets/${id}/analyses`).then(res => {
      return res.map(x => ApiToAppAnalysis(x))
    })
  },
}
