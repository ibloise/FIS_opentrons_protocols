from setuptools import find_packages
from setuptools import setup

setup(
    name = 'Opentrons-tools',
    version = '1.0.0',
    packages=find_packages('src'),
    packages_dir={'':'src'},
    author = 'Iván Bloise Sánchez',
    description= 'Functions and other tools for Opentrons protocols'
)