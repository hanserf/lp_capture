# import os
from setuptools import setup, find_packages

setup(
    name='lp_capture',
    version='0.6.6',
    description='For capturing LP and other analog audio',
    author='S3RF',
    author_email='hanse.fjeld@gmail.com',
    packages=find_packages(),
    setup_requires=['wheel'],
    install_requires=['scipy', 'numpy', 'sounddevice','pysoundfile', 'pyzmq', 'PyQt5==5.9.2','pyqtgraph' ],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'lp_capture=app.main:main'
        ],
    }
)
