from setuptools import find_packages
from setuptools import setup

setup (
    name = 'Oppentrons-applications',
    version = '0.1.0',
    install_requires=['Opentrons-tools'],
    packages= find_packages('src'),
    package_dir={'':'src'},
    author = 'Iván Bloise Sánchez',
    description = 'Applications for develop a massive screening of EPC-carrier using opentrons OT-2'
)