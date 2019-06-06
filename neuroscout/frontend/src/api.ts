/*
  calls against the python api may be put in here to help centralize which routes are being called.
 */
import { displayError, jwtFetch } from './utils';
import {
  ApiDataset,
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

export const api = {
  getDatasets:  (active_only = true): Promise<Dataset[]> => {
    return jwtFetch(domainRoot + `/api/datasets?active_only=${active_only}`)
    .then(data => {
      const datasets: Dataset[] = data.map(d => normalizeDataset(d));
      return datasets;
    })
    .catch((error) => {
      displayError(error);
      return [] as Dataset[];
    });
  },
  getDataset: (datasetId: (number | string)): Promise<(Dataset | null)> => {
    return jwtFetch(domainRoot + `/api/datasets/${datasetId}`)
    .then(data => {
      return normalizeDataset(data);
    })
    .catch((error) => {
      displayError(error);
      return null;
    });
  },
  getNVUploads: (analysisId: (string)): Promise<(any | null)> => {
    return jwtFetch(domainRoot + `/api/analyses/${analysisId}/upload`)
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
