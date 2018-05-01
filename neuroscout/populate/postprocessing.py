"""" Custom transformations of extracted features """

class Postprocessing(object):
    """ Functions applied to one or more ExtractedFeatures """
    @staticmethod
    def product(col1, col2):
        return col1 * col2

    @staticmethod
    def num_objects(ef):
        """ Counts the number of non zero objects """
        pass
