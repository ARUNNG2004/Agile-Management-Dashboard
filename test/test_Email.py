import unittest
from unittest.mock import patch
from app import app, db, Project, UserStory, generate_and_send_summary_email, send_deadline_reminders
from datetime import datetime, timedelta
from flask_mail import Message

class TestEmailFunctionality(unittest.TestCase):
    def setUp(self):
        # Configure test database
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app = app.test_client()

        with app.app_context():
            db.create_all()

            # Create test project
            self.test_project = Project(
                project_name="Test Project",
                project_manager="Test Manager",
                start_date=datetime.now().strftime("%Y-%m-%d"),
                end_date=(datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                status="Active"
            )
            db.session.add(self.test_project)

            # Create test user stories
            self.test_story = UserStory(
                project_id=1,
                sprint_id=1,
                description="Test Story",
                story_point=5,
                status="Completed"
            )
            db.session.add(self.test_story)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch('app.mail.send')
    def test_summary_email_generation(self, mock_send):
        """Test if summary email is generated correctly"""
        with app.app_context():
            generate_and_send_summary_email()
            mock_send.assert_called()

            # Verify email was called with correct parameters
            call_args = mock_send.call_args_list[0][0][0]
            self.assertIsInstance(call_args, Message)
            self.assertTrue("Summary Report" in call_args.subject)
            self.assertTrue(self.test_project.project_name in call_args.body)

    @patch('app.mail.send')
    def test_deadline_reminder_email(self, mock_send):
        """Test if deadline reminder emails are sent correctly"""
        with app.app_context():
            send_deadline_reminders()
            mock_send.assert_called()

            # Verify reminder email contains correct information
            call_args = mock_send.call_args_list[0][0][0]
            self.assertIsInstance(call_args, Message)
            self.assertTrue("Deadline Reminder" in call_args.subject)
            self.assertTrue(self.test_project.project_name in call_args.body)

    @patch('app.pdfkit.from_string')
    def test_pdf_generation(self, mock_pdf_gen):
        """Test if PDF report is generated correctly"""
        with app.app_context():
            mock_pdf_gen.return_value = b"Mock PDF Content"
            generate_and_send_summary_email()
            mock_pdf_gen.assert_called()

    def test_project_statistics_calculation(self):
        """Test if project statistics are calculated correctly for email reports"""
        with app.app_context():
            # Add more test data
            UserStory(
                project_id=1,
                sprint_id=1,
                description="Another Story",
                story_point=3,
                status="In Progress"
            ).save()

            total_stories = UserStory.query.filter_by(project_id=1).count()
            completed_stories = UserStory.query.filter_by(
                project_id=1,
                status="Completed"
            ).count()

            self.assertEqual(total_stories, 2)
            self.assertEqual(completed_stories, 1)

            # Test completion percentage calculation
            completion_percentage = (completed_stories / total_stories) * 100
            self.assertEqual(completion_percentage, 50.0)

    @patch('app.mail.send')
    def test_email_error_handling(self, mock_send):
        """Test error handling in email sending process"""
        with app.app_context():
            # Simulate email sending error
            mock_send.side_effect = Exception("Email sending failed")

            try:
                generate_and_send_summary_email()
            except Exception as e:
                self.fail(f"Email error handling failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
