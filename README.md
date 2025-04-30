<p align='center'>
    <b>
        <a href="https://github.com/jerrylin5168/PIGAN">GitHub</a>
        | 
        <a href="https://arxiv.org/abs/your_arxiv_paper_link">ArXiv</a>
        | 
        <a href="#Get-Start">Get Started</a>
        | 
        <a href="https://youtu.be/HWAT0OzGwg8">Video</a>
    </b>
</p>

# PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video

The source code for the Senior Design project "[PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video](https://arxiv.org/abs/your_arxiv_paper_link)" (2025).

PIGAN is a GAN-based model designed to generate videos from a single portrait image while embedding personality traits into the animation. This model enables:

* **Emotion-based Video Generation**
  <p align='center'>  
    <img src="https://github.com/jerrylin5168/PIGAN/raw/main/demo_images/Generated_Video_1744822720017.gif" width="700"/>
  </p>
  <p align='center'>  
    <b>Emotion-based Portrait-to-Video Generation</b>
  </p>

* **Personality Embedding in Animations**
  <p align='center'>  
    <img src="https://github.com/jerrylin5168/PIGAN/raw/main/demo_images/Generated_Video_1744822756935.gif" width="700"/>
  </p>
  <p align='center'>  
    <b>Personality-Informed Animation Control</b> 
  </p>

* **Facial Expression Manipulation**
  <p align='center'>  
    <img src="https://github.com/jerrylin5168/PIGAN/raw/main/demo_images/Generated_Video_1744822796613.gif" width="700"/>
  </p>
  <p align='center'>  
    <b>Facial Expression Control</b> 
  </p>

* **Motion Imitation**
  <p align='center'>  
    <img src="https://github.com/jerrylin5168/PIGAN/raw/main/demo_images/Generated_Video_1744822837077.gif" width="700"/>
  </p>
  <p align='center'>  
    <b>Same & Cross-identity Reenactment</b> 
  </p>

* **Audio-Driven Facial Reenactment**
  <p align='center'>  
    <img src="https://github.com/jerrylin5168/PIGAN/raw/main/demo_images/Generated_Video_1744822874770.gif" width="700"/>
  </p>
  <p align='center'>  
    <b>Audio-Driven Reenactment</b> 
  </p>

## Demo Video

<p align='center'>
    <iframe width="700" height="394" src="https://www.youtube.com/embed/HWAT0OzGwg8" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
</p>

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
