""" Miscelanous tools """

from .. import models as ms


def distinct_extractors(count=True, active=True):
    """ Tool to count unique number of predictors for each Dataset/Task """
    active_datasets = ms.Dataset.query.filter_by(active=active)
    superset = set([v for (v, ) in ms.Predictor.query.filter_by(active=True).filter(
        ms.Predictor.dataset_id.in_(
            active_datasets.with_entities('id'))).join(
                ms.ExtractedFeature).distinct(
                    'extractor_name').values('extractor_name')])

    res = {}

    for en in superset:
        for ds in active_datasets:
            for t in ds.tasks:
                name = f"{ds.name}_{t.name}"
                if name not in res:
                    res[name] = {}
                preds = ms.Predictor.query.filter_by(
                    dataset_id=ds.id, active=True).join(
                        ms.ExtractedFeature).filter_by(
                            extractor_name=en).distinct('feature_name')
                if count:
                    r = preds.count()
                else:
                    r = list(preds.values('name'))
                res[name][en] = r

    return res
