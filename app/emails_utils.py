# from flask_mail import mail, Message


# def send_email_notification(data):
#     team_members = {
#         "Pranav": "pranav@example.com",
#         "Meghana": "vemulameghana9@gmail.com",
#         "Suresh": "sureshmenati0@gmail.com",
#         "Sania": "saniascoops505@gmail.com",
#         "Edward": "ayaan.dhx@gmail.com",
#         "Haritha": "haritha.chakka04@gmail.com",
#         "Riya": "riyaasthana25@gmail.com",
#         "Sai Likitha": "gaddamlikhitha.cse@gmail.com",
#         "Dhruv": "dhruvmittal4480@gmail.com",
#         "Jasna": "jasnaivi@gmail.com",
#         "Janardhan": "reddyjanardhan834@gmail.com",
#         "Mahak": "mahakgianchandani124@gmail.com",
#         "Karthik": "karthik@example.com",
#         "Yashwanthi": "yashwanthimarni77@gmail.com",
#         "Vinitha": "vinitha.chirtha@gmail.com",
#         "Arun": "ngarun2004@gmail.com",
#         "Afreen": "afreen@example.com"
#     }

#     selected_members = data['devTeam']
#     product_owner = data['ProductOwner']
#     scrum_masters = [sprint['scrumMaster'] for sprint in data['sprints']]

#     subject = f"New Project Created: {data['projectName']}"
#     body = f"""
#     A new project has been created:
#     - Project ID: {data['projectId']}
#     - Project Name: {data['projectName']}
#     - Description: {data['projectDescription']}
#     - Product Owner: {product_owner}
#     - Scrum Masters: {', '.join(scrum_masters)}
#     - Development Team: {', '.join(selected_members)}
#     - Start Date: {data['startDate']}
#     - End Date: {data['endDate']}
#     - Revised End Date: {data.get('revisedEndDate', 'Not revised')}
#     """

#     recipients = set()

#     if product_owner in team_members:
#         recipients.add(team_members[product_owner])

#     for master in scrum_masters:
#         if master in team_members:
#             recipients.add(team_members[master])

#     for member in selected_members:
#         if member in team_members:
#             recipients.add(team_members[member])

#     if recipients:
#         msg = Message(subject, recipients=list(recipients))
#         msg.body = body
#         mail.send(msg)
#         print(f"Email sent successfully to: {', '.join(recipients)}")
#     else:
#         print("No valid recipients found to send the email.")
# # 

# from flask_mail import Message
# from flask import current_app  # Import current_app
# from app.models import User  # Assuming you have a User model


# def send_project_notification(data):
#     """
#     Sends an email notification for a new project, fetching recipients from the database.
#     """

#     selected_member_ids = data['devTeam']  # List of User IDs
#     product_owner_id = data['ProductOwner']  # User ID of the product owner
#     sprint_scrum_master_ids = [sprint['scrumMaster'] for sprint in data['sprints']]  # List of scrum master User IDs

#     subject = f"New Project Created: {data['projectName']}"
#     body = f"""
#     A new project has been created:
#     - Project ID: {data['projectId']}
#     - Project Name: {data['projectName']}
#     - Description: {data['projectDescription']}
#     - Product Owner: {get_user_name(product_owner_id)}
#     - Scrum Masters: {', '.join([get_user_name(sm_id) for sm_id in sprint_scrum_master_ids])}
#     - Development Team: {', '.join([get_user_name(member_id) for member_id in selected_member_ids])}
#     - Start Date: {data['startDate']}
#     - End Date: {data['endDate']}
#     - Revised End Date: {data.get('revisedEndDate', 'Not revised')}
#     """

#     recipients = get_recipients(product_owner_id, sprint_scrum_master_ids, selected_member_ids)

#     if recipients:
#         #mail = current_app.extensions.get('mail') #Access mail through app instance
#         msg = Message(subject, recipients=recipients,sender = current_app.config['MAIL_DEFAULT_SENDER'])  # Specify sender
#         msg.body = body

#         try:
#             mail = current_app.extensions.get('mail')
#             mail.send(msg)
#             print(f"Email sent successfully to: {', '.join(recipients)}")
#         except Exception as e:
#             print(f"Error sending email: {e}")
#     else:
#         print("No valid recipients found to send the email.")


# def get_user_name(user_id):
#     """
#     Fetches a user's name from the database given their ID.
#     """
#     try:
#         user = User.query.get(user_id)
#         if user:
#             return user.name  # Assuming your User model has a 'name' attribute
#         else:
#             return "Unknown User"  # Handle cases where the user is not found
#     except Exception as e:
#         print(f"Error fetching user name: {e}")
#         return "Error"


# def get_recipients(product_owner_id, sprint_scrum_master_ids, selected_member_ids):
#     """
#     Fetches email addresses from the database for the given user IDs.
#     Returns a list of email addresses.
#     """
#     recipients = set()

#     all_user_ids = [product_owner_id] + sprint_scrum_master_ids + selected_member_ids

#     try:
#         for user_id in all_user_ids:
#             user = User.query.get(user_id)
#             if user and user.email:  # Assuming your User model has an 'email' attribute
#                 recipients.add(user.email)

#     except Exception as e:
#         print(f"Error fetching recipients from the database: {e}")
#         return []  # Return an empty list if there's an error

#     return list(recipients)
from flask_mail import Message
from flask import current_app
from app import db, mail  # Ensure mail is imported
from app.models import User
def get_recipients(product_owner_name, sprint_scrum_master_names, selected_member_names):
    recipients = set()
    all_user_names = [product_owner_name] + sprint_scrum_master_names + selected_member_names
    print(f"All user NAMES to fetch: {all_user_names}")  # NOTE: NAMES, not IDs

    try:
        for user_name in all_user_names:
            user = User.query.filter_by(name=user_name).first()  # Find user by name!!!

            if user and user.email:
                recipients.add(user.email)
                print(f"Added email for NAME {user_name}: {user.email}")
            else:
                print(f"No user or email found for NAME: {user_name}")
        return list(recipients)
    except Exception as e:
        print(f"Error fetching recipients: {e}")
        return []

def send_project_notification(data):
   product_owner_name = data['ProductOwner']
   sprint_scrum_master_names = [sprint['scrum_master'] for sprint in data['sprints']]
   selected_member_names = data['devTeam']

   # Pass the names to the recipient function
   recipients = get_recipients(product_owner_name, sprint_scrum_master_names, selected_member_names)

   # Build the email
   subject = f"New Project Created: {data['projectName']}"
   body = f"""
   A new project has been created:
   - Project Name: {data['projectName']}
   - Description: {data['projectDescription']}
   - Product Owner: {get_user_name(product_owner_name)}
   -  Start Date: {data['startDate']}
   - End Date: {data['endDate']}
   - Status: {data['status']}

   """
   print(f"Here are all the recipients in the email {recipients}") #Good to check

    # The missing part that you will need to implement
   if recipients:
        msg = Message(
            subject,
            recipients=recipients,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER', 'teamofadm1n123@gmail.com')
        )
        msg.body = body
        print(f"Message recipients set to: {msg.recipients}")

        try:
            mail.send(msg)
            print(f"Email sent successfully to: {', '.join(recipients)}")
        except Exception as e:
            print(f"Error sending email: {e}")
            raise
   else:
        print("No valid recipients found to send the email.")

def get_user_name(user_name):
    try:
        user = User.query.filter_by(name=user_name).first()
        return user.name if user else f"Unknown User (Name: {user_name})"
    except Exception as e:
        print(f"Error fetching user name for name {user_name}: {e}")
        return f"Error (Name: {user_name})"