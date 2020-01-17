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
  dummyContrast: boolean;
}

// Normalized dataset object in Analysis Builder
export interface Dataset {
  name: string;
  id: string;
  authors: string[];
  url: string;
  description: string;
  tasks: Task[];
  active: boolean;
  modality: string;
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
  active: boolean;
  mimetypes: string[];
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
  private: boolean;
  dataset_id?: number;
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

export type TransformName = 'Scale' | 'Orthogonalize' | 'Threshold'
  | 'Or' | 'And' | 'Not' | 'Convolve';

export type StepLevel = 'Run' | 'Session' | 'Subject' | 'Dataset';

export type ReplaceNA = 'before' | 'after' | undefined;

export interface Transformation {
  Name: TransformName;
  ReplaceNA?: ReplaceNA;
  Input?: string[]; // predictor IDs
  Output?: string[];
  Demean?: boolean;
  Rescale?: boolean;
  Other?: string[];
  Weights?: number[];
  Threshold?: number;
  Binarize?: boolean;
  Above?: boolean;
  Signed?: boolean;
  Replace?: any;
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

export type ContrastTypeEnum = 't' | 'F';

export interface Contrast {
  Name: string;
  ConditionList: string[];
  Weights: number[];
  ContrastType: ContrastTypeEnum;
}

export interface Store {
  activeTab: TabName;
  predictorsActive: boolean;
  predictorsLoad: boolean;
  loadInitialPredictors: boolean;
  transformationsActive: boolean;
  contrastsActive: boolean;
  hrfActive: boolean;
  reviewActive: boolean;
  submitActive: boolean;
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
  currentLevel: StepLevel;
  postReports: boolean;
  model: BidsModel;
  poll: boolean;
  saveFromUpdate: boolean;
  activeXform?: Transformation;
  activeXformIndex: number;
  activeContrast?: Contrast;
  activeContrastIndex: number;
  xformErrors: string[];
  contrastErrors: string[];
  fillAnalysis: boolean;
  analysis404: boolean;
  doTooltip: boolean;
  auth?: AuthStoreState;
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
  Input?: ImageInput;
  Steps?: Step[] | never[];
  Name?: string;
  Description?: string;
}

export interface ImageInput {
  Task?: string;
  Run?: number[];
  Session?: string[];
  Subject?: string[];
}

export interface Step {
  Model?: StepModel;
  Transformations?: Transformation[];
  Contrasts?: Contrast[];
  Level: string;
  DummyContrasts?: object;
}

export interface StepModel {
  X: string[];
  HRF_X?: string[];
}

export interface ModelContrast {
  Name: string;
  Predictors: string[];
  Weights: number[];
  ContrastType: 't' | 'F';
}

export interface PredictorCollection {
  id: string;
  uploaded_at?: string;
  status?: string;
  traceback?: string;
  collection_name: string;
  // predictors?: {id: string, name: string}[];
  predictors?: Predictor[];
}

// Shape of User object as consumed/produced by the backend API
export interface ApiUser {
  email: string;
  name: string;
  picture: string;
  analyses: ApiAnalysis[];
  predictor_collections: PredictorCollection[];
  first_login: boolean;
}

// The more condensed version of analysis object as returned by the user route
// and displayed as list of analyses on the homepage
export interface AppAnalysis {
  id: string;
  name: string;
  description: string;
  status: AnalysisStatus;
  datasetName?: string;
  modifiedAt?: string;
}

export interface AuthStoreState {
  jwt: string;
  loggedIn: boolean;
  openLogin: boolean;
  openSignup: boolean;
  openReset: boolean;
  openEnterResetToken: boolean;
  openTour: boolean;
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
  predictorCollections: PredictorCollection[];
}

export interface AppState {
  loadAnalyses: () => void;
  analyses: AppAnalysis[]; // List of analyses belonging to the user
  publicAnalyses: AppAnalysis[]; // List of public analyses
  auth: AuthStoreState;
  datasets: Dataset[];
  cloneAnalysis: (number) => void;
  onDelete:  (analysis: AppAnalysis) => void;
}

export interface RunFilters {
  numbers: string[];
  subjects: string[];
  sessions: string[];
}

// shape of objects returned by api/analyses/{id}/uploads
export interface ApiUpload {
  collection_id: number;
  uploaded_at: string;
  files: [{level: string, status: string, traceback: (null | string)}];
}
