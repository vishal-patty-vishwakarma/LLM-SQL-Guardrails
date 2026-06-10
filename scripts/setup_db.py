from database.connection import init_db
from config.settings import settings


def main():
    print(f"Creating database at: {settings.database_path}")
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    init_db()
    print("Database setup complete!")


if __name__ == "__main__":
    main()