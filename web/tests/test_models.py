from app import app
from database import db
from models.dataset import Dataset
from models.analysis import Analysis
	
import pytest

from psycopg2 import IntegrityError

@pytest.fixture(scope="session")
def add_datasets():
	"""" Add test datasets """
	with app.app_context():
		dataset = Dataset(name='Fancy fMRI study', external_id = 'ds_32', 
			attributes = {'some' : 'attribute'})
		db.session.add(dataset)
		db.session.commit()

		dataset_2 = Dataset(name='Indiana Jones', external_id = 'ds_33')
		db.session.add(dataset_2)
		db.session.commit()

		return [dataset.id, dataset_2.id]

@pytest.fixture(scope="session")
def add_analyses():
	"""" Add test analyses """
	with app.app_context():
		analysis = Analysis(dataset_id = 1, user_id = 1, 
			name = "My first fMRI analysis!", description = "Ground breaking")

		analysis_2 = Analysis(dataset_id = 1, user_id = 2,
			name = "fMRI is cool" , description = "Earth shattering")

		db.session.add(analysis)
		db.session.commit()

		db.session.add(analysis_2)
		db.session.commit()

		return [analysis.id, analysis_2.id]

@pytest.mark.usefixtures("db_init_clean")
def test_dataset(add_users, add_datasets, add_analyses):
	with app.app_context():
		# Number of entries
		assert Dataset.query.count() == 2

		first_dataset = Dataset.query.first()

		# Datatypes of columns
		assert type(first_dataset.id) is int
		assert type(first_dataset.attributes) is dict
		assert type(first_dataset.name) is str
		assert type(first_dataset.external_id) is str

		# Relationship to Analyses
		assert first_dataset.analyses.count() == 2
		assert isinstance(first_dataset.analyses.first(), Analysis)

		# Try adding dataset without a name
		with pytest.raises(Exception) as excinfo:
			db.session.add(Dataset())
			db.session.commit()
		assert 'not-null constraint' in str(excinfo)
		db.session.rollback()

		# Try adding dataset with same external id as existing one
		with pytest.raises(Exception) as excinfo:
			db.session.add(Dataset(name="Test", 
				external_id=first_dataset.external_id))
			db.session.commit()
		assert 'unique constraint "dataset_external_id_key"' in str(excinfo)
		db.session.rollback()
