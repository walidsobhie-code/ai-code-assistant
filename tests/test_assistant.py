#!/usr/bin/env python3
"""Tests for AI Code Assistant"""
import unittest
import subprocess
import os

class TestAssistant(unittest.TestCase):
    
    def test_query_engine_exists(self):
        self.assertTrue(os.path.exists('query_engine.py'))
    
    def test_context_loader_exists(self):
        self.assertTrue(os.path.exists('context_loader.py'))

if __name__ == '__main__':
    unittest.main()
