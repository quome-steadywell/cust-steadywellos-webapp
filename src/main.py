"""Main application entry point following template structure."""

from src import create_app

def main():
    """Create and return the Flask application."""
    app = create_app()
    return app

if __name__ == "__main__":
    app = main()
    app.run(debug=True)