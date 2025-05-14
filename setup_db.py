from sqlalchemy import create_engine, text
import os

# Database connection URL
DATABASE_URL = "postgresql://domain_api_db_user:1mvna6F3NRpaKVQ5C7Q5gO2TY291aRjm@dpg-d0ht7pumcj7s739g7gc0-a.oregon-postgres.render.com/domain_api_db"

def setup_database():
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        # Read schema file
        with open('schema.sql', 'r') as file:
            schema = file.read()
        
        # Split into individual statements
        statements = schema.split(';')
        
        # Connect and execute each statement
        with engine.connect() as conn:
            for statement in statements:
                # Skip empty statements
                if statement.strip():
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                        print(f"Executed statement successfully")
                    except Exception as e:
                        print(f"Error executing statement: {str(e)}")
            
        print("Database schema creation completed!")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}")

if __name__ == "__main__":
    setup_database()
