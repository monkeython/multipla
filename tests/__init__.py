import unittest

from tests import test_multipla

suite = unittest.TestSuite()
loader = unittest.defaultTestLoader
suite.addTest(loader.loadTestsFromModule(test_multipla))

