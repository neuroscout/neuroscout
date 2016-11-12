import pytest
from models.dataset import Dataset
from models.analysis import Analysis
from models.auth import User
from models.predictor import Predictor
from models.extractor import Extractor
from models.stimulus import Stimulus

## Data population fixtures
@pytest.fixture(scope="function")
def add_datasets(session):
	dataset = Dataset(name='Fancy fMRI study', external_id = 'ds_32', 
		attributes = {'some' : 'attribute'})
	session.add(dataset)
	session.commit()

	dataset_2 = Dataset(name='Indiana Jones', external_id = 'ds_33')
	session.add(dataset_2)
	session.commit()

	return [dataset.id, dataset_2.id]

@pytest.fixture(scope="function")
def add_analyses(session, add_users, add_datasets):
	analysis = Analysis(dataset_id = add_datasets[0], user_id = add_users[0][0], 
		name = "My first fMRI analysis!", description = "Ground breaking")

	analysis_2 = Analysis(dataset_id = add_datasets[0], user_id = add_users[0][1],
		name = "fMRI is cool" , description = "Earth shattering")

	session.add(analysis)
	session.commit()

	session.add(analysis_2)
	session.commit()

	return [analysis.id, analysis_2.id]

@pytest.fixture(scope="function")
def add_extractor(session):
	extractor = Extractor(name="Google API", description="Deepest learning",
		version = 0.1)

	session.add(extractor)
	session.commit()

	return extractor.id

@pytest.fixture(scope="function")
def add_stimulus(session, add_datasets):
	stim = Stimulus(dataset_id = add_datasets[0])

	session.add(stim)
	session.commit()

	return stim.id

@pytest.fixture(scope="function")
def add_predictor(session, add_extractor, add_stimulus):
	predictor = Predictor(stimulus_id = add_stimulus, extractor_id = add_extractor)

	session.add(predictor)
	session.commit()

	return predictor.id

## Tests
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

	# Try cloning analysis


