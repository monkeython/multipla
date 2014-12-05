import os
import sys

NAME = 'multipla'
PACKAGE = __import__(NAME)
AUTHOR, EMAIL = PACKAGE.__author__.rsplit(' ', 1)

with open('docs/index.rst', 'r') as INDEX:
    DESCRIPTION = INDEX.readline()

with open('README.rst', 'r') as README:
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
    'license': 'BSD',
    'keywords': PACKAGE.__keywords__,
    'py_modules': [NAME],
    'tests_require': ['genty'],
    'test_suite': 'test_{}'.format(NAME)
}

if __name__ == '__main__':
    import setuptools
    setuptools.setup(**EGG)
