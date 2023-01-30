from setuptools import find_packages
from setuptools import setup

setup(
    name = 'FIS_opentrons_tools',
    version = '0.1.0',
    packages=find_packages('tools'),
    package_dir={'':'tools'},
    author = 'Iván Bloise Sánchez',
    description= 'Functions and other tools for Opentrons protocols'
)