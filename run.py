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
    # Get database name from environment variable
    from os import environ
    db_name = environ.get('POSTGRES_DB', 'pallcare_db')

    # Terminate all connections to the database before dropping
    sql = f"""
    SELECT pg_terminate_backend(pid) 
    FROM pg_stat_activity 
    WHERE datname = '{db_name}' 
    AND pid <> pg_backend_pid()
    """
    db.session.execute(sql)
    db.session.commit()

    # Now drop all tables
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
