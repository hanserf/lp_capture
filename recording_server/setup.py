# import os
from setuptools import setup, find_packages

setup(
    name='lp_server',
    version='0.6.4',
    description='For capturing LP and other analog audio',
    author='S3RF',
    author_email='hanse.fjeld@gmail.com',
    packages=find_packages(),
    setup_requires=['wheel'],
    install_requires=['scipy', 'numpy', 'sounddevice','pysoundfile' ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'lp_server=app.server:main'
        ],
    }
)
