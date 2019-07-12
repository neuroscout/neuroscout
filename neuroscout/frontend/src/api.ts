/*
  calls against the python api may be put in here to help centralize which routes are being called.
 */
import { _fetch, displayError, jwtFetch } from './utils';
import {
  ApiDataset,
  ApiAnalysis,
  AppAnalysis,
  Dataset
} from './coretypes';
import { config } from './config';
const domainRoot = config.server_url;

// Normalize dataset object returned by /api/datasets
const normalizeDataset = (d: ApiDataset): Dataset => {
  const authors = d.description.Authors ? d.description.Authors : ['No authors listed'];
  const description = d.summary;
  const url = d.url;
  const id = d.id.toString();
  const { name, tasks, active } = d;
  return { id, name, authors, url, description, tasks, active };
};

// Convert analyses returned by API to the shape expected by the frontend
export const ApiToAppAnalysis = (data: ApiAnalysis): AppAnalysis => ({
  id: data.hash_id!,
  name: data.name,
  description: data.description,
  status: data.status,
  datasetName: !!data.dataset_id ? '' + data.dataset_id : '',
  modifiedAt: data.modified_at
});

export const api = {
  getUser: (): Promise<ApiUser> => {
    return jwtFetch(`${domainRoot}/api/user`)
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

  getPredictorCollection: (id: string): Promise<PredictorCollection[]> => {
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
  getAnalyses: (): Promise<AppAnalysis[]> => {
    return jwtFetch(`${domainRoot}/api/user`)
      .then(data => {
        return (data.analyses || []).filter(x => !!x.status).map((x) => ApiToAppAnalysis(x));
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

  getNVUploads: (analysisId: (string)): Promise<(any | null)> => {
    return jwtFetch(`${domainRoot}/api/analyses/${analysisId}/upload`)
    .then(data => {
      let uploads = { 
        'last_failed': null as any,
        'pending': null as any,
        'ok': [] as any[]
      };
      if (data.length === 0) {
        return null;
      }
      data.map(x => x.uploaded_at = x.uploaded_at.replace('T', ' '));
      let failed = data.filter(x => x.status  === 'FAILED');
      if (failed.length > 0) {
        failed.sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at));
        uploads.last_failed = failed[0];
      }
      uploads.ok = data.filter(x => x.status === 'OK');
      if (uploads.ok.length === 0) {
       let pending = data.filter(x => x.status  === 'PENDING');
       if (pending.length > 0) {
         failed.sort((a, b) => b.uploaded_at.localeCompare(a.uploaded_at));
         uploads.pending = pending[0];
       }
      }
      return uploads;
    })
    .catch((error) => {
      displayError(error);
      return null;
    });
  }

};
