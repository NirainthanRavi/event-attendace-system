from flask import Flask, render_template, request, redirect, url_for, jsonify
from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from bson.objectid import ObjectId # Added to handle MongoDB object IDs

app = Flask(__name__)

# --- DATABASE SETUP ---
client = MongoClient("mongodb://localhost:27017/")
db = client["flask_app_db"]
users_collection = db["users"]
admin_db = client["admin_auth_db"]
admins_collection = admin_db["admins"]

try:
    users_collection.create_index([("mobile number", 1), ("DOB", 1)], unique=True)
    admins_collection.create_index("username", unique=True)
except Exception as e:
    print(f"Index setup warning: {e}")


# --- INITIALIZATION FUNCTION ---
def setup_default_admin():
    existing_admin = admins_collection.find_one({"username": "admin"})
    
    if not existing_admin:
        hashed_pw = generate_password_hash("admin123")
        admins_collection.insert_one({
            "username": "admin",
            "password_hash": hashed_pw,
            "dept": "ALL" 
        })
        print("\n--- System Notice: Default 'admin' user created successfully. ---")
    
    elif "dept" not in existing_admin:
        admins_collection.update_one(
            {"username": "admin"}, 
            {"$set": {"dept": "ALL"}}
        )
        print("\n--- System Notice: Existing 'admin' user patched. ---")


# --- PUBLIC ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')

@app.route('/checkin')
def checkin():
    return render_template('checkin.html')


# --- STUDENT SEARCH & CHECK-IN ---
@app.route('/search', methods=['POST'])
def search():
    phone_number = request.form.get('phone_number')
    dob = request.form.get('dob')
    has_members = request.form.get('has_members')  
    member_count = request.form.get('member_count')

    db_dob = None
    if dob:
        try:
            date_obj = datetime.strptime(dob, '%Y-%m-%d')
            db_dob = date_obj.strftime('%d-%m-%Y')
        except ValueError:
            db_dob = dob.replace('/', '-')

    actual_members = int(member_count) if (has_members == 'on' and member_count) else 0

    query = {"DOB": db_dob}
    
    match = users_collection.find_one({"mobile number": phone_number, **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": int(phone_number), **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": float(phone_number), **query})

    if match:
        # Changed: Student is now marked as CHECKED IN, waiting for admin verification
        users_collection.update_one(
            {"_id": match["_id"]}, 
            {"$set": {
                "parent count": actual_members,
                "status": "CHECKED IN"
            }}
        )

    return redirect(url_for('result_page', phone=phone_number, dob=db_dob))

@app.route('/result')
def result_page():
    phone_number = request.args.get('phone')
    db_dob = request.args.get('dob')
    search_result = None
    query = {"DOB": db_dob}

    match = users_collection.find_one({"mobile number": phone_number, **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": int(phone_number), **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": float(phone_number), **query})
    
    if match:
        search_result = {
            "name": match.get("name", "Unknown"),
            "room_number": match.get("room number", "N/A"),
            "seat_number": match.get("seat number", "N/A"),
            "parent_count": match.get("parent count", 0)
        }
    
    return render_template('result.html', data=search_result)


# --- SECURE ADMIN DASHBOARD ---
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin_user = admins_collection.find_one({"username": username})
        
        if admin_user and check_password_hash(admin_user['password_hash'], password):
            admin_dept = admin_user.get('dept', 'ALL')
            
            db_query = {}
            view_name = "Overall Data (All Departments)"
            
            if admin_dept != "ALL":
                db_query = {"dept": admin_dept}
                view_name = admin_dept

            # Calculate Stats (Present means fully verified)
            total_students = users_collection.count_documents(db_query)
            students_present = users_collection.count_documents({**db_query, "status": "PRESENT"})
            attendance_rate = round((students_present / total_students) * 100, 1) if total_students > 0 else 0
            
            parent_agg = list(users_collection.aggregate([
                {"$match": {**db_query, "status": "PRESENT"}},
                {"$group": {"_id": None, "total_parents": {"$sum": "$parent count"}}}
            ]))
            total_parents = parent_agg[0]['total_parents'] if parent_agg else 0

            # Fetch Individual Student Roster
            student_cursor = users_collection.find(db_query).sort("name", 1)
            
            # Format the _id as a string so we can pass it safely to the HTML template
            student_list = []
            for student in student_cursor:
                student['_id_str'] = str(student['_id'])
                student_list.append(student)

            return render_template('dashboard.html', 
                                   total_students=total_students, 
                                   students_present=students_present, 
                                   total_parents=total_parents,
                                   attendance_rate=attendance_rate,
                                   current_view=view_name,
                                   student_list=student_list)
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

# --- NEW: ADMIN VERIFICATION API ---
@app.route('/mark_present/<student_id>', methods=['POST'])
def mark_present(student_id):
    """Background route for the admin 'Verify' button."""
    try:
        users_collection.update_one(
            {"_id": ObjectId(student_id)},
            {"$set": {"status": "PRESENT"}}
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == '__main__':
    setup_default_admin()
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)