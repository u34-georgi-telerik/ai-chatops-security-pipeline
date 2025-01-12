"""
app_test.py
This module contains unit tests for the Flask application defined in app.py.
"""

import unittest
from app import app


class TestApp(unittest.TestCase):
    """
    Unit test case for the Flask application.
    """

    def setUp(self):
        """
        Set up a test client for the Flask application.
        """
        self.client = app.test_client()

    def test_hello_world(self):
        """
        Test the '/' route to ensure it returns the correct response.
        """
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, b"Hello, World!")


if __name__ == "__main__":

    # Entry point for running the unit tests.

    unittest.main()
