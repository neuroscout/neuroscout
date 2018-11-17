/*
 Type definitinos for key models, such as analysis, run, predictor, contrast, transformation, etc.
 The data models below are largely UI agonstic. This module is a good starting point to understand the
 shape of the data in the frontend app. All resusable type definitions should go into this module.
*/
export type AnalysisStatus = 'DRAFT' | 'PENDING' | 'PASSED' | 'FAILED' | 'SUBMITTING';

// Analysis type in Analysis Builder
export interface Analysis {
  analysisId: string | undefined;
  name: string;
  description: string;
  datasetId: string | null; // ID of selected dataset
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
  autoContrast: boolean;
}

// Normalized dataset object in Analysis Builder
export interface Dataset {
  name: string;
  id: string;
  authors: string;
  url: string;
  description: string;
  tasks: Task[];
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
  url: string;
  summary: string;
  tasks: Task[];
}

export interface Run {
  id: string;
  number: string;
  session: string | null;
  subject: string | null;
  task: string;
}

export interface Task {
  id: string;
  name: string;
  description?: string;
  numRuns: number;
  summary?: string;
}

export interface Predictor {
  id: string;
  name: string;
  source: string | null;
  description: string | null;
  extracted_feature?: ExtractedFeature;
}

export interface ExtractedFeature {
  description: string;
  extractor_name: string;
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

export type TransformName = 'Scale' | 'Orthogonalize' | 'Sum' | 'Product' | 'Threshold'
  | 'Or' | 'And' | 'Not' | 'ConvolveHRF' | 'Replace';

export type BlockLevel = 'run' | 'session' | 'subject' | 'dataset';

export type ReplaceNA = 'before' | 'after' | undefined;

export interface Transformation {
  name: TransformName;
  replace_na?: ReplaceNA;
  input?: string[]; // predictor IDs
  output?: string[];
  demean?: boolean;
  rescale?: boolean;
  other?: string[];
  weights?: number[];
  threshold?: number;
  binarize?: boolean;
  above?: boolean;
  signed?: boolean;
  replace?: any;
}

// Lookup hash of available transformations (as specified in transforms.ts) by their name
export interface XformRules {
  [name: string]: Transformation;
}

export type TabName =
    | 'overview'
    | 'predictors'
    | 'transformations'
    | 'contrasts'
    | 'modeling'
    | 'review'
    | 'submit';

export interface Contrast {
  name: string;
  condition_list: string[];
  weights: number[];
  contrastType: 't' | 'F';
}

export interface Store {
  activeTab: TabName;
  predictorsActive: boolean;
  predictorsLoad: boolean;
  transformationsActive: boolean;
  contrastsActive: boolean;
  hrfActive: boolean;
  reviewActive: boolean;
  submitActive: boolean;
  modelingActive: boolean;
  analysis: Analysis;
  datasets: Dataset[];
  availableRuns: Run[];
  selectedTaskId: string | null;
  availablePredictors: Predictor[];
  // Technically selectedPredictors is redundant because we're also storing Analysis.predictorIds
  // but store these separately for performance reasons
  selectedPredictors: Predictor[];
  selectedHRFPredictors: Predictor[];
  unsavedChanges: boolean;
  currentLevel: BlockLevel;
  postReports: boolean;
  model: BidsModel;
  poll: boolean;
  saveFromUpdate: boolean;
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
  dataset_id: string;
  runs?: string[];
  predictors?: string[];
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
  task?: string;
  run?: number[];
  session?: string[];
  subject?: string[];
}

export interface Block {
  model?: BlockModel;
  transformations?: Transformation[];
  contrasts?: Contrast[];
  level: string;
  auto_contrasts?: boolean;
}

export interface BlockModel {
  variables: string[];
  HRF_variables?: string[];
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
  picture: string;
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

export interface AuthStoreState {
  jwt: string;
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  openReset: boolean;
  openEnterResetToken: boolean;
  loginError: string;
  signupError: string;
  resetError: string;
  email: string | undefined;
  name: string | undefined;
  password: string | undefined;
  token: string | null;
  loggingOut: boolean; // flag set on logout to know to redirect after logout
  nextURL: string | null; // will probably remove this and find a better solution to login redirects
  gAuth: any;
  avatar: string;
}
