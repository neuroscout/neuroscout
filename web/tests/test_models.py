import pytest
from models import (Analysis, User, Dataset, Predictor, Extractor, Stimulus,
					Result, ExtractedFeature, ExtractedEvent)

#### Tests
def test_dataset(session, add_analyses):
	# Number of entries
	assert Dataset.query.count() == 2

	first_dataset = Dataset.query.first()

	# Relationship to Analyses
	assert first_dataset.analyses.count() == 2
	assert isinstance(first_dataset.analyses.first(), Analysis)

	# Try adding dataset without a name
	with pytest.raises(Exception) as excinfo:
		session.add(Dataset())
		session.commit()
	assert 'not-null constraint' in str(excinfo)
	session.rollback()

	# Try adding dataset with same external id as existing one
	with pytest.raises(Exception) as excinfo:
		session.add(Dataset(name="Test",
			external_id=first_dataset.external_id))
		session.commit()
	assert 'unique constraint "dataset_external_id_key"' in str(excinfo)

def test_analysis(session, add_analyses, add_predictor):
	# Number of entries
	assert Analysis.query.count() == 2

	first_analysis = Analysis.query.first()
	assert User.query.filter_by(id=first_analysis.user_id).count() == 1

	# Add relationship to a predictor
	pred = Predictor.query.filter_by(id = add_predictor).one()
	first_analysis.predictors = [pred]
	session.commit()
	assert Predictor.query.filter_by(id = add_predictor).one().analysis_id \
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

def test_extractor(session, add_extractor, add_predictor):
	assert Extractor.query.count() == 1

	extractor = Extractor.query.first()

	# Add more stuff here


def test_predictor(session, add_predictor):
	assert Predictor.query.count() == 1

	predictor = Predictor.query.first()

def test_features(add_extracted_event):
	assert ExtractedEvent.query.filter_by(id=add_extracted_event).count() == 1

	ev = ExtractedEvent.query.filter_by(id=add_extracted_event).first()
	assert ExtractedFeature.query.filter_by(id=ev.extracted_feature_id).count() == 1


def test_stimulus(session, add_stimulus, add_predictor):
	assert Stimulus.query.count() == 1

	stim = Stimulus.query.first()

def test_result(add_result):
	assert Result.query.count() == 1
