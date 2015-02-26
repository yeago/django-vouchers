#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django-vouchers',
    version="0.7",
    author='Federico Castro',
    author_email='fmc0208@gmail.com',
    description='Vouchers in Django',
    url='https://github.com/yeago/django-vouchers',
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Operating System :: OS Independent",
        "Topic :: Software Development"
    ],
)
