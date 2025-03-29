from app import create_app, db
from flask.cli import FlaskGroup

app = create_app()
cli = FlaskGroup(app)

@cli.command("create_db")
def create_db():
    """Create the database tables."""
    db.create_all()
    print("Database tables created!")

@cli.command("drop_db")
def drop_db():
    """Drop the database tables."""
    db.drop_all()
    print("Database tables dropped!")

@cli.command("seed_db")
def seed_db():
    """Seed the database with initial data."""
    from app.utils.db_seeder import seed_database
    seed_database()
    print("Database seeded with initial data!")

if __name__ == "__main__":
    cli()
