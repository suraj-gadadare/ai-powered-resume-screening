# AI-Powered Resume Screening App

This project is an **AI-powered resume screening tool** that helps recruiters quickly evaluate and rank resumes based on predefined criteria. It uses machine learning and NLP to automate the initial screening process.

## 🚀 Features
- Upload resumes in PDF/DOCX format.
- Extracts and processes text using NLP.
- Classifies or ranks resumes based on job description match.
- Web-based interface built with **Streamlit**.
- Containerized with **Docker** for easy deployment.

## 🗂 Project Structure
```
├── app.py                # Main Streamlit app
├── requirements.txt      # Python dependencies
├── Dockerfile            # Build container image
├── utils/                # Helper modules (text extraction, NLP, scoring)
├── models/               # Pre-trained ML/NLP models
└── .github/              # GitHub Actions/CI workflows
```

## ⚙️ Installation & Setup
```bash
git clone https://github.com/your-username/ai-powered-resume-screening.git
cd ai-powered-resume-screening
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## 🐳 Run with Docker
```bash
docker build -t resume-screener .
docker run -p 8501:8501 resume-screener
```
Visit `http://localhost:8501` to use the app.

## 📁 Models
The `models/` folder contains the trained machine learning models used for screening. You can replace them with your own models if needed.

## 🛠 Utilities
The `utils/` folder contains helper functions for:
- Resume text extraction
- Preprocessing
- Feature extraction
- Scoring logic

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue first to discuss what you’d like to change.

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ✨ Future Enhancements
- Add analytics dashboard
- Multi-language support
- API endpoints for integration with ATS
