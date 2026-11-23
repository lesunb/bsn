#!/usr/bin/python3

import unittest

class TestComponent(unittest.TestCase):
    def test_example(self):
        self.assertEqual(1, 1)
    def test2_example(self):
        self.assertEqual(3,3)

if __name__ == '__main__':
    unittest.main()
