from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

client = MongoClient("mongodb://localhost:27017/")
db = client["flask_app_db"]
users_collection = db["users"]

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    phone_number = request.form.get('phone_number')
    dob = request.form.get('dob')
    dept = request.form.get('dept') # Capture department
    has_members = request.form.get('has_members')  
    member_count = request.form.get('member_count')

    db_dob = dob.replace('/', '-') if dob else None
    actual_members = int(member_count) if (has_members == 'on' and member_count) else 0
    parent_status_val = "PRESENT" if actual_members > 0 else "ABSENT"

    # Update queries to include "dept"
    query = {"DOB": db_dob, "dept": dept}
    
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

    # Pass the department through the URL as well
    return redirect(url_for('result_page', phone=phone_number, dob=db_dob, dept=dept))

@app.route('/result')
def result_page():
    phone_number = request.args.get('phone')
    db_dob = request.args.get('dob')
    dept = request.args.get('dept') # Capture department from URL
    search_result = None

    # Update queries to include "dept"
    query = {"DOB": db_dob, "dept": dept}

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
        
        if username == 'admin' and password == 'admin123':
            total_students = users_collection.count_documents({})
            students_present = users_collection.count_documents({"status": "PRESENT"})
            attendance_rate = round((students_present / total_students) * 100, 1) if total_students > 0 else 0
            
            pipeline = [
                {"$match": {"status": "PRESENT"}},
                {"$group": {"_id": None, "total_parents": {"$sum": "$parent count"}}}
            ]
            parent_agg = list(users_collection.aggregate(pipeline))
            total_parents = parent_agg[0]['total_parents'] if parent_agg else 0

            return render_template('dashboard.html', 
                                   total_students=total_students, 
                                   students_present=students_present, 
                                   total_parents=total_parents,
                                   attendance_rate=attendance_rate)
        else:
            return render_template('login.html', error="Invalid credentials. Please try again.")

    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)