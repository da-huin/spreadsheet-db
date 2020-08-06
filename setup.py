import io
from setuptools import find_packages, setup


# Read in the README for the long description on PyPI
def long_description():
    with io.open('README.md', 'r', encoding='utf-8') as f:
        readme = f.read()
    return readme

setup(name='spreadsheet_db',
      version='1.1',
      description='Simply use Google Spreadsheet as DB in Python.',
      long_description="Please refer to the https://github.com/dahuins/spreadsheet_db",
      long_description_content_type="text/markdown",
      url='https://github.com/dahuins/spreadsheet_db',
      download_url= 'https://github.com/dahuins/spreadsheet_db/archive/master.zip',
      author='dahuins',
      author_email='dahuin000@gmail.com',
      license='MIT',
      packages=find_packages(),
      classifiers=[
          'Programming Language :: Python :: 3',
    ]
)
