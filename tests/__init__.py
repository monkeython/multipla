import unittest

from tests import test_pluggable_package

suite = unittest.TestSuite()
loader = unittest.defaultTestLoader
suite.addTest(loader.loadTestsFromModule(test_pluggable_package))

