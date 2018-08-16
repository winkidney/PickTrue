import os

from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))

install_requires = (
    "requests",
    'click',
    'pixivpy',
    'PySocks',
)

setup(
    name='picktrue',
    version='0.3.1',
    packages=find_packages(HERE),
    install_requires=install_requires,
    url='https://github.com/winkidney/picktrue',
    license='MIT',
    author='winkidney',
    author_email='winkidney@gmail.com',
    description='tools to download pictures you want',
    entry_points = {
        'console_scripts': [
            'picktrue-cli=picktrue.__main__:main',
            'picktrue-gui=picktrue.gui.__main__:main',
        ]
    },
)
