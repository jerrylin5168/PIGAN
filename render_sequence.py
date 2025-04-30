import os
import sys
import argparse
import torch
import yaml
import cv2
from tqdm import tqdm
from PIL import Image
from torchvision import transforms

# Add Deep3DFaceRecon path to system path
DEEP3D_PATH = "/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main/Deep3DFaceRecon_pytorch/"
sys.path.append(DEEP3D_PATH)

# Import PIRender modules
from models.networks import Net3DMM, define_G
from models.projected_model import fsModel

# Import necessary functions from emotion control script
from emotion_control import load_model

def render_sequence_video(model, source_img_path, param_sequence, output_path, device):
    """
    Render a video using a pre-generated sequence of 3DMM parameters.
    
    Args:
        model: The PIRender model
        source_img_path (str): Path to the source image
        param_sequence (list): List of 3DMM parameters for each frame
        output_path (str): Path to save the output video
        device: PyTorch device
    """
    # Load source image
    source_img = Image.open(source_img_path).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    source_tensor = transform(source_img).unsqueeze(0).to(device)
    
    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, 30, (256, 256))
    
    # Generate frames
    with torch.no_grad():
        for params in tqdm(param_sequence, desc="Rendering frames"):
            # Generate frame
            output = model.G(source_tensor, params.unsqueeze(0))
            
            # Convert to image and save to video
            output_img = output.squeeze(0).cpu().numpy()
            output_img = (output_img * 0.5 + 0.5) * 255
            output_img = output_img.transpose(1, 2, 0).astype(np.uint8)
            
            # BGR for OpenCV
            output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)
            video_writer.write(output_img)
    
    video_writer.release()
    print(f"Video saved to {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Render Emotion Sequence Video with PIRender")
    parser.add_argument("--config", type=str, default="./config/face_demo.yaml", help="Path to the config file")
    parser.add_argument("--checkpoint", type=str, 
                        default="/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main/result/face/epoch_00190_iteration_000400000_checkpoint.pt", 
                        help="Path to the model checkpoint")
    parser.add_argument("--source_img", type=str, required=True, help="Path to source image")
    parser.add_argument("--sequence_file", type=str, required=True, help="Path to the pre-generated sequence file")
    parser.add_argument("--output_path", type=str, default="emotion_video.mp4", help="Output video path")
    parser.add_argument("--gpu_ids", type=str, default="0", help="GPU IDs")
    args = parser.parse_args()
    
    # Create output directory if needed
    output_dir = os.path.dirname(args.output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    # Set device
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_ids
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    
    # Load model
    model = load_model(config, args.checkpoint, device)
    
    # Load parameter sequence
    param_sequence = torch.load(args.sequence_file)
    print(f"Loaded sequence with {len(param_sequence)} frames")
    
    # Render video
    render_sequence_video(model, args.source_img, param_sequence, args.output_path, device)

if __name__ == "__main__":
    import numpy as np
    main()