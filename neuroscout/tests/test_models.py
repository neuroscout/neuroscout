import pytest
from sqlalchemy import func
from ..models import (
    Analysis, User, Dataset, Predictor, Stimulus, Run, RunStimulus,
    ExtractedFeature, PredictorEvent, GroupPredictor, Task)

from numpy import isclose
from ..populate.convert import ingest_text_stimuli
from ..populate.modify import update_annotations


def test_dataset_ingestion(session, add_task):
    dataset_model = Dataset.query.filter_by(id=add_task).one()

    # Test mimetypes
    assert 'image/jpeg' in dataset_model.mimetypes
    assert 'bidstest' == dataset_model.tasks[0].name

    # Try adding dataset without a name
    with pytest.raises(Exception) as excinfo:
        session.add(Dataset())
        session.commit()
    session.rollback()

    # Test properties of Run
    assert Run.query.count() == len(dataset_model.runs) == 4
    run_model = [
        r for r in dataset_model.runs
        if r.subject == '01' and r.number == 1][0]
    assert run_model.dataset_id == dataset_model.id
    assert 'TaskName' in run_model.task.description
    assert run_model.task.description['RepetitionTime'] == 2.0

    # Test properties of first run's predictor events
    assert run_model.predictor_events.count() == 12
    assert Predictor.query.count() == dataset_model.predictors.count() == 3

    pred_names = [p.name for p in Predictor.query.all()]
    assert 'rt' in pred_names
    assert 'rating' in pred_names  # Derivative event

    predictor = Predictor.query.filter_by(name='rt').first()
    assert len(predictor.predictor_events) == 16
    assert predictor.source == 'events'
    assert predictor.original_name == 'reaction_time'

    # Test predictor event
    predictor_event = predictor.predictor_events[0]
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


def test_json_local_dataset(session, add_local_task_json):
    dataset_model = Dataset.query.filter_by(id=add_local_task_json).one()

    # Test mimetypes
    assert 'image/jpeg' in dataset_model.mimetypes
    assert 'bidstest' == dataset_model.tasks[0].name

    # Test properties of Run
    assert Run.query.filter_by(dataset_id=add_local_task_json).count() \
        == len(dataset_model.runs) == 1
    predictor = Predictor.query.filter_by(name='rt').first()
    assert len(predictor.predictor_events) == 4

    # Test that Stimiuli were extracted
    assert Stimulus.query.count() == 4

    # Test participants.tsv ingestion
    assert GroupPredictor.query.filter_by(
            dataset_id=add_local_task_json).count() == 3


def test_extracted_features(session, add_task, extract_features):
    """ This tests feature extraction from a remote dataset"""
    assert ExtractedFeature.query.count() == 2

    extractor_names = [ee.extractor_name
                       for ee in ExtractedFeature.query.all()]
    assert 'BrightnessExtractor' in extractor_names
    assert 'VibranceExtractor' in extractor_names

    ef_b = ExtractedFeature.query.filter_by(
        extractor_name='BrightnessExtractor').one()
    assert ef_b.extractor_version is not None
    assert ef_b.description == "Brightness of an image."

    # Check that the number of features extracted is the same as Stimuli
    assert len(ef_b.extracted_events) == Stimulus.query.count()

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
    pred = Predictor.query.filter_by(id=add_predictor).one()
    first_analysis.predictors = [pred]
    session.commit()
    assert Predictor.query.filter_by(id=add_predictor).one().analysis[0].id \
        == first_analysis.id

    # Try adding analysis without a name
    with pytest.raises(Exception) as excinfo:
        session.add(Analysis())
        session.commit()
    session.rollback()

    # Try cloning analysis
    user = User.query.filter_by(id=first_analysis.user_id).one()
    clone = first_analysis.clone(user)
    session.add(clone)
    session.commit()

    assert clone.id > first_analysis.id
    assert clone.name == first_analysis.name


def test_external_text(get_data_path, add_task):
    filename = (get_data_path / 'fake_transcript.csv').as_posix()

    dataset_model = Dataset.query.filter_by(id=add_task).one()
    ds_id = dataset_model.id
    task_name = Task.query.filter_by(dataset_id=add_task).one().name

    stim = [s
            for s in Stimulus.query.filter_by(dataset_id=ds_id).all()
            if 'obama' in s.path][0]

    ingest_text_stimuli(filename, dataset_model.name, task_name, stim.id,
                        transformer='FakeTextExtraction')

    data = [s for s in Stimulus.query.all() if s.content is not None]

    first_stim = [s for s in data if s.content == 'no'][0]

    assert len(data) == 3
    assert first_stim.run_stimuli.count() == 4
    assert 2.2 in [s.onset for s in first_stim.run_stimuli.all()]


def test_update_schema(session, add_task, extract_features):
    bright = ExtractedFeature.query.filter_by(
        feature_name='Brightness').one()
    bright.feature_name = 'whatever'
    session.commit()
    assert ExtractedFeature.query.filter_by(
        feature_name='whatever').count() == 1

    update_annotations(mode='features')

    assert ExtractedFeature.query.filter_by(
        feature_name='whatever').count() == 0
    bright = ExtractedFeature.query.filter_by(
        feature_name='Brightness').one()
    assert bright.feature_name == 'Brightness'
    assert bright.original_name == 'brightness'

    predictor = Predictor.query.filter_by(name='rt').first()
    predictor.name = 'REACTION_TIME'
    session.commit()

    assert Predictor.query.filter_by(name='REACTION_TIME').count() == 1

    update_annotations()

    assert Predictor.query.filter_by(name='REACTION_TIME').count() == 0
    predictor = Predictor.query.filter_by(name='rt').first()
    assert predictor.name == 'rt'
