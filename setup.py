#!/usr/bin/env python

from setuptools import setup, find_packages
import os

requires = [
    'asyncio',
    'aiohttp',
    'matplotlib',  # Optional for visualizations
    'networkx',    # Optional for visualizations
]

setup(
    name="telos",
    version="0.1.0",
    description="User Interface and Requirements Management for Tekton",
    author="Tekton Project",
    author_email="tekton@example.com",
    url="https://github.com/example/tekton",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    entry_points={
        'console_scripts': [
            'telos=telos.ui.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
