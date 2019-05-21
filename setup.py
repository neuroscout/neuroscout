from setuptools import setup, find_packages

setup(
    name='neuroscout',
    version='0.4',
    packages=find_packages(),
    install_requires=['flask', 'flask-sqlalchemy'],
    description='Neuroscout web application.',
    url='https://github.com/neuroscout/neuroscout',
    author='UT Psychoinformatics Lab',
    author_email='delavega@utexas.edu',
    license='MIT'
)
