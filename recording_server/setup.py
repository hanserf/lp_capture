# import os
from setuptools import setup, find_packages

setup(
    name='lp_server',
    version='0.3.3',
    description='Server for Capturing Audio and streaming it to a client',
    author='S3RF,hanse.fjeld@gmail.com',
    author_email='hans.erik.fjeld@embida.no',
    packages=find_packages(),
    setup_requires=['wheel'],
    install_requires=['sounddevice','pyaudio','pyFiglet' ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'lp_server=server.main:main'
        ],
    }
)