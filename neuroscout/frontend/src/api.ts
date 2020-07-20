/*
  calls against the python api may be put in here to help centralize which routes are being called.
 */
import { _fetch, displayError, jwtFetch } from './utils';
import {
  ApiAnalysis,
  ApiDataset,
  ApiUpload,
  ApiUser,
  AppAnalysis,
  Dataset,
  Predictor,
  Run
} from './coretypes';
//  PredictorCollection
import { config } from './config';
const domainRoot = config.server_url;

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const dataset: Dataset = {
    authors: d.description.Authors ? d.description.Authors : ['No authors listed'],
    summary: d.summary,
    url: d.url,
    id: d.id.toString(),
    modality: d.mimetypes.length > 0 ? d.mimetypes[0].split('/')[0] : '',
    name: d.name,
    tasks: d.tasks,
    active: d.active
  };
  d.mean_age !== null ? dataset.meanAge = d.mean_age : null;
  d.percent_female !== null ? dataset.percentFemale = d.percent_female : null;
  d.long_description !== null ? dataset.longDescription = d.long_description : null;
  return dataset;
};

// Convert analyses returned by API to the shape expected by the frontend
export const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => ({
  id: data.hash_id!,
  name: data.name,
  description: data.description,
  status: data.status,
  dataset_id: !!data.dataset_id ? '' + data.dataset_id : '',
  modified_at: data.modified_at
});

export const api = {
  getUser: (): Promise<ApiUser & {statusCode: number}> => {
    return jwtFetch(`${domainRoot}/api/user`);
  },

  getDatasets:  (active_only = true): Promise<Dataset[]> => {
    return jwtFetch(`${domainRoot}/api/datasets?active_only=${active_only}`)
    .then(data => {
      const datasets: Dataset[] = data.map(d => normalizeDataset(d));
      return datasets;
    })
    .catch((error) => {
      displayError(error);
      return [] as Dataset[];
    });
  },

  getPredictorCollection: (id: string): any => {
    return jwtFetch(`${domainRoot}/api/predictors/collection?collection_id=${id}`);
  },

  postPredictorCollection: (formData: FormData): any => {
    return jwtFetch(
      `${domainRoot}/api/predictors/collection`,
      {
        headers: {'accept': 'application/json'},
        method: 'POST',
        body: formData 
      },
      true
    );
  },

  getPredictor: (id: number): Promise<Predictor | null> => {
    return jwtFetch(`${domainRoot}/api/predictors/${id}`);
  },

  getPredictors: (ids: (number[] | string[])): Promise<Predictor[] | null> => {
    return jwtFetch(`${domainRoot}/api/predictors?run_id=${ids}`).then((data) => {
      if (data.statusCode && data.statusCode === 422) {
        return [] as Predictor[];
      }
      return data;
    });
  },

  getDataset: (datasetId: (number | string)): Promise<(Dataset | null)> => {
  return jwtFetch(`${domainRoot}/api/datasets/${datasetId}`)
    .then(data => {
      return normalizeDataset(data);
    })
    .catch((error) => {
      displayError(error);
      return null;
    });
  },

  // Gets a logged in users own analyses
  getAnalyses: (id?: number): Promise<AppAnalysis[]> => {
    let url = `${domainRoot}/api/user/myanalyses`;
    if (!!id) {
      url = `${domainRoot}/api/user/${id}/analyses`;
    }
    return jwtFetch(url)
      .then(data => {
        return (data || []).filter(x => !!x.status).map((x) => ApiToAppAnalysis(x));
      })
      .catch((error) => {
        displayError(error);
        return [] as AppAnalysis[];
      });
  },

  getPublicAnalyses: (): Promise<AppAnalysis[]> => {
    return _fetch(`${domainRoot}/api/analyses`)
    .then((response) => {
      return response.filter(x => !!x.status).map(x => ApiToAppAnalysis(x));
    })
    .catch((error) => {
      displayError(error);
      return [] as AppAnalysis[];
    });
  },

  cloneAnalysis: (id: string): Promise<AppAnalysis | null> => {
    return jwtFetch(`${domainRoot}/api/analyses/${id}/clone`, { method: 'post' })
      .then((data: ApiAnalysis) => {
        return ApiToAppAnalysis(data);
      })
      .catch((error) => {
        displayError(error);
        return null;
      });
  },

  deleteAnalysis: (id: string): Promise<boolean> => {
      return jwtFetch(`${domainRoot}/api/analyses/${id}`, { method: 'delete' })
      .then((response) => {
        if (response.statusCode === 200) {
          return true;
        } else {
          return false;
        }
      })
      .catch((error) => {
        displayError(error);
        return false;
      });
  },

  getRuns: (datasetId: string): Promise<Run[]> => {
    return jwtFetch(`${domainRoot}/api/runs?dataset_id=${datasetId}`);
  },

  getNVUploads: (analysisId: (string)): Promise<(any | null)> => {
    return jwtFetch(`${domainRoot}/api/analyses/${analysisId}/upload`)
    .then((data: ApiUpload[]) => {
      let uploads = [] as any[];
      if (data.length === 0) {
        return null;
      }

      data.map(collection => {
        let upload = {
          failed: 0,
          pending: 0,
          ok: 0,
          total: 0,
          id: 0,
          tracebacks: [] as (string | null)[]
        };
        let tracebacks = [...new Set(
          collection.files.filter(x => x.status === 'FAILED').filter(x => x.traceback !== null).map(x => x.traceback)
        )];
        if (tracebacks !== null && tracebacks.length > 0) {
          upload.tracebacks = tracebacks;
        }
        upload.total = collection.files.length;
        upload.failed = collection.files.filter(x => x.status  === 'FAILED').length;
        upload.ok = collection.files.filter(x => x.status === 'OK').length;
        upload.pending = collection.files.filter(x => x.status === 'PENDING').length;
        upload.id = collection.collection_id;
        uploads.push(upload);
      });
      return uploads;
    })
    .catch((error) => {
      displayError(error);
      return null;
    });
  },

  updateProfile: (updates): Promise<ApiUser & {statusCode: number}> => {
    return jwtFetch(
      `${domainRoot}/api/user`,
      {
        headers: {'accept': 'application/json'},
        method: 'put',
        body: JSON.stringify(updates)
      }
    );
  },
  getPublicProfile: (user_id): Promise<ApiUser & {statusCode: number}> => {
    return jwtFetch(`${domainRoot}/api/user/${user_id}`);
  }
};
