"""
python setup.py bdist_egg
"""
import os
import sys

WD = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, WD)

NAME = 'multipla'
PACKAGE = __import__(NAME)
AUTHOR, EMAIL = PACKAGE.__author__.rsplit(' ', 1)

DESCRIPTION = "A micro plugin framework."
with open(os.path.join(WD, 'README.rst'), 'r') as README:
    LONG_DESCRIPTION = README.read()

URL = 'https://github.com/monkeython/%s' % NAME

EGG = {
    'name': NAME,
    'version': PACKAGE.__version__,
    'author': AUTHOR,
    'author_email': EMAIL.strip('<>'),
    'url': URL,
    'description': DESCRIPTION,
    'long_description': LONG_DESCRIPTION,
    'classifiers': PACKAGE.__classifiers__,
    'keywords': PACKAGE.__keywords__,
    'py_modules': [NAME],
    'test_suite': 'tests.suite'
}

if __name__ == '__main__':
    import setuptools
    setuptools.setup(**EGG)
