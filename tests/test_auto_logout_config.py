import os
import unittest
from flask import current_app
from app import create_app, db
from flask_testing import TestCase

class AutoLogoutTestCase(TestCase):
    def create_app(self):
        # Use a separate test configuration
        os.environ['AUTO_LOGOUT_TIME'] = '10'
        os.environ['WARNING_TIME'] = '5'
        os.environ['TIME'] = 'SECONDS'
        app = create_app('testing')
        return app
        
    def setUp(self):
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        
    def test_auto_logout_config(self):
        """Test that the auto logout configuration is properly loaded from .env"""
        self.assertEqual(current_app.config['AUTO_LOGOUT_TIME'], 10)
        self.assertEqual(current_app.config['WARNING_TIME'], 5)
        self.assertEqual(current_app.config['TIME_UNIT'], 'SECONDS')
        
    def test_session_settings_endpoint(self):
        """Test that the session settings endpoint returns the correct values"""
        response = self.client.get('/api/v1/auth/session-settings')
        self.assertEqual(response.status_code, 200)
        
        data = response.json
        
        # With TIME=SECONDS, 10 seconds should be 10,000 milliseconds
        self.assertEqual(data['auto_logout_time'], 10000)
        self.assertEqual(data['warning_time'], 5000)
        self.assertEqual(data['time_unit'], 'SECONDS')
        
        # Minutes should be correctly calculated
        self.assertAlmostEqual(data['auto_logout_minutes'], 10/60, delta=0.01)
        self.assertAlmostEqual(data['warning_minutes'], 5/60, delta=0.01)
        
    def test_minutes_conversion(self):
        """Test conversion from minutes to milliseconds"""
        # Change environment to use minutes
        os.environ['TIME'] = 'MINUTES'
        os.environ['AUTO_LOGOUT_TIME'] = '2'
        os.environ['WARNING_TIME'] = '1'
        
        # Force refresh of config
        self.app.config['TIME_UNIT'] = 'MINUTES'
        self.app.config['AUTO_LOGOUT_TIME'] = 2
        self.app.config['WARNING_TIME'] = 1
        
        response = self.client.get('/api/v1/auth/session-settings')
        self.assertEqual(response.status_code, 200)
        
        data = response.json
        
        # With TIME=MINUTES, 2 minutes should be 120,000 milliseconds
        self.assertEqual(data['auto_logout_time'], 120000)  # 2 min * 60 sec * 1000 ms
        self.assertEqual(data['warning_time'], 60000)  # 1 min * 60 sec * 1000 ms
        self.assertEqual(data['time_unit'], 'MINUTES')
        
        # Minutes should be correctly reported
        self.assertEqual(data['auto_logout_minutes'], 2)
        self.assertEqual(data['warning_minutes'], 1)


if __name__ == '__main__':
    unittest.main()
