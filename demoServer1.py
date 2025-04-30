import subprocess
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/resize', methods=['POST'])
def resize_command():
    # Define the command for running the resize script
    command = ["python", "resize_256.py"]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Return the output of the command as a response
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })


@app.route('/detector', methods=['POST'])
def detector_command():
    # Define the command for running the model
    command = [
        "python", "coeff_detector.py",
        "--input_dir", "/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images",
        "--keypoint_dir", "/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images",
        "--output_dir", "/home/jerrylin51668/ECEN_404/PIGAN_V4/PIRender-main/demo_images",
        "--name", "model_name",
        "--epoch", "20",
        "--model", "facerecon",
        "--inference_batch_size", "1"
    ]

    # Run the command
    result = subprocess.run(command, capture_output=True, text=True)

    # Return the output of the command as a response
    return jsonify({
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    })


if __name__ == '__main__':
    # Run Flask server on port 5000
    app.run(debug=True, host='0.0.0.0', port=5000)

