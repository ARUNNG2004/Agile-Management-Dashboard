from vercel_wsgi import handle_request
from app import create_app  # Ensure this imports the create_app function

application = create_app()

def handler(request, context):
    return handle_request(application, request, context)

if __name__ == "__main__":
    application.run(debug=True)
