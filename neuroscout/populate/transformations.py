"""" Custom transformations of extracted features """

class Preprocessing(object):
    """ Functions to be applied to a single extracted feature value """
    @staticmethod
    def double(val):
        return val * 2

class Postprocessing(object):
    """ Functions to be applied to a one or more values, creating a new feature """
    @staticmethod
    def product(col1, col2):
        return col1 * col2

    @staticmethod
    def num_faces(**facecols):
        pass
