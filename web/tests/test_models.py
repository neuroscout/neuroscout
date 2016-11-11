import pytest
from models.dataset import Dataset
from models.analysis import Analysis

@pytest.fixture(scope="function")
def add_datasets(session):
	"""" Add test datasets """
	dataset = Dataset(name='Fancy fMRI study', external_id = 'ds_32', 
		attributes = {'some' : 'attribute'})
	session.add(dataset)
	session.commit()

	dataset_2 = Dataset(name='Indiana Jones', external_id = 'ds_33')
	session.add(dataset_2)
	session.commit()

	return [dataset.id, dataset_2.id]

@pytest.fixture(scope="function")
def add_analyses(session):
	"""" Add test analyses """
	analysis = Analysis(dataset_id = 1, user_id = 1, 
		name = "My first fMRI analysis!", description = "Ground breaking")

	analysis_2 = Analysis(dataset_id = 1, user_id = 2,
		name = "fMRI is cool" , description = "Earth shattering")

	session.add(analysis)
	session.commit()

	session.add(analysis_2)
	session.commit()

	return [analysis.id, analysis_2.id]

def test_dataset(session, add_users, add_datasets, add_analyses):
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
	session.rollback()


# @pytest.mark.usefixtures("db_init_clean")
# def test_analysis(add_users, add_datasets, add_analyses):
# 		assert Analysis.query.count() == 2
# 		first_analysis = Analysis.query.first()

