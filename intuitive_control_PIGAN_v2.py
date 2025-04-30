import os
import argparse
import numpy as np
from scipy.io import loadmat

import torch
import torchvision.transforms.functional as F
import torchvision.transforms as transforms

from config import Config
from util.logging import init_logging, make_logging_dir
from util.distributed import init_dist
from util.trainer import get_model_optimizer_and_scheduler, set_random_seed, get_trainer
from util.distributed import master_only_print as print
from data.image_dataset import ImageDataset
from inference import write2video


def parse_args():
    parser = argparse.ArgumentParser(description='Training')
    parser.add_argument('--config', default='./config/face.yaml')
    parser.add_argument('--name', default=None)
    parser.add_argument('--checkpoints_dir', default='result',
                        help='Dir for saving logs and models.')
    parser.add_argument('--seed', type=int, default=0, help='Random seed.')
    parser.add_argument('--which_iter', type=int, default=None)
    parser.add_argument('--no_resume', action='store_true')
    parser.add_argument('--input_name', type=str)
    parser.add_argument('--local_rank', type=int, default=0)
    parser.add_argument('--single_gpu', action='store_true')
    parser.add_argument('--output_dir', type=str)
    
    # Add emotion arguments
    parser.add_argument('--happy', action='store_true', help='Use happiness emotion')
    parser.add_argument('--sad', action='store_true', help='Use sadness emotion')
    parser.add_argument('--angry', action='store_true', help='Use anger emotion')
    parser.add_argument('--fear', action='store_true', help='Use fear emotion')
    parser.add_argument('--surprise', action='store_true', help='Use surprise emotion')
    parser.add_argument('--intensity', type=int, default=3, 
                        help='Emotion intensity (1-5, where 5 is most intense)')

    args = parser.parse_args()
    return args

def get_control(input_name, args):
    control_dict = {}
    
    # Load facial expressions from the .mat file
    expression = loadmat('{}/expression.mat'.format(input_name))

    # Base expressions (ensure to squeeze out extra dimensions if needed)
    control_dict['expression_center'] = torch.tensor(expression['expression_center'])[0]
    control_dict['expression_mouth'] = torch.tensor(expression['expression_mouth'])[0]
    control_dict['expression_eyebrow'] = torch.tensor(expression['expression_eyebrow'])[0]
    control_dict['expression_eyes'] = torch.tensor(expression['expression_eyes'])[0]
    
    # Get intensity scale factor (maps 1->1.0, 3->1.5, 5->2.0)
    intensity_scale = args.intensity * 0.25 + 0.75  
    
    # Define the selected emotion based on command line flags.
    # We start from the neutral (center) expression and add a weighted difference.
    selected_expression = 'expression_center'  # Default to neutral
    emotion_name = "Neutral"
    
    if args.happy:
        control_dict['expression_happiness'] = control_dict['expression_center'] + \
            (control_dict['expression_mouth'] - control_dict['expression_center']) * intensity_scale * 0.8
        selected_expression = 'expression_happiness'
        emotion_name = "Happiness"
    
    elif args.sad:
        # For sadness, use slight downward adjustments from eyebrows, eyes, and mouth relative to center.
        control_dict['expression_sadness'] = control_dict['expression_center'] + \
            (control_dict['expression_eyebrow'] - control_dict['expression_center']) * (-0.6 * intensity_scale) + \
            (control_dict['expression_eyes'] - control_dict['expression_center']) * (0.1 * intensity_scale) + \
            (control_dict['expression_mouth'] - control_dict['expression_center']) * (-1.1 * intensity_scale)
        selected_expression = 'expression_sadness'
        emotion_name = "Sadness"
    
    elif args.angry:
        # For anger: exaggerate eyebrow movement (e.g. furrowed brows),
        # moderate increase in eye changes, and a slight frown for the mouth.
        control_dict['expression_anger'] = control_dict['expression_center'] + \
            (control_dict['expression_eyebrow'] - control_dict['expression_center']) * (-1.1 * intensity_scale) + \
            (control_dict['expression_eyes'] - control_dict['expression_center']) * (1.4 * intensity_scale) + \
            (control_dict['expression_mouth'] - control_dict['expression_center']) * (-1 * intensity_scale)
        selected_expression = 'expression_anger'
        emotion_name = "Anger"
        
    elif args.fear:
        # For fear: widen the eyes and slightly raise the eyebrows;
        # use a milder change for the mouth.
        control_dict['expression_fear'] = control_dict['expression_center'] + \
            (control_dict['expression_eyes'] - control_dict['expression_center']) * (-2 * intensity_scale) + \
            (control_dict['expression_eyebrow'] - control_dict['expression_center']) * (0 * intensity_scale) + \
            (control_dict['expression_mouth'] - control_dict['expression_center']) * (0 * intensity_scale) + \
            (control_dict['expression_open_mouth'] - control_dict['expression_center']) * (1 * intensity_scale)
        selected_expression = 'expression_fear'
        emotion_name = "Fear"
    
    elif args.surprise:
        # For surprise: open mouth wider, raise both the eyes and eyebrows.
        control_dict['expression_surprise'] = control_dict['expression_center'] + \
            (control_dict['expression_eyes'] - control_dict['expression_center']) * (0.9 * intensity_scale) + \
            (control_dict['expression_eyebrow'] - control_dict['expression_center']) * (0.7 * intensity_scale) + \
            (control_dict['expression_mouth'] - control_dict['expression_center']) * (1.3 * intensity_scale)
        selected_expression = 'expression_surprise'
        emotion_name = "Surprise"
    
    # Simplified animation sequence: directly from input image to chosen emotion.
    sort_exp_control = [selected_expression]
    
    print(f"Selected Emotion: {emotion_name}, Intensity: {args.intensity}/5")
    
    return control_dict, sort_exp_control

if __name__ == '__main__':
    args = parse_args()
    set_random_seed(args.seed)
    opt = Config(args.config, args, is_train=False)

    if not args.single_gpu:
        opt.local_rank = args.local_rank
        init_dist(opt.local_rank)    
        opt.device = torch.cuda.current_device()

    # Create a visualizer logging system
    date_uid, logdir = init_logging(opt)
    opt.logdir = logdir
    make_logging_dir(logdir, date_uid)

    # Create a model (generator and EMA version)
    net_G, net_G_ema, opt_G, sch_G = get_model_optimizer_and_scheduler(opt)
    trainer = get_trainer(opt, net_G, net_G_ema, opt_G, sch_G, None)

    current_epoch, current_iteration = trainer.load_checkpoint(opt, args.which_iter)
    net_G = trainer.net_G_ema.eval()

    output_dir = os.path.join(
        args.output_dir, 
        'epoch_{:05}_iteration_{:09}'.format(current_epoch, current_iteration)
    )
    os.makedirs(output_dir, exist_ok=True)
    
    image_dataset = ImageDataset(opt.data, args.input_name)

    # Get emotion controls based on command line arguments.
    control_dict, sort_exp_control = get_control(args.input_name, args)
    
    for _ in range(len(image_dataset)):
        with torch.no_grad():
            data = image_dataset.next_image()
            num = 60  # Increased number of frames for a slower, longer emotion transition
            output_images = []     
            
            # Expression control only (no rotation)
            current = data['target_semantics'][0, :64, 0]
            
            for control in sort_exp_control: 
                for i in range(num):
                    # Gradually change the expression from the current state to the target emotion.
                    expression = (control_dict[control] - current) * i / (num - 1) + current
                    data['target_semantics'][:, :64, :] = expression[None, :, None]
                    
                    # Keep the rotation parameters constant.
                    output_dict = net_G(data['source_image'].cuda(), data['target_semantics'].cuda())
                    output_images.append(output_dict['fake_image'].cpu().clamp_(-1, 1))
                    
                current = expression
                
            output_images = torch.cat(output_images, 0)
            print('write results to file {}/{}'.format(output_dir, data['name']))
            write2video('{}/{}'.format(output_dir, data['name']), output_images)

