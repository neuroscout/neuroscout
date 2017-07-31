type AnalysisStatus = 'DRAFT' | 'PENDING' | 'PASSED' | 'FAILED';

// Analysis type in Analysis Builder
export interface Analysis {
  analysisId: string | undefined;
  name: string;
  description: string;
  datasetId: number | null;  // ID of selected dataset
  runIds: string[];          // IDs of selected runs
  predictions: string;
  predictorIds: string[]; // IDs of selected predictors
  status: AnalysisStatus;
  private?: boolean;
  modifiedAt?: string;
  config: AnalysisConfig;
  transformations: Transformation[];
}

// Normalized dataset object  in Analysis Builder
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

export interface AnalysisConfig {
  smoothing: number;
  predictorConfigs: { [id: string]: PredictorConfig };
}

export interface PredictorConfig {
  convolution: 'Gamma' | 'Beta' | 'Alpha';
  temporalDerivative: boolean;
  orthogonalize: boolean;
}

interface BooleanParam {
  kind: 'boolean';
  name: string;
  value: boolean;
}

interface PredictorsParam {
  kind: 'predictors';
  name: string;
  value: string[];
}

export type Parameter = BooleanParam | PredictorsParam;

export type TransformName = 'standardize' | 'orthogonalize';

export interface Transformation {
  name: TransformName;
  inputs?: string[]; // predictor IDs
  parameters: Parameter[];
}

export interface XformRules {
  [name: string]: Transformation;
}

export interface Contrast {
  predictors: Predictor[];
  weights: number[];
  contrastType: 'T' | 'F';
}

export interface Store {
  activeTab: 'overview' | 'predictors' | 'transformations' | 'contrasts' | 'modeling' | 'review' | 'status';
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
  // Technically selectedPredictors is redundant because we're also storing Analysis.predictorIds
  // but store these separately for performance reasons
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
  predictions: string;
  status: AnalysisStatus;
  private?: boolean;
  dataset_id: number;
  runs?: { id: string }[];
  predictors?: { id: string }[];
  transformations?: Transformation[];
  config: AnalysisConfig;
  modified_at?: string;
}

export interface ApiUser {
  email: string;
  name: string;
  analyses: ApiAnalysis[];
}

export interface AppAnalysis {
  id: string;
  name: string;
  description: string;
  status: AnalysisStatus;
  modifiedAt?: string;
}