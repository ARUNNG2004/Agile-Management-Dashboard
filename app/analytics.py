import os
import sys
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import app, generate_burnup_chart, generate_burndown_chart


class TestFlaskBurnCharts(unittest.TestCase):

    def setUp(self):
        print("\nSetting up test client...")
        self.app = app.test_client()
        self.app.testing = True

    def test_app_running(self):
        print("Running test: test_app_running")
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        print("✔ Flask app is running successfully.")

    def test_generate_burnup_chart(self):
        print("Running test: test_generate_burnup_chart")
        burnup_path = generate_burnup_chart()  
        self.assertTrue(os.path.exists(burnup_path))
        print("Burnup chart generated successfully at:", burnup_path)

    def test_generate_burndown_chart(self):
        print("Running test: test_generate_burndown_chart")
        burndown_path = generate_burndown_chart() 
        self.assertTrue(os.path.exists(burndown_path))
        print("Burndown chart generated successfully at:", burndown_path)


    def test_index_route(self):
        print("Running test: test_index_route")
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b"burnup_chart.png" in response.data)
        self.assertTrue(b"burndown_chart.png" in response.data)
        print("✔ Index page loaded correctly with charts.")

    def tearDown(self):
        print("\nCleaning up generated chart files...")
        burnup_path = os.path.join("app", "static", "burnup_chart.png")
        burndown_path = os.path.join("app", "static", "burndown_chart.png")

        if os.path.exists(burnup_path):
            os.remove(burnup_path)
            print("✔ Removed:", burnup_path)

        if os.path.exists(burndown_path):
            os.remove(burndown_path)
            print("✔ Removed:", burndown_path)

if __name__ == "__main__":
    unittest.main()
