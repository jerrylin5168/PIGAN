#!/bin/bash

# Base directory
BASE_DIR="/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main"

# Configuration paths
CONFIG_PATH="$BASE_DIR/config/face_demo.yaml"
CHECKPOINT_PATH="$BASE_DIR/result/face/epoch_00190_iteration_000400000_checkpoint.pt"

# Create output directory
OUTPUT_DIR="$BASE_DIR/emotion_results"
mkdir -p $OUTPUT_DIR

# Use the specific demo image provided by the user
SOURCE_IMG="/mnt/nfs-scratch/ECEN_403-404/jerrylin5168/PIRender-main/demo_images/id10010#Fi21gDronE4#001686#002204_00079.jpg"

# Verify the image exists
if [ ! -f "$SOURCE_IMG" ]; then
    echo "ERROR: The specified image does not exist: $SOURCE_IMG"
    exit 1
fi

echo "Using source image: $SOURCE_IMG"

# Run the emotion control script
python -m torch.distributed.launch --nproc_per_node=1 --master_port 12345 \
  emotion_control.py \
  --config $CONFIG_PATH \
  --checkpoint $CHECKPOINT_PATH \
  --source_img "$SOURCE_IMG" \
  --output_dir $OUTPUT_DIR \
  --start_emotion neutral \
  --end_emotion happy \
  --start_intensity 0.0 \
  --end_intensity 1.0 \
  --steps 60