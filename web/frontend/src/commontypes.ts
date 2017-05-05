export interface Analysis {
  analysisId: number | null;
  analysisName: string;
  analysisDescription: string;
  datasetId: number | null;
  runIds: string[];          // IDs of selected runs
  predictions: string; 
  predictorIds: Predictor[]; // IDs of selected predictors
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

export interface Predictor {
  id: string;
  name: string;
  description: string | null;
}

export interface Store {
  activeTab: 'overview' | 'predictors' | 'transformations' | 'contrasts' | 'modeling' | 'overview';
  predictorsActive: boolean;
  transformationsActive: boolean;
  contrastsActive: boolean;
  modelingActive: boolean;
  reviewActive: boolean;
  analysis: Analysis;
  datasets: Dataset[];
  availableRuns: Run[];
  availablePredictors: Predictor[];
}