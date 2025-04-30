import os
import numpy as np
import cv2
import argparse
from datetime import datetime
import sys
import warnings
warnings.filterwarnings("ignore")

def create_enhanced_animation(image_path, emotion, intensity=0.5, frames=30):
    """
    Create an enhanced animation for facial emotions with more pronounced effects.
    
    Args:
        image_path: Path to the source image
        emotion: Target emotion (happy, sad, etc.)
        intensity: Intensity of the effect (0-1)
        frames: Number of frames to generate
        
    Returns:
        List of frames (BGR format)
    """
    # Ensure frames is an integer
    frames = int(frames)
    
    # Read the image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    # Convert to RGB for processing
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Resize to a standard size
    img_rgb = cv2.resize(img_rgb, (512, 512), interpolation=cv2.INTER_LANCZOS4)
    
    # Create frames array
    result_frames = []
    height, width = img_rgb.shape[:2]
    
    # Estimated face regions based on typical proportions
    # These values are more accurate for a frontal face
    face_top = height // 6
    face_bottom = height * 5 // 6
    face_left = width // 6
    face_right = width * 5 // 6
    
    # Eye region estimation (more precise)
    eye_top = height // 5
    eye_bottom = height * 2 // 5
    left_eye_left = width // 5
    left_eye_right = width * 2 // 5
    right_eye_left = width * 3 // 5
    right_eye_right = width * 4 // 5
    
    # Mouth region estimation (more precise)
    mouth_top = height * 3 // 5
    mouth_bottom = height * 4 // 5
    mouth_left = width // 3
    mouth_right = width * 2 // 3
    
    # Create frames based on the emotion
    for i in range(frames):
        # Calculate the animation progress (0 to 1)
        progress = i / (frames - 1)
        
        # Apply smooth easing (quintic ease in-out)
        t = progress
        t_smooth = t*t*t*(t*(t*6 - 15) + 10)
        
        # Scale by intensity
        effect_strength = t_smooth * intensity
        
        # Create a copy of the original image for this frame
        frame = img_rgb.copy()
        
        # Apply emotion-specific effects
        if emotion == 'happy':
            # ENHANCED HAPPY EFFECT
            
            # 1. Extract mouth region for more precise manipulation
            mouth_region = frame[mouth_top:mouth_bottom, mouth_left:mouth_right].copy()
            m_height, m_width = mouth_region.shape[:2]
            
            # 2. Create a mesh grid for the mouth region
            x, y = np.meshgrid(np.arange(m_width), np.arange(m_height))
            
            # 3. Apply a more pronounced smile curve
            # This creates a stronger upward curve at the corners
            center_x = m_width // 2
            # Stronger parabolic effect
            y_offset = np.square((x - center_x) / (m_width / 2)) * (20 * effect_strength)
            
            # 4. Add horizontal compression at corners to create a wider smile
            x_offset = np.zeros_like(x, dtype=np.float32)
            # Create a compression effect at the corners
            corner_effect = np.square((x - center_x) / (m_width / 2))
            x_offset = corner_effect * (5 * effect_strength) * np.sign(center_x - x)
            
            # 5. Ensure offsets are within bounds and create mapping
            y_new = np.clip(y - y_offset, 0, m_height-1).astype(np.float32)
            x_new = np.clip(x - x_offset, 0, m_width-1).astype(np.float32)
            
            # 6. Apply the warp
            warped_mouth = cv2.remap(mouth_region, x_new, y_new, cv2.INTER_LINEAR)
            
            # 7. Put the warped region back
            frame[mouth_top:mouth_bottom, mouth_left:mouth_right] = warped_mouth
            
            # 8. Enhance cheeks (slight raise and brighten)
            left_cheek = frame[mouth_top-30:mouth_top, mouth_left-30:mouth_left+30]
            right_cheek = frame[mouth_top-30:mouth_top, mouth_right-30:mouth_right+30]
            
            # Brighten cheeks
            cheek_brightness = int(20 * effect_strength)
            left_cheek = cv2.convertScaleAbs(left_cheek, alpha=1, beta=cheek_brightness)
            right_cheek = cv2.convertScaleAbs(right_cheek, alpha=1, beta=cheek_brightness)
            
            # Apply back
            frame[mouth_top-30:mouth_top, mouth_left-30:mouth_left+30] = left_cheek
            frame[mouth_top-30:mouth_top, mouth_right-30:mouth_right+30] = right_cheek
            
            # 9. Slightly narrow eyes (genuine smile effect)
            # Left eye
            left_eye = frame[eye_top:eye_bottom, left_eye_left:left_eye_right].copy()
            le_height, le_width = left_eye.shape[:2]
            
            # Resize vertically to make eyes narrower
            eye_factor = max(0.95, 1.0 - 0.15 * effect_strength)
            resized_left_eye = cv2.resize(left_eye, (le_width, int(le_height * eye_factor)))
            
            # Add padding to maintain original size
            pad_top = (le_height - resized_left_eye.shape[0]) // 2
            padded_left_eye = np.zeros_like(left_eye)
            padded_left_eye[pad_top:pad_top+resized_left_eye.shape[0], :] = resized_left_eye
            
            # Apply back
            frame[eye_top:eye_bottom, left_eye_left:left_eye_right] = padded_left_eye
            
            # Right eye (same process)
            right_eye = frame[eye_top:eye_bottom, right_eye_left:right_eye_right].copy()
            re_height, re_width = right_eye.shape[:2]
            
            resized_right_eye = cv2.resize(right_eye, (re_width, int(re_height * eye_factor)))
            
            pad_top = (re_height - resized_right_eye.shape[0]) // 2
            padded_right_eye = np.zeros_like(right_eye)
            padded_right_eye[pad_top:pad_top+resized_right_eye.shape[0], :] = resized_right_eye
            
            frame[eye_top:eye_bottom, right_eye_left:right_eye_right] = padded_right_eye
            
            # 10. Overall slight brightness increase
            brightness = int(10 * effect_strength)
            frame = cv2.convertScaleAbs(frame, alpha=1.0, beta=brightness)
            
        elif emotion == 'sad':
            # ENHANCED SAD EFFECT
            
            # 1. Extract mouth region for precise manipulation
            mouth_region = frame[mouth_top:mouth_bottom, mouth_left:mouth_right].copy()
            m_height, m_width = mouth_region.shape[:2]
            
            # 2. Create a mesh grid for the mouth region
            x, y = np.meshgrid(np.arange(m_width), np.arange(m_height))
            
            # 3. Apply inverted curve for frown
            center_x = m_width // 2
            # Stronger downward curve at corners
            y_offset = -np.square((x - center_x) / (m_width / 2)) * (15 * effect_strength)
            
            # 4. Ensure offsets are within bounds
            y_new = np.clip(y - y_offset, 0, m_height-1).astype(np.float32)
            x_new = x.astype(np.float32)
            
            # 5. Apply the warp
            warped_mouth = cv2.remap(mouth_region, x_new, y_new, cv2.INTER_LINEAR)
            
            # 6. Put the warped region back
            frame[mouth_top:mouth_bottom, mouth_left:mouth_right] = warped_mouth
            
            # 7. Inner eyebrow raise (sad expression)
            left_brow = frame[eye_top-20:eye_top, left_eye_left:left_eye_right].copy()
            right_brow = frame[eye_top-20:eye_top, right_eye_left:right_eye_right].copy()
            
            # Create a mesh grid for eyebrows
            lb_h, lb_w = left_brow.shape[:2]
            x_lb, y_lb = np.meshgrid(np.arange(lb_w), np.arange(lb_h))
            
            # Apply inner brow raise
            center_x_lb = lb_w // 2
            # More raise on inner part
            y_offset_lb = np.square((x_lb - center_x_lb) / (lb_w / 2)) * (8 * effect_strength)
            # Ensure offsets are within bounds
            y_new_lb = np.clip(y_lb + y_offset_lb, 0, lb_h-1).astype(np.float32)
            x_new_lb = x_lb.astype(np.float32)
            
            # Apply the warp
            warped_left_brow = cv2.remap(left_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            warped_right_brow = cv2.remap(right_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            
            # Apply back
            frame[eye_top-20:eye_top, left_eye_left:left_eye_right] = warped_left_brow
            frame[eye_top-20:eye_top, right_eye_left:right_eye_right] = warped_right_brow
            
            # 8. Slightly darken the image
            darkness = 1.0 - 0.15 * effect_strength
            frame = cv2.convertScaleAbs(frame, alpha=darkness, beta=0)
            
        elif emotion == 'surprise':
            # ENHANCED SURPRISE EFFECT
            
            # 1. Widen eyes significantly
            # Left eye
            left_eye = frame[eye_top:eye_bottom, left_eye_left:left_eye_right].copy()
            le_height, le_width = left_eye.shape[:2]
            
            # Resize vertically to make eyes wider
            eye_factor = 1.0 + 0.3 * effect_strength
            resized_left_eye = cv2.resize(left_eye, (le_width, int(le_height * eye_factor)))
            
            # Take the center portion to maintain original size
            if resized_left_eye.shape[0] > le_height:
                start = (resized_left_eye.shape[0] - le_height) // 2
                resized_left_eye = resized_left_eye[start:start+le_height, :]
            
            # Apply back
            frame[eye_top:eye_bottom, left_eye_left:left_eye_right] = resized_left_eye
            
            # Right eye (same process)
            right_eye = frame[eye_top:eye_bottom, right_eye_left:right_eye_right].copy()
            re_height, re_width = right_eye.shape[:2]
            
            resized_right_eye = cv2.resize(right_eye, (re_width, int(re_height * eye_factor)))
            
            if resized_right_eye.shape[0] > re_height:
                start = (resized_right_eye.shape[0] - re_height) // 2
                resized_right_eye = resized_right_eye[start:start+re_height, :]
            
            frame[eye_top:eye_bottom, right_eye_left:right_eye_right] = resized_right_eye
            
            # 2. Raise eyebrows
            left_brow = frame[eye_top-25:eye_top, left_eye_left:left_eye_right].copy()
            right_brow = frame[eye_top-25:eye_top, right_eye_left:right_eye_right].copy()
            
            # Simply shift eyebrows up
            shift_amount = int(8 * effect_strength)
            if shift_amount > 0:
                # Create shifted eyebrows with padding
                shifted_left_brow = np.zeros_like(left_brow)
                shifted_left_brow[:-shift_amount] = left_brow[shift_amount:]
                
                shifted_right_brow = np.zeros_like(right_brow)
                shifted_right_brow[:-shift_amount] = right_brow[shift_amount:]
                
                # Apply back
                frame[eye_top-25:eye_top, left_eye_left:left_eye_right] = shifted_left_brow
                frame[eye_top-25:eye_top, right_eye_left:right_eye_right] = shifted_right_brow
            
            # 3. Open mouth
            mouth_region = frame[mouth_top:mouth_bottom, mouth_left:mouth_right].copy()
            m_height, m_width = mouth_region.shape[:2]
            
            # Create a mesh grid for the mouth region
            x, y = np.meshgrid(np.arange(m_width), np.arange(m_height))
            
            # Apply vertical stretching in the center
            center_x = m_width // 2
            center_y = m_height // 2
            
            # Calculate distance from center (horizontally)
            dist_from_center = np.abs(x - center_x) / (m_width / 2)
            
            # Create a vertical stretching effect stronger in the center
            stretch_factor = (1.0 - dist_from_center) * (15 * effect_strength)
            
            # Above center, shift up; below center, shift down
            y_offset = np.zeros_like(y, dtype=np.float32)
            above_center = y < center_y
            below_center = y >= center_y
            
            y_offset[above_center] = -stretch_factor[above_center]
            y_offset[below_center] = stretch_factor[below_center]
            
            # Ensure offsets are within bounds
            y_new = np.clip(y + y_offset, 0, m_height-1).astype(np.float32)
            x_new = x.astype(np.float32)
            
            # Apply the warp
            warped_mouth = cv2.remap(mouth_region, x_new, y_new, cv2.INTER_LINEAR)
            
            # Put the warped region back
            frame[mouth_top:mouth_bottom, mouth_left:mouth_right] = warped_mouth
            
            # 4. Increase brightness and contrast
            alpha = 1.0 + 0.2 * effect_strength  # Contrast
            beta = int(15 * effect_strength)     # Brightness
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
            
        elif emotion == 'angry':
            # ENHANCED ANGRY EFFECT
            
            # 1. Lower and furrow eyebrows
            left_brow = frame[eye_top-25:eye_top, left_eye_left:left_eye_right].copy()
            right_brow = frame[eye_top-25:eye_top, right_eye_left:right_eye_right].copy()
            
            # Create a mesh grid for eyebrows
            lb_h, lb_w = left_brow.shape[:2]
            x_lb, y_lb = np.meshgrid(np.arange(lb_w), np.arange(lb_h))
            
            # Apply inner brow lower and furrow
            center_x_lb = lb_w // 2
            
            # More lowering on inner part (V shape)
            y_offset_lb = -np.square((x_lb - center_x_lb) / (lb_w / 2)) * (10 * effect_strength)
            
            # Ensure offsets are within bounds
            y_new_lb = np.clip(y_lb - y_offset_lb, 0, lb_h-1).astype(np.float32)
            x_new_lb = x_lb.astype(np.float32)
            
            # Apply the warp
            warped_left_brow = cv2.remap(left_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            warped_right_brow = cv2.remap(right_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            
            # Apply back
            frame[eye_top-25:eye_top, left_eye_left:left_eye_right] = warped_left_brow
            frame[eye_top-25:eye_top, right_eye_left:right_eye_right] = warped_right_brow
            
            # 2. Tighten mouth (slight compression)
            mouth_region = frame[mouth_top:mouth_bottom, mouth_left:mouth_right].copy()
            m_height, m_width = mouth_region.shape[:2]
            
            # Compress mouth slightly
            compression = 0.9 + 0.1 * (1 - effect_strength)
            resized_mouth = cv2.resize(mouth_region, (int(m_width * compression), m_height))
            
            # Center it
            padded_mouth = np.zeros_like(mouth_region)
            x_offset = (m_width - resized_mouth.shape[1]) // 2
            padded_mouth[:, x_offset:x_offset+resized_mouth.shape[1]] = resized_mouth
            
            # Apply back
            frame[mouth_top:mouth_bottom, mouth_left:mouth_right] = padded_mouth
            
            # 3. Add reddish tint
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv)
            
            # Increase saturation
            s = cv2.convertScaleAbs(s, alpha=1 + 0.4 * effect_strength, beta=0)
            
            # Slight hue shift toward red
            h = cv2.convertScaleAbs(h, alpha=1, beta=-5 * effect_strength)
            
            hsv = cv2.merge([h, s, v])
            tinted = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
            
            # Blend the tinted image with original
            frame = cv2.addWeighted(frame, 1 - 0.5 * effect_strength, tinted, 0.5 * effect_strength, 0)
            
            # 4. Slightly darken
            frame = cv2.convertScaleAbs(frame, alpha=1.0 - 0.1 * effect_strength, beta=0)
            
        elif emotion == 'fear':
            # ENHANCED FEAR EFFECT
            
            # 1. Widen eyes
            # Left eye
            left_eye = frame[eye_top:eye_bottom, left_eye_left:left_eye_right].copy()
            le_height, le_width = left_eye.shape[:2]
            
            # Resize vertically to make eyes wider
            eye_factor = 1.0 + 0.25 * effect_strength
            resized_left_eye = cv2.resize(left_eye, (le_width, int(le_height * eye_factor)))
            
            # Take the center portion to maintain original size
            if resized_left_eye.shape[0] > le_height:
                start = (resized_left_eye.shape[0] - le_height) // 2
                resized_left_eye = resized_left_eye[start:start+le_height, :]
            
            # Apply back
            frame[eye_top:eye_bottom, left_eye_left:left_eye_right] = resized_left_eye
            
            # Right eye (same process)
            right_eye = frame[eye_top:eye_bottom, right_eye_left:right_eye_right].copy()
            re_height, re_width = right_eye.shape[:2]
            
            resized_right_eye = cv2.resize(right_eye, (re_width, int(re_height * eye_factor)))
            
            if resized_right_eye.shape[0] > re_height:
                start = (resized_right_eye.shape[0] - re_height) // 2
                resized_right_eye = resized_right_eye[start:start+re_height, :]
            
            frame[eye_top:eye_bottom, right_eye_left:right_eye_right] = resized_right_eye
            
            # 2. Raise eyebrows
            left_brow = frame[eye_top-25:eye_top, left_eye_left:left_eye_right].copy()
            right_brow = frame[eye_top-25:eye_top, right_eye_left:right_eye_right].copy()
            
            # Create a mesh grid for eyebrows
            lb_h, lb_w = left_brow.shape[:2]
            x_lb, y_lb = np.meshgrid(np.arange(lb_w), np.arange(lb_h))
            
            # Apply brow raise with inner parts raised more
            center_x_lb = lb_w // 2
            
            # Inverse parabolic raise (inner parts up more)
            y_offset_lb = (1 - np.square((x_lb - center_x_lb) / (lb_w / 2))) * (8 * effect_strength)
            
            # Ensure offsets are within bounds
            y_new_lb = np.clip(y_lb - y_offset_lb, 0, lb_h-1).astype(np.float32)
            x_new_lb = x_lb.astype(np.float32)
            
            # Apply the warp
            warped_left_brow = cv2.remap(left_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            warped_right_brow = cv2.remap(right_brow, x_new_lb, y_new_lb, cv2.INTER_LINEAR)
            
            # Apply back
            frame[eye_top-25:eye_top, left_eye_left:left_eye_right] = warped_left_brow
            frame[eye_top-25:eye_top, right_eye_left:right_eye_right] = warped_right_brow
            
            # 3. Tense mouth (slight compression and downward curve)
            mouth_region = frame[mouth_top:mouth_bottom, mouth_left:mouth_right].copy()
            m_height, m_width = mouth_region.shape[:2]
            
            # Create a mesh grid for the mouth region
            x, y = np.meshgrid(np.arange(m_width), np.arange(m_height))
            
            # Apply slight downward curve
            center_x = m_width // 2
            
            # Slight downward curve
            y_offset = -np.square((x - center_x) / (m_width / 2)) * (5 * effect_strength)
            
            # Ensure offsets are within bounds
            y_new = np.clip(y - y_offset, 0, m_height-1).astype(np.float32)
            x_new = x.astype(np.float32)
            
            # Apply the warp
            warped_mouth = cv2.remap(mouth_region, x_new, y_new, cv2.INTER_LINEAR)
            
            # Compress mouth slightly
            compression = 0.95 + 0.05 * (1 - effect_strength)
            resized_mouth = cv2.resize(warped_mouth, (int(m_width * compression), m_height))
            
            # Center it
            padded_mouth = np.zeros_like(mouth_region)
            x_offset = (m_width - resized_mouth.shape[1]) // 2
            padded_mouth[:, x_offset:x_offset+resized_mouth.shape[1]] = resized_mouth
            
            # Apply back
            frame[mouth_top:mouth_bottom, mouth_left:mouth_right] = padded_mouth
            
            # 4. Make face slightly paler
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            h, s, v = cv2.split(hsv)
            
            # Decrease saturation (make paler)
            s = cv2.convertScaleAbs(s, alpha=1 - 0.3 * effect_strength, beta=0)
            
            # Increase value slightly (lighter)
            v = cv2.convertScaleAbs(v, alpha=1, beta=10 * effect_strength)
            
            hsv = cv2.merge([h, s, v])
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        # Apply a subtle blur to make it look smoother
        frame = cv2.GaussianBlur(frame, (3, 3), 0.5)
        
        # Convert back to BGR for saving
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        result_frames.append(frame_bgr)
    
    return result_frames

def create_emotion_video(source_image, target_emotion, intensity, output_dir, frames=30):
    """
    Create a video showing emotion transition.
    
    Args:
        source_image: Path to source image
        target_emotion: Target emotion ('happy', 'sad', 'angry', 'fear', 'surprise', 'neutral')
        intensity: Intensity of the emotion (0-1)
        output_dir: Directory to save the output
        frames: Number of frames for the transition
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate animation frames
    print(f"Creating {target_emotion} animation with intensity {intensity}...")
    frames_list = create_enhanced_animation(source_image, target_emotion, intensity, frames)
    
    # Save the original image
    img = cv2.imread(source_image)
    if img is not None:
        processed_img = cv2.resize(img, (512, 512), interpolation=cv2.INTER_LANCZOS4)
        cv2.imwrite(os.path.join(output_dir, "processed_source.jpg"), processed_img)
    
    # If we have frames, create and save the video
    if frames_list:
        # Save individual frames
        for i, frame in enumerate(frames_list):
            cv2.imwrite(os.path.join(output_dir, f'{i:04d}.jpg'), frame)
        
        # Create video file
        video_path = os.path.join(output_dir, f'{target_emotion}_{intensity}.mp4')
        height, width = frames_list[0].shape[:2]
        video = cv2.VideoWriter(video_path, 
                              cv2.VideoWriter_fourcc(*'mp4v'), 
                              30, (width, height))
        for frame in frames_list:
            video.write(frame)
        video.release()
        
        print(f"Video saved to: {video_path}")
        return video_path
    else:
        print("Failed to generate frames.")
        return None

def create_emotion_chain(source_image, emotion_sequence, intensities, output_dir, frames_per_transition=30):
    """Create a video showing a chain of emotion transitions."""
    if len(emotion_sequence) < 2:
        print("Error: Need at least 2 emotions for a chain")
        return None
    
    # Normalize intensities
    if isinstance(intensities, (int, float)):
        intensities = [intensities] * len(emotion_sequence)
    elif len(intensities) != len(emotion_sequence):
        print("Error: Number of intensities must match number of emotions")
        return None
    
    # Create main output directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    main_output_dir = os.path.join(output_dir, f"emotion_chain_{timestamp}")
    os.makedirs(main_output_dir, exist_ok=True)
    
    # Process each emotion
    all_frames = []
    
    for i, emotion in enumerate(emotion_sequence):
        if emotion == 'neutral' and i > 0:  # Skip neutral except for the first one
            continue
            
        intensity = intensities[i]
        
        print(f"\nProcessing emotion {i+1}/{len(emotion_sequence)}: {emotion}")
        
        # Create specific output directory for this emotion
        emotion_dir = os.path.join(main_output_dir, f"{i+1}_{emotion}")
        
        # Generate frames for this emotion
        video_path = create_emotion_video(
            source_image,
            emotion,
            intensity,
            emotion_dir,
            frames_per_transition
        )
        
        if video_path:
            # Collect frames from this transition
            frame_dir = emotion_dir
            frame_paths = sorted([os.path.join(frame_dir, f) for f in os.listdir(frame_dir) 
                                if f.endswith('.jpg') and f != 'processed_source.jpg'])
            
            for frame_path in frame_paths:
                frame = cv2.imread(frame_path)
                if frame is not None:
                    all_frames.append(frame)
        else:
            print(f"Failed to process emotion {emotion}")
    
    # Create the final chain video if we have frames
    if all_frames:
        chain_video_path = os.path.join(main_output_dir, f"emotion_chain.mp4")
        height, width = all_frames[0].shape[:2]
        video = cv2.VideoWriter(chain_video_path, 
                              cv2.VideoWriter_fourcc(*'mp4v'), 
                              30, (width, height))
        for frame in all_frames:
            video.write(frame)
        video.release()
        
        print(f"Chain video saved to: {chain_video_path}")
        return chain_video_path
    else:
        print("No frames were generated. Could not create chain video.")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Enhanced Facial Emotion Animation')
    parser.add_argument('--source', type=str, required=True, help='Source image path')
    parser.add_argument('--target_emotion', type=str, required=True, 
                        choices=['happy', 'sad', 'angry', 'fear', 'surprise', 'neutral'],
                        help='Target emotion')
    parser.add_argument('--intensity', type=float, default=0.5, help='Emotion intensity (0-1), default: 0.5')
    parser.add_argument('--output', type=str, default='./emotion_results', help='Output directory')
    parser.add_argument('--frames', type=int, default=30, help='Number of frames for the transition')
    parser.add_argument('--chain', action='store_true', help='Create a chain of emotion transitions')
    parser.add_argument('--emotion_sequence', type=str, nargs='+', 
                        help='Sequence of emotions for chain (e.g., happy sad surprise)')
    parser.add_argument('--intensities', type=float, nargs='+',
                        help='Intensities for each emotion in the chain')
    
    args = parser.parse_args()
    
    # Create timestamp folder
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_dir = os.path.join(args.output, f'{args.target_emotion}_{timestamp}')
    
    try:
        if args.chain:
            # Create a chain of emotion transitions
            if args.emotion_sequence:
                emotion_sequence = args.emotion_sequence
            else:
                # Default sequence
                emotion_sequence = ['neutral', args.target_emotion, 'neutral']
            
            chain_video = create_emotion_chain(
                args.source,
                emotion_sequence,
                args.intensities if args.intensities else args.intensity,
                args.output,
                args.frames
            )
            
            if chain_video:
                print(f"Chain video created: {chain_video}")
        else:
            # Process a single image with a single emotion
            video_path = create_emotion_video(
                args.source, 
                args.target_emotion, 
                args.intensity, 
                output_dir, 
                args.frames
            )
            
            if video_path:
                print(f"Video saved to: {video_path}")
                
                # Print recommendations for better results
                print("\n=== Tips for Better Results ===")
                print("1. Try intensities between 0.5-0.8 for more visible effects")
                print("2. For a more natural look, lower intensity to 0.4-0.6")
                print("3. For smoother transitions, try using '--frames 45'")
                print("4. Try the --chain option to sequence multiple emotions")
            else:
                print("Video creation failed.")
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()