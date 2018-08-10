import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

install_requires = (
    "requests",
    'click',
)

setup(
    name='pickture',
    version='0.0.1',
    packages=find_packages(HERE),
    install_requires=install_requires,
    url='https://github.com/winkidney/pickture',
    license='MIT',
    author='winkidney',
    author_email='winkidney@gmail.com',
    description='tools to download pictures you want',
)
