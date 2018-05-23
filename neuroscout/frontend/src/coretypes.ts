/*
 Type definitinos for key models, such as analysis, run, predictor, contrast, transformation, etc.
 The data models below are largely UI agonstic. This module is a good starting point to understand the
 shape of the data in the frontend app. All resusable type definitions should go into this module.
*/
type AnalysisStatus = 'DRAFT' | 'PENDING' | 'PASSED' | 'FAILED';

// Analysis type in Analysis Builder
export interface Analysis {
  analysisId: string | undefined;
  name: string;
  description: string;
  datasetId: number | null; // ID of selected dataset
  runIds: string[]; // IDs of selected runs
  predictions: string;
  predictorIds: string[]; // IDs of selected predictors
  hrfPredictorIds: string[];
  status: AnalysisStatus;
  private?: boolean;
  modifiedAt?: string;
  config: AnalysisConfig;
  transformations: Transformation[];
  contrasts: Contrast[];
  model?: BidsModel;
}

// Normalized dataset object in Analysis Builder
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
  task: { id: string; name: string };
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

export type TransformName = 'scale' | 'orthogonalize';

export type BlockLevel = 'run' | 'session' | 'subject' | 'dataset';

export interface Transformation {
  name: TransformName;
  input?: string[]; // predictor IDs
  demean?: boolean;
  rescale?: boolean;
  wrt?: string[];
}
 
// Lookup hash of available transformations (as specified in transforms.ts) by their name
export interface XformRules {
  [name: string]: Transformation;
}

export interface Contrast {
  name: string;
  predictors: string[];
  weights: number[];
  contrastType: 't' | 'F';
}

export interface Store {
  activeTab:
    | 'overview'
    | 'predictors'
    | 'transformations'
    | 'contrasts'
    | 'modeling'
    | 'review'
    | 'status';
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
  selectedHRFPredictors: Predictor[];
  unsavedChanges: boolean;
  currentLevel: BlockLevel;
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

// Shape of Analysis object as consumed/produced by the backend API
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
  contrasts?: Contrast[];
  config: AnalysisConfig;
  modified_at?: string;
  model?: BidsModel;
}

export interface BidsModel {
  input?: ImageInput;
  blocks?: Block[] | never[];
  name?: string;
  description?: string;
}

export interface ImageInput {
  include?: InputType;
  exclude?: InputType;
}

export interface InputType {
  task?: string;
  run?: string[];
  session?: string[];
  subject?: string[];
}

export interface Block {
  model?: BlockModel;
  transformations?: Transformation[];
  contrasts?: Contrast[];
  level: string;
}

export interface BlockModel {
  variables: string[];
  hrf_variables?: string[];
}

export interface ModelContrast {
  name: string;
  predictors: string[];
  weights: number[];
  contrastType: 't' | 'F';
}

// Shape of User object as consumed/produced by the backend API
export interface ApiUser {
  email: string;
  name: string;
  analyses: ApiAnalysis[];
}

// The more condensed version of analysis object as returned by the user route
// and displayed as list of analyses on the homepage
export interface AppAnalysis {
  id: string;
  name: string;
  description: string;
  status: AnalysisStatus;
  modifiedAt?: string;
}
