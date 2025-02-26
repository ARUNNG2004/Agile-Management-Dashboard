import unittest
import os
from app import app, generate_burnup_chart, generate_burndown_chart

class TestFlaskBurnCharts(unittest.TestCase):

    def setUp(self):
        """Set up test client."""
        print("Setting up test client...")
        self.app = app.test_client()
        self.app.testing = True

    def test_app_running(self):
        """Test if the Flask app starts properly."""
        print("Running test: test_app_running")
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        print("Flask app is running successfully.")

    def test_generate_burnup_chart(self):
        """Test if the burnup chart is generated and exists."""
        print("Running test: test_generate_burnup_chart")
        burnup_path = generate_burnup_chart()
        self.assertTrue(os.path.exists(burnup_path))
        print("Burnup chart generated successfully at:", burnup_path)

    def test_generate_burndown_chart(self):
        """Test if the burndown chart is generated and exists."""
        print("Running test: test_generate_burndown_chart")
        burndown_path = generate_burndown_chart()
        self.assertTrue(os.path.exists(burndown_path))
        print("Burndown chart generated successfully at:", burndown_path)

    def test_index_route(self):
        """Test if the index page loads correctly."""
        print("Running test: test_index_route")
        response = self.app.get('/')
        self.assertIn(b'<img src="/static/burnup_chart.png"', response.data)
        self.assertIn(b'<img src="/static/burndown_chart.png"', response.data)
        print("Index page loaded correctly with charts.")

    def tearDown(self):
        """Cleanup: Remove generated chart files."""
        print("Cleaning up generated chart files...")
        burnup_path = os.path.join(app.root_path, "static", "burnup_chart.png")
        burndown_path = os.path.join(app.root_path, "static", "burndown_chart.png")
        if os.path.exists(burnup_path):
            os.remove(burnup_path)
            print("Removed:", burnup_path)
        if os.path.exists(burndown_path):
            os.remove(burndown_path)
            print("Removed:", burndown_path)

if __name__ == "__main__":
    unittest.main()
