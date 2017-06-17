export interface Analysis {
  analysisId: string | undefined;
  name: string;
  description: string;
  datasetId: number | null;  // ID of selected dataset
  runIds: string[];          // IDs of selected runs
  predictions: string;
  predictorIds: string[]; // IDs of selected predictors
  locked: boolean;
  private: boolean;
}

// Normalized dataset object 
export interface Dataset {
  name: string;
  id: string;
  authors: string;
  url: string;
  description: string;
}

export interface Run {
  id: string;
  number: string;
  session: string | null;
  subject: string | null;
  task: { id: string, name: string };
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  numRuns: number;
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
  availableTasks: Task[];
  availableRuns: Run[];
  selectedTaskId: string | null;
  availablePredictors: Predictor[];
  selectedPredictors: Predictor[];
  unsavedChanges: boolean;
}

// Dataset object as returned by /api/datasets
export interface ApiDataset {
  id: number;
  name: string;
  description: {
    Authors: string[];
    Description: string;
    URL: string;
  };
}

export interface ApiRun {
  id: string;
  number: string;
  session: string | null;
  subject: string | null;
}

export interface ApiAnalysis {
  hash_id?: string;
  name: string;
  description: string;
  locked: boolean;
  private: boolean;
  dataset_id: number;
  runs: { id: string }[];
  predictors: { id: string }[];
  transformations: object;
}

export interface ApiUser {
  email: string;
  name: string;
  analyses: { hash_id: string, name: string }[];
}