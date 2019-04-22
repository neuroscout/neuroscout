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
  }
};
