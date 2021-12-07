/*
 Type definitinos for key models, such as analysis, run, predictor, contrast, transformation, etc.
 The data models below are largely UI agonstic. This module is a good starting point to understand the
 shape of the data in the frontend app. All resusable type definitions should go into this module.
*/
import { UserStore } from './user'

export type AnalysisStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'PASSED'
  | 'FAILED'
  | 'SUBMITTING'

// Analysis type in Analysis Builder
export interface Analysis {
  analysisId: string | undefined
  name: string
  description: string
  datasetId: string | null // ID of selected dataset
  runIds: string[] // IDs of selected runs
  predictions: string
  predictorIds: string[] // IDs of selected predictors
  hrfPredictorIds: string[]
  status: AnalysisStatus
  private?: boolean
  created_at?: string
  modified_at?: string
  config: AnalysisConfig
  transformations: Transformation[]
  contrasts: Contrast[]
  model?: BidsModel
  dummyContrast: boolean
  user_name?: string
}

// Normalized dataset object in Analysis Builder
export interface Dataset {
  name: string
  id: string
  authors: string[]
  url: string
  summary: string
  longDescription?: string
  tasks: Task[]
  active: boolean
  modality: string
  meanAge?: number
  percentFemale?: number
}

// Dataset object as returned by /api/datasets
export interface ApiDataset {
  id: number
  name: string
  description: {
    Authors: string[]
    Description: string
    URL: string
  }
  url: string
  long_description?: string
  summary: string
  tasks: Task[]
  active: boolean
  mimetypes: string[]
  mean_age?: number
  percent_female?: number
}

export interface Run {
  id: string
  number: string
  session: string | null
  subject: string | null
  task: string
}

export interface Task {
  id: string
  name: string
  description?: string
  numRuns: number
  summary?: string
  n_subjects?: number
  n_runs_subject?: number
  avg_run_duration?: number
  TR?: number
}

export interface Predictor {
  id: string
  name: string
  source: string | null
  description: string | null
  extracted_feature?: ExtractedFeature
  private: boolean
  dataset_id?: number
}

export interface ExtractedFeature {
  id?: number
  resample_frequency: number
  description: string
  extractor_name: string
  modality: string
}

export interface PredictorConfig {
  convolution: 'Gamma' | 'Beta' | 'Alpha'
  temporalDerivative: boolean
  orthogonalize: boolean
}

interface PredictorConfigs {
  [id: string]: PredictorConfig
}

export interface AnalysisConfig {
  smoothing: number
  predictorConfigs: PredictorConfigs
}

interface BooleanParam {
  kind: 'boolean'
  name: string
  value: boolean
}

interface PredictorsParam {
  kind: 'predictors'
  name: string
  value: string[]
}

export type Parameter = BooleanParam | PredictorsParam

export type TransformName = 'Scale' | 'Orthogonalize' | 'Threshold' | 'Convolve'

export type StepLevel = 'Run' | 'Session' | 'Subject' | 'Dataset'

export type ReplaceNA = 'before' | 'after' | undefined

export interface Transformation {
  Name: TransformName
  ReplaceNA?: ReplaceNA
  Input?: string[] // predictor IDs
  Output?: string[]
  Demean?: boolean
  Rescale?: boolean
  Other?: string[]
  Weights?: number[]
  Threshold?: number
  Binarize?: boolean
  Above?: boolean
  Signed?: boolean
}

// Lookup hash of available transformations (as specified in transforms.ts) by their name
export interface XformRules {
  [name: string]: Transformation
}

export type TabName =
  | 'overview'
  | 'predictors'
  | 'transformations'
  | 'contrasts'
  | 'modeling'
  | 'review'
  | 'submit'
  | 'summary'

export type ContrastTypeEnum = 't' | 'F'

export interface Contrast {
  Name: string
  ConditionList: string[]
  Weights: number[]
  Type: ContrastTypeEnum
}

export interface Store {
  activeTab: TabName
  predictorsActive: boolean
  predictorsLoad: boolean
  loadInitialPredictors: boolean
  transformationsActive: boolean
  contrastsActive: boolean
  hrfActive: boolean
  reviewActive: boolean
  submitActive: boolean
  analysis: Analysis
  datasets: Dataset[]
  availableRuns: Run[]
  selectedTaskId: string | null
  availablePredictors: Predictor[]
  // Technically selectedPredictors is redundant because we're also storing Analysis.predictorIds
  // but store these separately for performance reasons
  selectedPredictors: Predictor[]
  selectedHRFPredictors: Predictor[]
  unsavedChanges: boolean
  currentLevel: StepLevel
  postReports: boolean
  model: BidsModel
  poll: boolean
  saveFromUpdate: boolean
  activeXform?: Transformation
  activeXformIndex: number
  activeContrast?: Contrast
  activeContrastIndex: number
  xformErrors: string[]
  contrastErrors: string[]
  fillAnalysis: boolean
  analysis404: boolean
  doTooltip: boolean
  user?: UserStore
  extractorDescriptions: ExtractorDescriptions
  loadingAnalysis: boolean
}

export interface ApiRun {
  id: string
  number: string
  session: string | null
  subject: string | null
}

// Shape of Analysis object as consumed/produced by the backend API
export interface ApiAnalysis {
  hash_id?: string
  name: string
  description: string
  predictions: string
  status: AnalysisStatus
  private?: boolean
  dataset_id: string
  runs?: string[]
  predictors?: string[]
  transformations?: Transformation[]
  contrasts?: Contrast[]
  config: AnalysisConfig
  created_at?: string
  modified_at?: string
  model?: BidsModel
  user?: string
  nv_count?: number
}

export interface BidsModel {
  Input?: ImageInput
  Steps?: Step[] | never[]
  Name?: string
  Description?: string
}

export interface ImageInput {
  Task?: string
  Run?: number[]
  Session?: string[]
  Subject?: string[]
}

export interface DummyContrasts {
  Type: string
}

export interface Step {
  Model?: StepModel
  Transformations?: Transformation[]
  Contrasts?: Contrast[]
  Level: string
  DummyContrasts?: DummyContrasts
}

export interface StepModel {
  X: string[]
  HRF_X?: string[]
}

export interface ModelContrast {
  Name: string
  Predictors: string[]
  Weights: number[]
  Type: 't' | 'F'
}

export interface PredictorCollection {
  id: string
  uploaded_at?: string
  status?: string
  traceback?: string
  collection_name: string
  // predictors?: {id: string, name: string}[];
  predictors?: Predictor[]
}

// The more condensed version of analysis object as returned by the user route
// and displayed as list of analyses on the homepage
export interface AppAnalysis {
  id: string
  name: string
  description: string
  status: AnalysisStatus
  dataset_id?: string
  created_at?: string
  modified_at?: string
  user_name?: string
  dataset_name: string
  nv_count?: number
}

export const profileEditItems = [
  'name',
  'user_name',
  'institution',
  'orcid',
  'bio',
  'twitter_handle',
  'personal_site',
  'public_email',
  'picture',
]

export interface User {
  id: number
  name: string
  user_name: string
  email: string
  institution: string
  orcid: string
  bio: string
  twitter_handle: string
  personal_site: string
  public_email: string
  picture: string
}

export interface ProfileState extends User {
  update: (updates: Partial<ProfileState>, updateLocal?: boolean) => void
}

// Shape of User object as consumed/produced by the backend API
export interface ApiUser extends User {
  analyses?: AppAnalysis[]
  predictor_collections: PredictorCollection[]
  first_login: boolean
}
export interface AppState {
  loadAnalyses: () => void
  analyses: AppAnalysis[] | null // List of analyses belonging to the user
  publicAnalyses: AppAnalysis[] | null // List of public analyses
  user: UserStore
  datasets: Dataset[]
  cloneAnalysis: (number) => Promise<string>
  onDelete: (analysis: AppAnalysis) => void
}

export interface RunFilters {
  numbers: string[]
  subjects: string[]
  sessions: string[]
}

// shape of objects returned by api/analyses/{id}/uploads
export interface ApiUpload {
  collection_id: number
  uploaded_at: string
  estimator: string | null
  fmriprep_version: string | null
  cli_version: string | null
  files: [{ level: string; status: string; traceback: null | string }]
}

export interface NvUploads {
  api_upload: ApiUpload
  uploaded_at: string
  estimator: string | null
  fmriprep_version: string | null
  cli_version: string | null
  files: [{ level: string; status: string; traceback: null | string }]
  failed: number
  pending: number
  ok: number
  total: number
  id: number
  tracebacks: (string | null)[]
}

export interface ApiExtractorDescription {
  description: string
  name: string
}

export interface ExtractorDescriptions {
  [key: string]: string
}

export interface AnalysisResources {
  preproc_address: string
  dataset_address: string
  dataset_name: string
  predictors: Predictor[]
}

export type UpdateBuilderStateValue = (value: Store[keyof Store]) => void

export type UpdateBuilderState = (
  attrName: keyof Store,
  keepClean?: boolean,
  saveToAPI?: boolean,
) => UpdateBuilderStateValue
