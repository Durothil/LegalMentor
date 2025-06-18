from setuptools import setup, find_packages

setup(
    name="legalmentor",
    version="0.1.0",
    packages=find_packages(include=["core", "core.*"]),
)