#!/usr/bin/env python3
with open("README.md", "r") as fp:
    long_description = fp.read()

from setuptools import setup, find_packages
setup(
    name="emuparadise-dl",
    version="0.2.1",
    packages=['emuparadise_dl'],
    scripts=['bin/emuparadise-dl'],

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=[
        'requests',
        'bs4',
        'termcolor',
        ],

    # metadata to display on PyPI
    author="Andrea Grazioso (ray)",
    author_email="grazioandre@gmail.com",
    description="Search and Download from rom hosting websites",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    keywords="rom emulators retrogaming",
    url="https://github.com/r4yan2/emuparadise-dl",   # project home page, if any
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        ]
)
