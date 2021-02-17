# Use this command for deploy.
#   python3 setup.py sdist bdist_wheel
#   python3 -m twine upload --skip-existing dist/*

import io
from setuptools import find_packages, setup

setup(name='spreadsheet_db',
      version='1.2.3',
      description='Simply use Google Spreadsheet as DB in Python.',
      long_description="Please refer to the https://github.com/da-huin/spreadsheet_db",
      long_description_content_type="text/markdown",
      url='https://github.com/da-huin/spreadsheet_db',
      download_url= 'https://github.com/da-huin/spreadsheet_db/archive/master.zip',
      author='JunYeong Park',
      author_email='dahuin000@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=["boto3", "pandas", "gspread", "oauth2client"],
      classifiers=[
          'Programming Language :: Python :: 3',
    ]
)
