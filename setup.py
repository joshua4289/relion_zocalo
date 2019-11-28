#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from setuptools import setup, find_packages

requirements = ["workflows", "zocalo","schedule"]
setup_requirements = []


setup(
    author="Joshua Lobo",
    author_email="scientificsoftware@diamond.ac.uk",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Natural Language :: English",
    ],
    description="Zocalo runners for Relion",
    entry_points={
        "workflows.services": [
            "RelionRunner = relion_zo.consumers.zoc_relion_main_consumer:RelionRunner",
            "Relionstop = relion_zo.consumers.stop_relion_from_ispyb:Relionstop",
            "Relionsubmitstop = relion_zo.consumers.stop_relion_pipeline:Relionsubmitstop",
            "Relionfindgain = relion_zo.consumers.find_gain_by_session:Relionfindgain",
        ],
    },
    install_requires=requirements,
    license="BSD license",
    include_package_data=True,
    name="relion_zo",
    packages=find_packages(),
    python_requires='>=3.6.*',
    setup_requires=setup_requirements,
    version="1.1",
    zip_safe=False,
)

