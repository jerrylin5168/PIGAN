from flask import Flask, jsonify, request, g, send_file
import os
import time  # Add this at the top of your file if it's not already imported
import glob
import subprocess
from PIL import Image, ImageOps
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

# Directories setup
UPLOAD_FOLDER = './user_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
TEMP_STORAGE_DIR = './data_inputs'
os.makedirs(TEMP_STORAGE_DIR, exist_ok=True)

# Helper function to generate a secure filename
def secure_user_filename(filename):
    return secure_filename(f"{g.user}_{filename}")

# Helper function for resizing images
def resize_image(input_path, output_path, size=(256, 256)):
    """
    Resizes an image to the specified size and saves it.
    """
    try:
        img = Image.open(input_path)
        img = ImageOps.exif_transpose(img)  # Apply EXIF orientation fix
        # Ensure compatibility with both new and old versions of Pillow
        try:
            resample_filter = Image.Resampling.LANCZOS
        except AttributeError:
            resample_filter = Image.ANTIALIAS

        img_resized = img.resize(size, resample_filter)
        img_resized.save(output_path)
        print(f"Resized image saved to: {output_path}")
    except Exception as e:
        print(f"Error resizing image: {e}")
        raise

# Route to upload a file
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], g.user)
    os.makedirs(user_folder, exist_ok=True)
    
    filename = "uploaded_image.jpg"
    file_path = os.path.join(user_folder, filename)

    # Save the file
    file.save(file_path)

    return jsonify({'message': 'File uploaded successfully', 'file_path': file_path}), 200

# Route to receive input from the Android app
@app.route('/receive_input', methods=['POST'])
def receive_input():
    dropdown1_value = request.json.get('dropdown1')
    dropdown2_value = request.json.get('dropdown2')
    user_id = g.user
    user_folder = os.path.join(TEMP_STORAGE_DIR, user_id)
    os.makedirs(user_folder, exist_ok=True)
    
    emotion_map = {
        "1": "happy",
        "2": "angry",
        "3": "sad",
        "4": "fear",
        "5": "surprise"
    }

    if dropdown1_value:
        # Look up the emotion string using the provided number
        emotion = emotion_map.get(str(dropdown1_value), "unknown")
        with open(os.path.join(user_folder, 'emotion.txt'), 'w') as f:
            f.write(emotion)

    
    if dropdown2_value:
        with open(os.path.join(user_folder, 'emotion_level.txt'), 'w') as f:
            f.write(str(dropdown2_value))
    
    return jsonify({"message": "Data received and stored successfully!"})

# Modified generate endpoint using inline resizing
@app.route('/generate', methods=['POST'])
def generate():
    try:
        user_id = g.user
        user_folder = os.path.join(app.config['UPLOAD_FOLDER'], user_id)
        # Assuming the uploaded image is stored with a known filename
        uploaded_image_path = os.path.join(user_folder, 'uploaded_image.jpg')
        
        # Define the demo_images directory and output path for resized image
        demo_images_dir = "/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images"
        os.makedirs(demo_images_dir, exist_ok=True)
        # Construct output file path; here, we append "_256" to indicate resized image
        output_filename = "uploaded_image_256.jpg"
        output_path = os.path.join(demo_images_dir, output_filename)
        
        # Directly call the resize function
        resize_image(uploaded_image_path, output_path)
        
        # Now proceed with the rest of your processing commands:
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
        
        # Read dropdown values from the temporary storage
        emotion_file = os.path.join(TEMP_STORAGE_DIR, user_id, 'emotion.txt')
        emotion_level_file = os.path.join(TEMP_STORAGE_DIR, user_id, 'emotion_level.txt')

        with open(emotion_file, 'r') as f:
            emotion = f.read().strip()
        with open(emotion_level_file, 'r') as f:
            intensity = f.read().strip()
        
        cmd3 = (
            f'python -m torch.distributed.launch --nproc_per_node=1 --master_port 12345 intuitive_control_PIGAN_v3.py '
            f'--config ./config/face_demo.yaml '
            f'--name face '
            f'--no_resume ' 
            f'--output_dir ./vox_result/PIGAN/{emotion} ' 
            f'--input_name ./demo_images '   # Use the resized image path here
            f'--{emotion} '
            f'--intensity {intensity}'
        )
        subprocess.run(cmd3, shell=True, check=True)
        
        # Locate the generated video file
        # Your video is in a folder like:
        # "/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/vox_result/PIGAN/happy/epoch_00190_iteration_000400000/"
        # Expected final video path
        video_output_dir = f"/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/vox_result/PIGAN/{emotion}"
        sub_dirs = glob.glob(os.path.join(video_output_dir, 'epoch_*'))
        if not sub_dirs:
            return jsonify({'status': 'error', 'message': 'No video generation folder found'}), 500

        target_dir = sorted(sub_dirs)[-1]
        user_output_path = os.path.join(target_dir, "uploaded_image_256.mp4")

        print(f"Looking for video at: {user_output_path}")

        # Retry mechanism: Wait for video file to appear
        max_retries = 10
        retry_interval = 2  # seconds

        for attempt in range(max_retries):
            if os.path.exists(user_output_path):
                print(f"Video found at {user_output_path} on attempt {attempt + 1}")
                return send_file(user_output_path, mimetype='video/mp4', as_attachment=False)
            else:
                print(f"Video not found yet (Attempt {attempt + 1}), retrying in {retry_interval}s...")
                time.sleep(retry_interval)

        return jsonify({'error': 'Generated video not found after multiple attempts'}), 404

    except subprocess.CalledProcessError as e:
        print(f"Subprocess failed: {e}")
        return jsonify({'error': f'Subprocess failed: {str(e)}'}), 500
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500
# Serve the app using Waitress
if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=5000, threads=20)

