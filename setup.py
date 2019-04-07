from setuptools import setup
import os

requirements = []
with open(os.path.join(os.getcwd(), 'requirements.txt')) as f:
    requirements = f.read().splitlines()

version = '0.0.1'

readme = ''
with open('README.rst') as f:
    readme = f.read()

setup(name='coc.py',
      author='mathsman5133',
      url='https://github.com/mathsman5133/coc.py',
      version=version,
      license='MIT',
      description='A python wrapper for the Clash of Clans API',
      long_description=readme,
      long_description_content_type="text/x-rst",
      python_requires='>=3.5.3',
      install_requires=requirements,
      )