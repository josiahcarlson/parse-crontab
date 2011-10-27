#!/usr/bin/env python

from distutils.core import setup

with open('README') as f:
    long_description = f.read()

setup(
    name='crontab',
    version='.11',
    description='Parse and use crontab schedules in Python',
    author='Josiah Carlson',
    author_email='josiah.carlson@gmail.com',
    url='https://github.com/josiahcarlson/parse-crontab',
    packages=['crontab', 'tests'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Programming Language :: Python',
    ],
    license='GNU LGPL v2.1',
    long_description=long_description,
)
