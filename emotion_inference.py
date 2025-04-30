"""
Modified inference script for PIRender to control facial emotions.
Based on the original inference.py script with added emotion control functionality.
"""

import os
import numpy as np
import torch
import torch.nn.functional as F
from argparse import ArgumentParser
from tqdm import tqdm
import cv2
import yaml
from PIL import Image
from torchvision import transforms
import matplotlib.pyplot as plt

# Define emotion parameter mappings for the expression coefficients
EMOTION_PARAMS = {
    'neutral': np.zeros(64),  # Base neutral expression
    'happy': np.zeros(64),
    'sad': np.zeros(64),
    'angry': np.zeros(64),
    'fear': np.zeros(64),
    'surprise': np.zeros(64)
}

# Set the key expression coefficients for each emotion
# Happy - smile related parameters
EMOTION_PARAMS['happy'][0] = 0.7   # Mouth corners up
EMOTION_PARAMS['happy'][1] = 0.5   # Slight mouth open
EMOTION_PARAMS['happy'][4] = 0.3   # Cheek raise

# Sad - droopy features
EMOTION_PARAMS['sad'][0] = -0.5    # Mouth corners down
EMOTION_PARAMS['sad'][6] = 0.3     # Inner brow raise
EMOTION_PARAMS['sad'][15] = 0.3    # Slight brow furrow

# Angry - furrowed brow, tight mouth
EMOTION_PARAMS['angry'][4] = -0.3  # Lowered brow
EMOTION_PARAMS['angry'][14] = 0.6  # Brow furrow
EMOTION_PARAMS['angry'][15] = 0.3  # Lip tightener

# Fear - raised brows, widened eyes
EMOTION_PARAMS['fear'][5] = 0.6    # Brow raise
EMOTION_PARAMS['fear'][6] = 0.5    # Inner brow raise
EMOTION_PARAMS['fear'][19] = 0.4   # Upper lid raiser

# Surprise - raised brows, open mouth
EMOTION_PARAMS['surprise'][5] = 0.7  # Brow raise
EMOTION_PARAMS['surprise'][1] = 0.8  # Jaw drop
EMOTION_PARAMS['surprise'][19] = 0.6 # Upper lid raiser

# Function to apply an emotion to 3DMM parameters
def apply_emotion(source_params, emotion, intensity=1.0):
    """
    Apply emotion parameters to source 3DMM parameters.
    
    Args:
        source_params: Source identity parameters (tensor)
        emotion: Emotion name (string)
        intensity: Intensity of the emotion (0.0 to 1.0)
        
    Returns:
        Modified 3DMM parameters
    """
    params = source_params.clone()
    emotion_params = EMOTION_PARAMS[emotion] * intensity
    
    # Apply to expression coefficients (typically indices 80-144)
    expression_start_idx = 80
    expression_end_idx = 144
    params[:, expression_start_idx:expression_end_idx] = torch.tensor(
        emotion_params, 
        dtype=torch.float32, 
        device=source_params.device
    ).unsqueeze(0)
    
    return params

# Function to interpolate between emotions
def interpolate_emotions(source_params, start_emotion, end_emotion, steps=30, start_intensity=1.0, end_intensity=1.0):
    """
    Generate a sequence of 3DMM parameters that transition from one emotion to another.
    
    Args:
        source_params: Source identity parameters
        start_emotion (str): Starting emotion name
        end_emotion (str): Target emotion name
        steps (int): Number of frames for the transition
        start_intensity (float): Intensity of starting emotion (0.0 to 1.0)
        end_intensity (float): Intensity of target emotion (0.0 to 1.0)
        
    Returns:
        List of parameter tensors for each step
    """
    start_params = EMOTION_PARAMS[start_emotion] * start_intensity
    end_params = EMOTION_PARAMS[end_emotion] * end_intensity
    
    # Create interpolation sequence
    param_sequence = []
    for i in range(steps):
        t = i / (steps - 1) if steps > 1 else 1.0  # Interpolation factor (0 to 1)
        emotion_params = start_params * (1 - t) + end_params * t
        
        # Create a copy of source parameters
        params = source_params.clone()
        
        # Apply emotion parameters to expression coefficients
        expression_start_idx = 80
        expression_end_idx = 144
        params[:, expression_start_idx:expression_end_idx] = torch.tensor(
            emotion_params, 
            dtype=torch.float32, 
            device=source_params.device
        ).unsqueeze(0)
        
        param_sequence.append(params)
    
    return param_sequence

if __name__ == '__main__':
    # Arguments
    parser = ArgumentParser()
    parser.add_argument('--config', type=str, default='config/face_demo.yaml')
    parser.add_argument('--checkpoint', type=str, default=None)
    parser.add_argument('--name', type=str, default='face')
    parser.add_argument('--source_img', type=str, required=True, help='Path to source image')
    parser.add_argument('--output_dir', type=str, default='./emotion_results/')
    parser.add_argument('--start_emotion', type=str, default='neutral', 
                        choices=['neutral', 'happy', 'sad', 'angry', 'fear', 'surprise'],
                        help='Starting emotion')
    parser.add_argument('--end_emotion', type=str, default='happy', 
                        choices=['neutral', 'happy', 'sad', 'angry', 'fear', 'surprise'],
                        help='Target emotion')
    parser.add_argument('--start_intensity', type=float, default=0.2, help='Starting emotion intensity (0-1)')
    parser.add_argument('--end_intensity', type=float, default=1.0, help='Target emotion intensity (0-1)')
    parser.add_argument('--steps', type=int, default=60, help='Number of frames for the transition')
    parser.add_argument('--no_resume', action='store_true')
    parser.add_argument('--local_rank', type=int, default=0)
    args = parser.parse_args()

    print(f"Using source image: {args.source_img}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load config
    with open(args.config) as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)

    # Set up model
    from models.projected_model import fsModel
    from models.networks import Net3DMM, define_G

    net_3dmm = Net3DMM().cuda().eval()
    net_G = define_G(input_nc=3, output_nc=3, ngf=64, netG='unet_256',
                     norm='instance', use_dropout=False, init_type='normal', init_gain=0.02)
    net_G = net_G.cuda().eval()

    # Load model
    model = fsModel(config, net_G, net_3dmm, device=torch.device('cuda'))
    model.eval()

    if args.checkpoint is None:
        args.checkpoint = os.path.join('checkpoints', args.name)
    ckpt = torch.load(args.checkpoint, map_location=lambda storage, loc: storage)
    
    # Load checkpoint weights
    if not args.no_resume:
        model.G.load_state_dict(ckpt['G'])
        model.netArc.load_state_dict(ckpt['Arc'])
    print(f'Model checkpoint loaded from {args.checkpoint}')

    # Load source image
    source_img = Image.open(args.source_img).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    source_tensor = transform(source_img).unsqueeze(0).cuda()
    
    print("Extracting identity parameters...")
    with torch.no_grad():
        source_params = model.netArc(source_tensor)
    
    # Generate parameter sequence
    print(f"Generating parameter sequence from {args.start_emotion} to {args.end_emotion}...")
    param_sequence = interpolate_emotions(
        source_params,
        args.start_emotion, 
        args.end_emotion, 
        steps=args.steps,
        start_intensity=args.start_intensity,
        end_intensity=args.end_intensity
    )
    
    # Generate video
    output_path = os.path.join(
        args.output_dir, 
        f"{args.start_emotion}_{args.start_intensity:.1f}_to_{args.end_emotion}_{args.end_intensity:.1f}.mp4"
    )
    
    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter(output_path, fourcc, 30, (256, 256))
    
    # Generate frames
    print(f"Rendering {args.steps} frames...")
    with torch.no_grad():
        for params in tqdm(param_sequence):
            # Generate frame
            output = model.G(source_tensor, params)
            
            # Convert to image and save to video
            output_img = output.squeeze(0).cpu().numpy()
            output_img = (output_img * 0.5 + 0.5) * 255
            output_img = output_img.transpose(1, 2, 0).astype(np.uint8)
            
            # BGR for OpenCV
            output_img = cv2.cvtColor(output_img, cv2.COLOR_RGB2BGR)
            video_writer.write(output_img)
    
    video_writer.release()
    print(f"Video saved to {output_path}")