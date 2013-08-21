#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='gae-envaya',
    version='0.0.1',
    description='Tiny webapp envaya utility',
    author='Mitchel Kelonye',
    author_email='kelonyemitchel@gmail.com',
    url='https://github.com/kelonye/gae-envaya',
    packages=['gae_envaya',],
    package_dir = {'gae_envaya': 'lib'},
    license='MIT License',
    zip_safe=True
)