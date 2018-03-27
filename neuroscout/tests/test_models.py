import pytest
import os
from sqlalchemy import func
from models import (Analysis, User, Dataset, Predictor, Stimulus, Run,
					RunStimulus, Result, ExtractedFeature, PredictorEvent,
					GroupPredictor)

from numpy import isclose

def test_dataset_ingestion(session, add_task):
	dataset_model = Dataset.query.filter_by(id=add_task).one()

	# Test mimetypes
	assert 'image/jpeg' in dataset_model.mimetypes
	assert 'bidstest' == dataset_model.tasks[0].name

	# Try adding dataset without a name
	with pytest.raises(Exception) as excinfo:
		session.add(Dataset())
		session.commit()
	assert 'not-null constraint' in str(excinfo)
	session.rollback()

	# Test properties of Run
	assert Run.query.count() == dataset_model.runs.count() == 4
	run_model =  dataset_model.runs.filter_by(number='1', subject='01').first()
	assert run_model.dataset_id == dataset_model.id
	assert 'TaskName' in run_model.task.description
	assert run_model.task.description['RepetitionTime'] == 2.0

	assert run_model.func_path == 'sub-01/func/sub-01_task-bidstest_run-01_bold_space-MNI152NLin2009cAsym_preproc.nii.gz'

	# Test properties of first run's predictor events
	assert run_model.predictor_events.count() == 12
	assert Predictor.query.count() == dataset_model.predictors.count() == 3

	pred_names = [p.name for p in Predictor.query.all()]
	assert 'rt' in pred_names
	assert 'rating' in pred_names ## Derivative event

	predictor = Predictor.query.filter_by(name='rt').first()
	assert predictor.predictor_events.count() == 16
	assert predictor.source == 'events'

	# Test run summary statistics
	assert len(predictor.run_statistics) == 4
	assert predictor.run_statistics[0].mean == 167.25

	# Test predictor event
	predictor_event = predictor.predictor_events.first()
	assert predictor_event.value is not None
	assert predictor_event.onset is not None

	# Test that Stimiuli were extracted
	assert Stimulus.query.count() == 4

	# and that they were associated with runs (4 runs )
	assert RunStimulus.query.count() == \
		Stimulus.query.count() * Run.query.count() == 16

	# Test participants.tsv ingestion
	assert GroupPredictor.query.count() == 3
	assert GroupPredictor.query.filter_by(name='sex').count() == 1

	gpv = GroupPredictor.query.filter_by(name='sex').one().values
	assert gpv.count() == 4
	assert 'F' in [v.value for v in gpv]

@pytest.mark.skipif(os.environ.get("TRAVIS") == "true",
	reason="Skipping this test on Travis CI.")
def test_remote_dataset(session, add_task_remote):
	dataset_model = Dataset.query.filter_by(id=add_task_remote).one()

	# Test mimetypes
	assert 'image/jpeg' in dataset_model.mimetypes
	assert 'bidstest' == dataset_model.tasks[0].name

	# Test properties of Run
	assert Run.query.filter_by(dataset_id=add_task_remote).count() \
			== dataset_model.runs.count() == 1
	predictor = Predictor.query.filter_by(name='rt').first()
	assert predictor.predictor_events.count() == 4

	# Test that Stimiuli were extracted
	assert Stimulus.query.count() == 5

	# Test participants.tsv ingestion
	assert GroupPredictor.query.filter_by(
			dataset_id=add_task_remote).count() == 3

def test_json_local_dataset(session, add_local_task_json):
	dataset_model = Dataset.query.filter_by(id=add_local_task_json).one()

	# Test mimetypes
	assert 'image/jpeg' in dataset_model.mimetypes
	assert 'bidstest' == dataset_model.tasks[0].name

	# Test properties of Run
	assert Run.query.filter_by(dataset_id=add_local_task_json).count() \
			== dataset_model.runs.count() == 1
	predictor = Predictor.query.filter_by(name='rt').first()
	assert predictor.predictor_events.count() == 4

	# Test that Stimiuli were extracted
	assert Stimulus.query.count() == 5

	# Test participants.tsv ingestion
	assert GroupPredictor.query.filter_by(
			dataset_id=add_local_task_json).count() == 3

	# Test that stimuli were converted
	converted_stim = [s for s in Stimulus.query if s.parent_id is not None][0]
	assert converted_stim.converter_name == 'TesseractConverter'

	assert ExtractedFeature.query.filter_by(
		feature_name='Brightness').count() == 1

def test_local_update(update_local_json):
	assert update_local_json is not None
	assert ExtractedFeature.query.count() == 4

def test_extracted_features(session, add_task, extract_features):
	""" This tests feature extraction from a remote dataset"""
	assert ExtractedFeature.query.count() == 2

	extractor_names = [ee.extractor_name for ee in ExtractedFeature.query.all()]
	assert 'BrightnessExtractor' in extractor_names
	assert 'VibranceExtractor' in extractor_names

	ef_b = ExtractedFeature.query.filter_by(extractor_name='BrightnessExtractor').one()
	assert ef_b.extractor_version is not None
	assert ef_b.description == "Brightness of an image."

	# Check that the number of features extracted is the same as Stimuli
	assert ef_b.extracted_events.count() == Stimulus.query.count()

	# Check for sensical value
	assert isclose(float(session.query(func.max(PredictorEvent.value)).join(
		Predictor).filter_by(ef_id=ef_b.id).one()[0]), 0.88, 0.1)

	# And that a sensical onset was extracted
	assert session.query(func.max(PredictorEvent.onset)).join(
		Predictor).filter_by(ef_id=ef_b.id).one()[0] == 25.0

	# Test that Predictors were created from EF
	pred = Predictor.query.filter_by(ef_id=ef_b.id).one()
	assert pred.name == "Brightness"
	assert pred.source == "extracted"

	# Test that a Predictor was not made for vibrance (hidden)
	ef_v = ExtractedFeature.query.filter_by(
		extractor_name='VibranceExtractor').one()
	assert Predictor.query.filter_by(ef_id=ef_v.id).count() == 0

	# Test that vibrance's name was changed using regex
	assert ef_v.feature_name == "vib"
	assert ef_v.description == "vib of an image."

	# Test that sharpness was annotated regardless (even without entry)
	ef_v = ExtractedFeature.query.filter_by(
		extractor_name='SharpnessExtractor').count() == 1
def test_analysis(session, add_analysis, add_predictor):
	# Number of entries
	assert Analysis.query.count() == 1

	first_analysis = Analysis.query.first()
	assert User.query.filter_by(id=first_analysis.user_id).count() == 1

	# Add relationship to a predictor
	pred = Predictor.query.filter_by(id = add_predictor).one()
	first_analysis.predictors = [pred]
	session.commit()
	assert Predictor.query.filter_by(id = add_predictor).one().analysis[0].id \
		== first_analysis.id

	# Try adding analysis without a name
	with pytest.raises(Exception) as excinfo:
		session.add(Analysis())
		session.commit()
	assert 'not-null constraint' in str(excinfo)
	session.rollback()

	# Try cloning analysis
	user = User.query.filter_by(id=first_analysis.user_id).one()
	clone = first_analysis.clone(user)
	session.add(clone)
	session.commit()

	assert clone.id > first_analysis.id
	assert clone.name == first_analysis.name

def test_result(add_result):
	assert Result.query.count() == 1
