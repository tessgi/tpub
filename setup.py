#!/usr/bin/env python
from setuptools import setup


# PyPi requires reStructuredText instead of Markdown,
# so we convert our Markdown README for the long description
try:
   import pypandoc
   long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
   long_description = open('README.md').read()

# Command-line tools
entry_points = {'console_scripts': [
    'tpub = tpub:tpub',
    'tpub-update = tpub:tpub_update',
    'tpub-add = tpub:tpub_add',
    'tpub-delete = tpub:tpub_delete',
    'tpub-import = tpub:tpub_import',
    'tpub-export = tpub:tpub_export',
    'tpub-plot = tpub:tpub_plot',
    'tpub-spreadsheet = tpub:tpub_spreadsheet'
]}

setup(name='tpub',
      version='1.1.0',
      description="A simple tool to keep track of the publications related "
                  "to NASA's TESS mission.",
      long_description=long_description,
      author='Tom Barclay',
      author_email='tom@tombarclay.com',
      license='MIT',
      url='',
      packages=['tpub'],
      data_files=[('tpub/templates', ['tpub/templates/template.md', 'tpub/templates/template-overview.md'])],
      install_requires=["jinja2",
                        "six",
                        "astropy",
                        "ads",
                        "tqdm"],
      entry_points=entry_points,
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Intended Audience :: Science/Research",
          "Topic :: Scientific/Engineering :: Astronomy",
          ],
      )
