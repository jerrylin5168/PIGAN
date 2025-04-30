from flask import Flask, jsonify, request, send_file, g
import subprocess
import os
import time
import firebase_admin
from firebase_admin import credentials, auth
from werkzeug.utils import secure_filename
from waitress import serve

# Initialize Firebase Admin SDK for Authentication
cred = credentials.Certificate(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])
firebase_admin.initialize_app(cred)

# Middleware to verify Firebase ID token
def verify_firebase_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except auth.InvalidIdTokenError:
        return None

app = Flask(__name__)

# Middleware to authenticate the user before each request
@app.before_request
def authenticate_user():
    id_token = request.headers.get('Authorization')
    if not id_token:
        return jsonify({"error": "Authorization token is missing"}), 401

    decoded_token = verify_firebase_token(id_token)
    if not decoded_token:
        return jsonify({"error": "Invalid ID token"}), 401

    g.user = decoded_token['uid']

# Directories
UPLOAD_FOLDER = './user_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
TEMP_STORAGE_DIR = './data_inputs'
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)

# Helper function to generate a secure filename
def secure_user_filename(filename):
    return secure_filename(f"{g.user}_{filename}")

# Route to upload a file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], g.user)
    os.makedirs(user_folder, exist_ok=True)  # Ensure user-specific folder exists
    
    filename = secure_user_filename(file.filename)
    file_path = os.path.join(user_folder, filename)

    # Save the file
    file.save(file_path)

    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 200

# Route to receive input from the Android app
@app.route('/receive_input', methods=['POST'])
def receive_input():
    # Get the data sent by the Android app (selected values for dropdowns)
    dropdown1_value = request.json.get('dropdown1')
    dropdown2_value = request.json.get('dropdown2')

    # Get the user ID from g (set in the authenticate_user middleware)
    user_id = g.user

    # Ensure the user's folder exists
    user_folder = os.path.join(TEMP_STORAGE_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)

    # Emotion mapping
    emotion_map = {
        "1": "happy",
        "2": "angry",
        "3": "sad",
        "4": "fearful",
        "5": "surprised"
    }

    # Store the received values in user-specific text files
    if dropdown1_value:
        emotion = emotion_map.get(str(dropdown1_value), "unknown")
        with open(os.path.join(user_folder, 'emotion.txt'), 'w') as f:
            f.write(str(dropdown1_value))  # Store the emotion value (1-5)
    
    if dropdown2_value:
        with open(os.path.join(user_folder, 'emotion_level.txt'), 'w') as f:
            f.write(str(dropdown2_value))  # Store the emotion level value (1-5)

    # Return a response
    return jsonify({"message": "Data received and stored successfully!"})

# Generate endpoint to handle all commands
@app.route('/generate', methods=['POST'])
def generate():
    try:
        # User-specific paths
        user_id = g.user
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
        uploaded_image_path = os.path.join(user_folder, 'uploaded_image.jpg')  # Adjust based on your actual file

        # Command 1: Run resize_256.py
        cmd1 = (
            f'conda run -n deep3d_pytorch bash -c "cd /home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/Deep3DFaceRecon_pytorch && '
            f'python resize_256_new.py --input {uploaded_image_path}"'
        )
        subprocess.run(cmd1, shell=True, check=True)

        # Command 2: Run coeff_detector.py
        cmd2 = (
            f'conda run -n deep3d_pytorch bash -c "cd /home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/Deep3DFaceRecon_pytorch && '
            f'python coeff_detector.py '
            f'--input_dir /home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images '
            f'--keypoint_dir /home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images '
            f'--output_dir /home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images '
            f'--name=model_name '
            f'--epoch=20 '
            f'--model=facerecon '
            f'--inference_batch_size=1"'
        )
        subprocess.run(cmd2, shell=True, check=True)

        # Read the stored dropdown values for emotion and emotion level
        emotion_file = os.path.join(TEMP_STORAGE_DIR, user_id, 'emotion.txt')
        emotion_level_file = os.path.join(TEMP_STORAGE_DIR, user_id, 'emotion_level.txt')

        with open(emotion_file, 'r') as f:
            emotion = f.read().strip()  # Read the emotion (e.g., '3', '4', etc.)

        with open(emotion_level_file, 'r') as f:
            intensity = f.read().strip()  # Read the intensity level (e.g., '1', '5', etc.)

        # Command 3: Run intuitive_control_PIGAN.py
        cmd3 = (
            f'python -m torch.distributed.launch --nproc_per_node=1 --master_port 12345 intuitive_control_PIGAN.py '
            f'--config ./config/face_demo.yaml '
            f'--name face '
            f'--no_resume ' 
            f'--output_dir ./vox_result/PIGAN/{emotion} ' 
            f'--input_name {uploaded_image_path} ' 
            f'--{emotion} '
            f'--intensity {intensity}'
        )
        subprocess.run(cmd3, shell=True, check=True)

        return jsonify({'status': 'success', 'message': 'Commands executed successfully.'})
    except subprocess.CalledProcessError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Serve the app using Waitress
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=20)
