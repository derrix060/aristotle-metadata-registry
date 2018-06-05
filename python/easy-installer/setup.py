import os
from setuptools import setup, find_packages

__version__ = '1.0.0'

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='easyinstaller',
    version=__version__,
    packages=['easy_installer'],
    include_package_data=True,
    license='Aristotle-MDR Modified BSD Licence',
    description='Easy Installer',
    long_description='Easy Installer',
    url='https://www.aristotlemetadata.com/cloud',
    zip_safe=False,
    entry_points={
        'console_scripts': ['aristotle-installer=easy_installer.install:main']
    },
    install_requires=[
        'requests'
    ]
)
