from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# --- DATABASE SETUP ---

# Database 1: Main Application Database (Students)
client = MongoClient("mongodb://localhost:27017/")
db = client["flask_app_db"]
users_collection = db["users"]

# Database 2: Admin Authentication Database (Separate DB)
admin_db = client["admin_auth_db"]
admins_collection = admin_db["admins"]

# Apply Indexes for Performance
try:
    users_collection.create_index([("mobile number", 1), ("DOB", 1)], unique=True)
    admins_collection.create_index("username", unique=True)
except Exception as e:
    print(f"Index setup warning: {e}")


# --- INITIALIZATION FUNCTION ---
def setup_default_admin():
    """Checks if an admin user exists, and creates a default one if it doesn't."""
    existing_admin = admins_collection.find_one({"username": "admin"})
    
    if not existing_admin:
        # Create the default admin with a hashed password
        hashed_pw = generate_password_hash("admin123")
        admins_collection.insert_one({
            "username": "admin",
            "password_hash": hashed_pw
        })
        print("System Notice: Default 'admin' user created successfully.")


# --- INDUCTION FLOW ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/instructions')
def instructions():
    return render_template('instructions.html')


# --- MAIN APP ROUTES ---
@app.route('/checkin')
def checkin():
    return render_template('checkin.html')

@app.route('/search', methods=['POST'])
def search():
    phone_number = request.form.get('phone_number')
    dob = request.form.get('dob')
    has_members = request.form.get('has_members')  
    member_count = request.form.get('member_count')

    # Convert incoming YYYY-MM-DD from HTML5 date picker to DD-MM-YYYY for the database
    db_dob = None
    if dob:
        try:
            date_obj = datetime.strptime(dob, '%Y-%m-%d')
            db_dob = date_obj.strftime('%d-%m-%Y')
        except ValueError:
            db_dob = dob.replace('/', '-')

    actual_members = int(member_count) if (has_members == 'on' and member_count) else 0
    parent_status_val = "PRESENT" if actual_members > 0 else "ABSENT"

    query = {"DOB": db_dob}
    
    match = users_collection.find_one({"mobile number": phone_number, **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": int(phone_number), **query})
    if not match and phone_number.isdigit():
        match = users_collection.find_one({"mobile number": float(phone_number), **query})

    if match:
        users_collection.update_one(
            {"_id": match["_id"]}, 
            {"$set": {
                "parent count": actual_members,
                "parent status": parent_status_val,
                "status": "PRESENT"
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

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # --- SECURE DATABASE AUTHENTICATION ---
        admin_user = admins_collection.find_one({"username": username})
        
        if admin_user and check_password_hash(admin_user['password_hash'], password):
            
            # --- 1. Overall Stats ---
            total_students = users_collection.count_documents({})
            students_present = users_collection.count_documents({"status": "PRESENT"})
            attendance_rate = round((students_present / total_students) * 100, 1) if total_students > 0 else 0
            
            parent_agg = list(users_collection.aggregate([
                {"$match": {"status": "PRESENT"}},
                {"$group": {"_id": None, "total_parents": {"$sum": "$parent count"}}}
            ]))
            total_parents = parent_agg[0]['total_parents'] if parent_agg else 0

            # --- 2. Department-Wise Aggregation Pipeline ---
            dept_pipeline = [
                {
                    "$group": {
                        "_id": "$dept",
                        "total_registered": {"$sum": 1},
                        "total_present": {
                            "$sum": {"$cond": [{"$eq": ["$status", "PRESENT"]}, 1, 0]}
                        },
                        "parents_present": {
                            "$sum": {
                                "$cond": [{"$eq": ["$status", "PRESENT"]}, "$parent count", 0]
                            }
                        }
                    }
                },
                {"$sort": {"_id": 1}}
            ]
            
            raw_dept_stats = list(users_collection.aggregate(dept_pipeline))
            
            # --- 3. Format the department stats ---
            dept_stats = []
            for d in raw_dept_stats:
                dept_name = d["_id"] if d["_id"] else "Unknown"
                t_reg = d["total_registered"]
                t_pres = d["total_present"]
                p_pres = d["parents_present"]
                att_rate = round((t_pres / t_reg) * 100, 1) if t_reg > 0 else 0
                
                dept_stats.append({
                    "dept": dept_name,
                    "total_registered": t_reg,
                    "total_present": t_pres,
                    "parents_present": p_pres,
                    "attendance_rate": att_rate
                })

            return render_template('dashboard.html', 
                                   total_students=total_students, 
                                   students_present=students_present, 
                                   total_parents=total_parents,
                                   attendance_rate=attendance_rate,
                                   dept_stats=dept_stats)
        else:
            return render_template('login.html', error="Invalid username or password.")

    return render_template('login.html')

if __name__ == '__main__':
    # Run the setup check right before starting the server
    setup_default_admin()
    app.run(debug=True)