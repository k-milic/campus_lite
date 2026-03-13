from app import create_app

# Create the Flask application instance for local development.
app = create_app()

if __name__ == "__main__":
    # Debug mode is useful during development; production should use a WSGI server.
    app.run(debug=True)
