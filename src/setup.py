import os

from setuptools import setup, find_packages, convert_path

HERE = os.path.abspath(os.path.dirname(__file__))


def get_version():
    ver_path = convert_path('picktrue/version.py')
    main_ns = {}

    with open(ver_path) as ver_file:
        exec(ver_file.read(), )
    return main_ns['__version__']


install_requires = (
    "requests",
    'click',
    'pixivpy',
    'PySocks',
    'flask',
)

setup(
    name='picktrue',
    version=get_version(),
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
