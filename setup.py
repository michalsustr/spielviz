#!/usr/bin/env python3
#
# The purpose of this script is to enable uploading SpielViz to the Python
# Package Index, which can be easily done by doing:
#
#   python3 setup.py sdist upload
#
# See also:
# - https://packaging.python.org/distributing/
# - https://docs.python.org/3/distutils/packageindex.html
#

from setuptools import setup

setup(
    name='spielviz',
    version='0.0.1',
    author='Michal Sustr',
    author_email='michal.sustr@gmail.com',
    url='https://github.com/michalsustr/spielviz',
    description="SpielViz is an interactive viewer for OpenSpiel games",
    long_description="""
        SpielViz is an interactive viewer for OpenSpiel games.
        """,
    license="LGPL",

    packages=['spielviz'],
    entry_points=dict(gui_scripts=['spielviz=spielviz.__main__:main']),

    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
      'Development Status :: 1 - Planning',
      'Environment :: X11 Applications :: GTK',
      'Intended Audience :: Information Technology',
      'Operating System :: OS Independent',
      'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3 :: Only',
      'Topic :: Multimedia :: Graphics :: Viewers',
    ],

    install_requires=[
      'coloredlogs',
      'pyspiel',
      'chess',
      # This is true, but doesn't work realiably
      'gi',
      'gi-cairo'
    ],
)
