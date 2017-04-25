export interface Analysis {
  analysisId: number | null;
  analysisName: string;
  analysisDescription: string;
  datasetId: number | null;
  runIds: string[];
  predictions: string;
}

export interface Dataset {
  name: string;
  id: number;
}

export interface Run {
  id: string;
  number: string;
  session: string | null;
  subject: string | null;
  task: string;
}

export interface Store {
  activeTab: 'overview' | 'predictors' | 'transformations' | 'contrasts' | 'modeling' | 'overview';
  predictorsActive: boolean;
  transformationsActive: boolean;
  analysis: Analysis;
  datasets: Dataset[];
  availableRuns: Run[];
}