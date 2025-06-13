"""Main Flask application factory following template structure."""

from src import create_app

# Create the application instance
app = create_app()

if __name__ == "__main__":
    app.run()