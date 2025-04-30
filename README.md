<p align='center'>
    <b>
        <a href="https://github.com/jerrylin5168/PIGAN">GitHub</a>
        | 
        <a href="https://youtu.be/HWAT0OzGwg8">Demo Video</a>
    </b>
</p>

# PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video

The source code for the Senior Design project "[PIGAN: Personality Informed Generative Adversarial Network for Portrait to Video](https://arxiv.org/abs/your_arxiv_paper_link)" (2025).

PIGAN is a GAN-based model that combines two distinct GAN architectures—**PI-Render** ([GitHub](https://github.com/sicxu/PI-Render)) and **Deep3DFaceRecon_pytorch** ([GitHub](https://github.com/microsoft/Deep3DFaceReconstruction))—to generate animated videos from a single portrait image. By embedding personality traits into the animation process, PIGAN enables the generation of realistic facial expressions and motions, allowing for personalized, emotion-driven video creation. This project leverages these two GANs to produce dynamic facial reenactments, making it a powerful tool for applications in personalized media, entertainment, and human-computer interaction.

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

## Citation

If you find this code useful, please cite the following papers:

For **PI-Render**:

```tex
@misc{sicxu2020pire,
  author = {Sicxu},
  title = {PI-Render: A Personality-Informed Portrait Image Generation Framework},
  year = {2020},
  url = {https://github.com/sicxu/PI-Render}
}
@misc{feng2020deep3d,
  author = {Feng, Z. and Zhang, Y. and Li, Z.},
  title = {Deep3DFaceRecon_pytorch: A 3D Face Reconstruction Method},
  year = {2020},
  url = {https://github.com/microsoft/Deep3DFaceReconstruction}
}

