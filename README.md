<p align='center'>
  <b>
    <a href="https://your_project_website_link.com">Website</a>
    | 
    <a href="https://arxiv.org/abs/your_arxiv_paper_link">ArXiv</a>
    | 
    <a href="#Get-Start">Get Started</a>
    | 
    <a href="https://youtu.be/your_video_link">Video</a>
  </b>
</p> 

# PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video

The source code for the Senior Design project "[PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video](https://arxiv.org/abs/your_arxiv_paper_link)" (2025).

PIGAN is a GAN-based model designed to generate videos from a single portrait image while embedding personality traits into the animation. This model enables:

* **Emotion-based Video Generation**
  <p align='center'>  
    <img src='https://your_image_link.com' width='700'/>
  </p>
  <p align='center'>  
    <b>Emotion-based Portrait-to-Video Generation</b> 
  </p>
  
* **Personality Embedding in Animations**
  <p align='center'> 
    <img src='https://your_image_link.com' width='700'/>
  </p>
  <p align='center'>  
    <b>Personality-Informed Animation Control</b> 
  </p>

* **Facial Expression Manipulation**
  <p align='center'>  
    <img src='https://your_image_link.com' width='700'/>
  </p>
  <p align='center'>  
    <b>Facial Expression Control</b> 
  </p>

## News

* 2025.04.15: PIGAN code is now available!

## Colab Demo

Coming soon

## Get Started

### 1). Installation

#### Requirements

* Python 3
* PyTorch 1.10+
* CUDA 11.1

#### Conda Installation

```bash
# 1. Create a conda virtual environment.
conda create -n PIGAN python=3.8
conda activate PIGAN
conda install -c pytorch pytorch=1.10 torchvision cudatoolkit=11.1

# 2. Install other dependencies
pip install -r requirements.txt
