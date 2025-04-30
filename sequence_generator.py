import os
import sys
import argparse
import numpy as np
import torch
import yaml
import json
from tqdm import tqdm
from PIL import Image
from torchvision import transforms

# Add Deep3DFaceRecon path to system path
DEEP3D_PATH = "/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main/Deep3DFaceRecon_pytorch/"
sys.path.append(DEEP3D_PATH)

# Import PIRender modules
from models.networks import Net3DMM, define_G
from models.projected_model import fsModel

# Import emotion parameters from the emotion control script
from emotion_control import EMOTION_PARAMS, load_model, create_3dmm_params

def generate_complex_sequence(source_params, emotion_list, intensity_list=None, steps_per_transition=30):
    """
    Generate a sequence transitioning through multiple emotions with specified intensities.
    
    Args:
        source_params: Source identity parameters
        emotion_list (list): List of emotion names to transition through
        intensity_list (list, optional): List of intensities for each emotion (0.0 to 1.0)
                                        If None, all emotions use intensity 1.0
        steps_per_transition (int): Number of frames for each transition
        
    Returns:
        List of 3DMM parameter tensors for the full sequence
    """
    if intensity_list is None:
        intensity_list = [1.0] * len(emotion_list)
    
    assert len(emotion_list) == len(intensity_list), "Emotion list and intensity list must have the same length"
    
    full_sequence = []
    
    # Generate transitions between each pair of consecutive emotions
    for i in range(len(emotion_list) - 1):
        start_emotion = emotion_list[i]
        end_emotion = emotion_list[i + 1]
        start_intensity = intensity_list[i]
        end_intensity = intensity_list[i + 1]
        
        # Get the emotion parameters
        start_params = EMOTION_PARAMS[start_emotion] * start_intensity
        end_params = EMOTION_PARAMS[end_emotion] * end_intensity
        
        # Create interpolation sequence for this transition
        for j in range(steps_per_transition):
            t = j / (steps_per_transition - 1) if steps_per_transition > 1 else 1.0  # Interpolation factor (0 to 1)
            emotion_params = start_params * (1 - t) + end_params * t
            param = create_3dmm_params(source_params, emotion_params)
            full_sequence.append(param)
    
    return full_sequence

def save_sequence_to_file(sequence, output_file):
    """Save the generated sequence to a torch file for later use"""
    torch.save(sequence, output_file)
    print(f"Sequence saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description="Generate Complex Emotion Sequence for PIRender")
    parser.add_argument("--config", type=str, default="./config/face_demo.yaml", help="Path to the config file")
    parser.add_argument("--checkpoint", type=str, 
                        default="/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main/result/face/epoch_00190_iteration_000400000_checkpoint.pt", 
                        help="Path to the model checkpoint")
    parser.add_argument("--source_img", type=str, required=True, help="Path to source image")
    parser.add_argument("--output_file", type=str, default="emotion_sequence.pt", 
                        help="File to save the generated sequence")
    parser.add_argument("--emotions", type=str, nargs='+', 
                        default=["neutral", "happy", "sad", "angry", "fear", "surprise", "neutral"],
                        help="List of emotions to transition through")
    parser.add_argument("--intensities", type=float, nargs='+', 
                        default=None,
                        help="List of intensities for each emotion (0.0 to 1.0)")
    parser.add_argument("--steps_per_transition", type=int, default=30,
                        help="Number of frames for each transition")
    parser.add_argument("--json_config", type=str, default=None,
                        help="JSON file with emotion sequence configuration")
    parser.add_argument("--gpu_ids", type=str, default="0", help="GPU IDs")
    
    args = parser.parse_args()
    
    # Set device
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu_ids
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.load(f, Loader=yaml.SafeLoader)
    
    # If JSON config file is provided, load the configuration from there
    if args.json_config and os.path.exists(args.json_config):
        with open(args.json_config, 'r') as f:
            json_config = json.load(f)
        emotions = json_config.get('emotions', args.emotions)
        intensities = json_config.get('intensities', args.intensities)
        steps_per_transition = json_config.get('steps_per_transition', args.steps_per_transition)
    else:
        emotions = args.emotions
        intensities = args.intensities
        steps_per_transition = args.steps_per_transition
    
    # Validate emotions
    valid_emotions = list(EMOTION_PARAMS.keys())
    for emotion in emotions:
        if emotion not in valid_emotions:
            raise ValueError(f"Invalid emotion: {emotion}. Valid emotions are: {valid_emotions}")
    
    # Load model
    model = load_model(config, args.checkpoint, device)
    
    # Load source image and extract identity parameters
    source_img = Image.open(args.source_img).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])
    ])
    source_tensor = transform(source_img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        source_params = model.netArc(source_tensor).squeeze()
    
    # Generate the sequence
    sequence = generate_complex_sequence(source_params, emotions, intensities, steps_per_transition)
    
    # Save the sequence
    save_sequence_to_file(sequence, args.output_file)
    
    # Print summary
    print(f"Generated sequence with {len(sequence)} frames")
    print(f"Emotions: {emotions}")
    print(f"Intensities: {intensities}")

if __name__ == "__main__":
    main()