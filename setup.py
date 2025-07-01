#!/usr/bin/env python3
"""Setup script for keyword-serp-analyzer."""

from setuptools import setup, find_packages

with open("Readme.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="keyword-serp-analyzer",
    version="1.0.0",
    author="Liad Gez",
    description="Discover competitors by analyzing keyword search results",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/liadgez/keyword-serp-analyzer",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Topic :: Office/Business :: Financial :: Investment",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "keyword-analyzer=main:app",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="seo, competitor-analysis, serp, keywords, marketing",
)