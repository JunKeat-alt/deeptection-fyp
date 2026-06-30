# Deeptection

> AI-Based Deepfake-Enabled Phishing Detection Framework for Verifying Multimedia Messages Using Computer Vision and Audio Analysis

Deeptection is a web-based deepfake verification system developed as a Final Year Project (FYP) at Asia Pacific University of Technology & Innovation (APU).

The system helps non-technical users, especially parents, guardians, and elderly individuals, verify suspicious multimedia messages by analysing both video and audio for signs of AI-generated manipulation.


---

## 📷 Application Preview

<p align="center">
  <img src="docs/images/homepage.png" width="900" alt="Homepage">
</p>

## Features

- Video deepfake detection
- Audio deepfake detection
- Multimodal decision fusion
- Confidence scoring
- Explainable AI detection report
- Risk assessment
- Decision logging
- Web-based interface
- Lightweight deployment

---

## Project Architecture

```
Frontend (React)

        │

        ▼

Backend (FastAPI)

        │

        ├── Video Detection Module
        ├── Audio Detection Module
        ├── Decision Fusion Engine
        ├── Explainable AI Report Generator
        └── Decision Logger
```

---

## Technology Stack

### Frontend

- React
- JavaScript
- HTML5
- CSS3

### Backend

- FastAPI
- Python

### AI & Machine Learning

- PyTorch
- ONNX Runtime
- OpenCV

### Multimedia Processing

- FFmpeg
- Librosa
- NumPy

---

## Project Objectives

- Detect manipulated video content
- Detect AI-generated voice
- Combine audio and video predictions
- Produce understandable verification reports
- Improve protection against deepfake-enabled phishing attacks

---

## Installation

Clone the repository.

```bash
git clone https://github.com/<username>/Deeptection.git
```

Install backend dependencies.

```bash
pip install -r requirements.txt
```

Install frontend dependencies.

```bash
npm install
```

Run backend.

```bash
uvicorn app:app --reload
```

Run frontend.

```bash
npm start
```

---

## Disclaimer

This project is developed for educational and research purposes as part of an undergraduate Final Year Project.

It should not be considered a replacement for professional forensic analysis or commercial deepfake detection systems.

---

## Third-Party Components

This project incorporates several open-source libraries, pretrained models, and publicly available datasets.

Please refer to:

- THIRD_PARTY_LICENSES.md
- NOTICE.md

---

## Citation

If you use this project in academic work, please cite:

```
Koh, J. K.

Deeptection: AI-Based Deepfake-Enabled Phishing Detection Framework for Verifying Multimedia Messages Using Computer Vision and Audio Analysis.

Final Year Project

Asia Pacific University of Technology & Innovation

2026
```

---

## License

This project is licensed under the MIT License.

See the LICENSE file for details.
