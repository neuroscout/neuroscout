import pytest
from models import (Analysis, User, Dataset, Predictor, Stimulus, Run,
					RunStimulus, Result, ExtractedFeature,
					GroupPredictor, GroupPredictorValue)

def test_dataset_ingestion(session, add_dataset):
	# Number of entries
	assert Dataset.query.count() == 1
	dataset_model = Dataset.query.filter_by(id=add_dataset).one()

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
	run_model =  dataset_model.runs.first()
	assert run_model.dataset_id == dataset_model.id
	assert 'TaskName' in run_model.task.description
	assert run_model.task.description['RepetitionTime'] == 2.0

	assert run_model.duration is None
	assert run_model.path is None

	# Test properties of first run's predictor events
	assert run_model.predictor_events.count() == 8
	assert Predictor.query.count() == dataset_model.predictors.count() == 2

	assert 'rt' in [p.name for p in Predictor.query.all()]

	predictor = Predictor.query.filter_by(name='rt').first()
	assert predictor.predictor_events.count() == 16

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
	assert RunStimulus.query.count() == Stimulus.query.count() * Run.query.count() == 16

	# Test participants.tsv ingestion
	assert GroupPredictor.query.count() == 3
	assert GroupPredictor.query.filter_by(name='sex').count() == 1

	gpv = GroupPredictor.query.filter_by(name='sex').one().values
	assert gpv.count() == 2
	assert 'F' in [v.value for v in gpv]


def test_extracted_features(extract_features):
	assert ExtractedFeature.query.count() == 2

	extractor_names = [ee.extractor_name for ee in ExtractedFeature.query.all()]
	assert ['BrightnessExtractor', 'VibranceExtractor'] == extractor_names

	ef = ExtractedFeature.query.first()
	# Check that the number of features extracted is the same as Stimuli
	assert ef.extracted_events.count() == Stimulus.query.count()

	# And that a sensical value was extracted
	assert ef.extracted_events.first().value < 1

	# Test that Predictors were created from EF
	pred = Predictor.query.filter_by(ef_id=ef.id).one()
	assert pred.predictor_events.first().onset == 1.0

	# Add a test checking that values correspond from Predictors to EFs?


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
	clone = first_analysis.clone()
	session.add(clone)
	session.commit()

	assert clone.id > first_analysis.id
	assert clone.name == first_analysis.name

def test_result(add_result):
	assert Result.query.count() == 1
