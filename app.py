from flask import Flask, request, jsonify, send_from_directory
from pymongo import MongoClient
from bson.objectid import ObjectId
import logging

app = Flask(__name__)
app.config['DEBUG'] = True

logging.basicConfig(level=logging.DEBUG)

# MongoDB credentials
mongo_username = "ravi_admin"
mongo_password = "SachinAdmin"
mongo_host = '20.244.40.18'
mongo_port = 27017
mongo_db = 'PCL_INTERNS'
mongo_auth_db = 'admin'

# MongoDB connection string
mongo_uri = f'mongodb://{mongo_username}:{mongo_password}@{mongo_host}:{mongo_port}/{mongo_db}?authSource={mongo_auth_db}'
client = MongoClient(mongo_uri)

# Access the database and collection
db = client[mongo_db]
employees_collection = db['employee_data']

def format_employee(employee):
    return f"ID: {employee['employee_id']}, Name: {employee['name']}, Position: {employee['position']}, Salary: {employee['salary']}"

def format_employees(employees):
    return "\n".join([format_employee(employee) for employee in employees])

# Employee model operations
def create_employee(data):
    first_name = data['name'].split()[0].lower()
    employee_id = generate_employee_id(first_name)
    data['employee_id'] = employee_id
    result = employees_collection.insert_one(data)
    return employee_id

def get_employee(employee_id):
    employee = employees_collection.find_one({'employee_id': employee_id})
    if employee:
        employee['_id'] = str(employee['_id'])
        return employee
    return None

def delete_employee(employee_id):
    result = employees_collection.delete_one({'employee_id': employee_id})
    return result.deleted_count > 0

def get_all_employees():
    employees = employees_collection.find()
    return [{**employee, '_id': str(employee['_id'])} for employee in employees]

def update_employee(employee_id, data):
    result = employees_collection.update_one(
        {'employee_id': employee_id},
        {'$set': data}
    )
    return result.modified_count > 0

def generate_employee_id(first_name):
    existing_employees = list(employees_collection.find({'employee_id': {'$regex': f'^{first_name}_'}}))
    max_id = 0
    for employee in existing_employees:
        suffix = int(employee['employee_id'].split('_')[1])
        if suffix > max_id:
            max_id = suffix
    new_id = max_id + 1
    return f"{first_name}_{new_id}"

# Chatbot processing
@app.route('/chatbot', methods=['POST'])
def chatbot_interaction():
    user_input = request.json.get('message')
    lines = user_input.strip().split('\n')
    
    if len(lines) < 1:
        return jsonify({'response': 'Invalid input format'}), 400

    action = lines[0].strip().lower()

    if action == 'create_employee':
        if len(lines) < 2:
            return jsonify({'response': 'Invalid input format for creating an employee'}), 400
        data = parse_employee_data(lines[1:])
        employee_id = create_employee(data)
        return jsonify({'response': f'Employee created with ID: {employee_id}'}), 201

    elif action == 'get_employee_details':
        if len(lines) != 2:
            return jsonify({'response': 'Invalid input format for getting employee details'}), 400
        employee_id = lines[1].strip()
        employee = get_employee(employee_id)
        if employee:
            return jsonify({'response': format_employee(employee)})
        return jsonify({'response': 'Employee not found'}), 404

    elif action == 'delete_employee':
        if len(lines) != 2:
            return jsonify({'response': 'Invalid input format for deleting an employee'}), 400
        employee_id = lines[1].strip()
        success = delete_employee(employee_id)
        if success:
            return jsonify({'response': 'Employee deleted'}), 204
        return jsonify({'response': 'Delete failed'}), 404

    elif action == 'get_all_employees':
        employees = get_all_employees()
        return jsonify({'response': format_employees(employees)})

    elif action == 'update_employee':
        if len(lines) < 2:
            return jsonify({'response': 'Invalid input format for updating an employee'}), 400
        employee_id = lines[1].strip()
        data = parse_employee_data(lines[2:])
        success = update_employee(employee_id, data)
        if success:
            return jsonify({'response': 'Employee updated'})
        return jsonify({'response': 'Update failed'}), 404

    else:
        return jsonify({'response': 'Unknown action'}), 400


def parse_employee_data(lines):
    data = {}
    for line in lines:
        key, value = line.split(':', 1)
        data[key.strip()] = value.strip()
    return data

# Serve the HTML file
@app.route('/')
def serve_index():
    return send_from_directory('templates', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
