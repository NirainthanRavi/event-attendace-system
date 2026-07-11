import getpass
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# 1. Connect to the Admin Database
client = MongoClient("mongodb://localhost:27017/")
admin_db = client["admin_auth_db"]
admins_collection = admin_db["admins"]

def create_admin():
    print("--- Add New Department Admin ---")
    
    # 2. Get the desired username
    username = input("Enter new admin username: ").strip()
    if not username:
        print("Error: Username cannot be empty.")
        return

    # Check if user already exists
    if admins_collection.find_one({"username": username}):
        print(f"Error: The user '{username}' already exists in the database.")
        return

    # 3. Get the Department
    print("\nAvailable Departments: ALL, BSc, BCA")
    print("(Make sure this exactly matches the dropdown options in your login.html)")
    dept = input("Assign Department: ").strip()
    
    if not dept:
        print("Error: Department cannot be empty.")
        return

    # 4. Get and confirm the password securely (input is hidden)
    password = getpass.getpass("\nEnter password: ")
    confirm_password = getpass.getpass("Confirm password: ")

    if password != confirm_password:
        print("Error: Passwords do not match. Aborting.")
        return
    
    if not password:
        print("Error: Password cannot be empty.")
        return

    # 5. Hash the password and save to MongoDB
    hashed_pw = generate_password_hash(password)
    
    try:
        admins_collection.insert_one({
            "username": username,
            "password_hash": hashed_pw,
            "dept": dept  # <-- The crucial new field for RBAC
        })
        print(f"\nSuccess! User '{username}' has been securely added with access to '{dept}'.")
    except Exception as e:
        print(f"\nDatabase Error: {e}")

if __name__ == "__main__":
    create_admin()