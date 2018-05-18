from setuptools import setup, find_packages
PACKAGES = find_packages()

setup(
    name='neuroscout',
    version='0.1',
    description='Neuroscout server.',
    url='https://github.com/PsychoinformaticsLab/neuroscout',
    author='UT Psychoinformatics Lab',
    author_email='delavega@utexas.edu',
    license='MIT',
    packages=PACKAGES
)
