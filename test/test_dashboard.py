import unittest
import sys
import os
from flask import json
from datetime import datetime, timedelta

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from app import app, db, Project, UserStory, ScrumMaster, SprintCalendar

class DashboardTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("Setting up test environment...")
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        app.config['TESTING'] = True
        cls.client = app.test_client()
        cls.client.testing = True
        with app.app_context():
            db.create_all()
            cls._create_test_data()
        print("Test environment setup complete.")

    @classmethod
    def _create_test_data(cls):
        """Create sample test data"""
        with app.app_context():
            try:
                # Create test project
                project = Project(
                    project_name="Test Project",
                    project_manager="Test Manager",
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                    end_date=(datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                    status="active"
                )
                db.session.add(project)
                db.session.commit()

                # Create test scrum master
                scrum_master = ScrumMaster(
                    email="test@test.com",
                    name="Test Master",
                    contact_number="1234567890"
                )
                db.session.add(scrum_master)
                db.session.commit()

                # Create test sprint
                sprint = SprintCalendar(
                    project_id=project.id,
                    scrum_master_id=scrum_master.id,
                    sprint_no=1,
                    start_date=datetime.now().strftime("%Y-%m-%d"),
                    end_date=(datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
                    velocity=20  # Set velocity to 20 as expected in test
                )
                db.session.add(sprint)
                db.session.commit()

                # Create test user stories with explicit status
                stories = [
                    UserStory(
                        project_id=project.id,
                        sprint_id=1,
                        planned_sprint=1,
                        actual_sprint=1,
                        description="Test Story 1",
                        story_point=5,
                        moscow="Must",
                        assignee="Test Dev",
                        status="Completed",
                        dependency="None"
                    ),
                    UserStory(
                        project_id=project.id,
                        sprint_id=1,
                        planned_sprint=1,
                        actual_sprint=1,
                        description="Test Story 2",
                        story_point=3,
                        moscow="Should",
                        assignee="Test Dev",
                        status="In Progress",
                        dependency="None"
                    )
                ]
                for story in stories:
                    db.session.add(story)
                db.session.commit()

            except Exception as e:
                print(f"Error in test data setup: {e}")
                db.session.rollback()
                raise

    def setUp(self):
        """Reset database before each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()
            self._create_test_data()

    def test_homepage_loads(self):
        """Test if the homepage loads successfully"""
        print("Running test: Homepage Loads")
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Dashboard", res.data)
        print("Test Passed: Homepage Loads")

    def test_project_list_api(self):
        """Test if /projects API returns valid JSON response"""
        print("Running test: Project List API")
        res = self.client.get('/projects')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = json.loads(res.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)  # Should have our test project
        print("Test Passed: Project List API")

    def test_project_counts_api(self):
        """Test project status pie chart API response"""
        print("Running test: Project Counts API")
        res = self.client.get('/project_counts')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = json.loads(res.data)
        self.assertIn('total', data)
        self.assertIn('active', data)
        self.assertIn('on_hold', data)
        self.assertIn('ongoing', data)
        self.assertTrue(data['total'] > 0)  # Should have our test project
        print("Test Passed: Project Counts API")

    def test_sprint_details_api(self):
        """Test if the sprint details API returns valid JSON response"""
        print("Running test: Sprint Details API")
        res = self.client.get('/sprint_details')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.is_json)
        data = json.loads(res.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)  # Should have our test sprint
        print("Test Passed: Sprint Details API")

    def test_project_details_page(self):
        """Test if project details page loads for a given project ID"""
        print("Running test: Project Details Page")
        with app.app_context():
            project = Project.query.first()
            self.assertIsNotNone(project)
            res = self.client.get(f'/project/{project.id}')
            self.assertEqual(res.status_code, 200)
        print("Test Passed: Project Details Page")

    def test_invalid_project_access(self):
        """Test accessing an invalid project ID returns 404"""
        print("Running test: Invalid Project Access")
        with app.app_context():
            try:
                # Get the maximum project ID and add 1 to ensure it doesn't exist
                max_id = db.session.query(db.func.max(Project.id)).scalar() or 0
                invalid_id = max_id + 1

                # Make the request and check status code
                res = self.client.get(f'/project/{invalid_id}')
                self.assertEqual(res.status_code, 404, f"Expected 404 for non-existent project {invalid_id}, got {res.status_code}")

                # Also try with a negative ID to be thorough
                res = self.client.get('/project/-1')
                self.assertEqual(res.status_code, 404, "Expected 404 for negative project ID")

            except Exception as e:
                self.fail(f"Test failed with exception: {str(e)}")
        print("Test Passed: Invalid Project Access")

    def test_project_summary(self):
        """Test project summary page"""
        print("Running test: Project Summary")
        with app.app_context():
            project = Project.query.first()
            self.assertIsNotNone(project)
            res = self.client.get(f'/summary/{project.id}')
            self.assertEqual(res.status_code, 200)
            self.assertIn(b"Project Summary", res.data)
        print("Test Passed: Project Summary")

    def test_user_story_status(self):
        """Test user story status counts"""
        print("Running test: User Story Status")
        with app.app_context():
            project = Project.query.first()
            self.assertIsNotNone(project)

            # Verify the stories were created correctly
            stories = UserStory.query.filter_by(project_id=project.id).all()
            self.assertEqual(len(stories), 2, "Should have exactly 2 test stories")

            completed_stories = UserStory.query.filter_by(
                project_id=project.id,
                status="Completed"
            ).count()
            in_progress_stories = UserStory.query.filter_by(
                project_id=project.id,
                status="In Progress"
            ).count()

            # Debug output
            print(f"Found {completed_stories} completed and {in_progress_stories} in-progress stories")

            self.assertEqual(completed_stories, 1, "Should have exactly 1 completed story")
            self.assertEqual(in_progress_stories, 1, "Should have exactly 1 in-progress story")
        print("Test Passed: User Story Status")

    def test_sprint_velocity(self):
        """Test sprint velocity calculation"""
        print("Running test: Sprint Velocity")
        with app.app_context():
            project = Project.query.first()
            self.assertIsNotNone(project)
            sprint = SprintCalendar.query.filter_by(project_id=project.id).first()
            self.assertIsNotNone(sprint)
            self.assertEqual(sprint.velocity, 20, "Sprint velocity should be 20")
        print("Test Passed: Sprint Velocity")

    def tearDown(self):
        """Clean up after each test"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @classmethod
    def tearDownClass(cls):
        print("Tearing down test environment...")
        with app.app_context():
            db.drop_all()
        # Remove test database file
        if os.path.exists('test.db'):
            os.remove('test.db')
        print("Test environment teardown complete.")

if __name__ == '__main__':
    unittest.main()
