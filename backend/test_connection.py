
from sqlalchemy import text
from app.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT DATABASE(), VERSION()")
        )

        database, version = result.fetchone()

        print("MySQL connection successful!")
        print("Database:", database)
        print("MySQL version:", version)

except Exception as error:
    print("MySQL connection failed.")
    print("Error:", error)
