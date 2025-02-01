# 🌍 Zingu: AI-Powered Accent Improvement Platform

## 🚀 Project Overview

Zingu is an innovative language learning application designed to help users improve their pronunciation and accent through advanced AI technologies. By combining speech recognition, machine learning, and interactive coaching, Zingu provides a personalized language learning experience.

## ✨ Key Features

- 🎙️ **Accent Detection**: Advanced AI-powered accent recognition
- 🧠 **AI Language Coach**: Personalized coaching and feedback
- 🎮 **Interactive Learning**: Gamified pronunciation practice
- 📊 **Progress Tracking**: Real-time performance metrics
- 🌈 **Kids Mode**: Child-friendly interface and learning experience

## 🛠️ Tech Stack

### Frontend
- React (TypeScript)
- Vite
- Axios
- Firebase Authentication

### Backend
- Python
- FastAPI
- Machine Learning Models
- Speech Recognition SDK

## 🌐 Open Source Community

Zingu is more than just an application - it's a collaborative platform for language learners and enthusiasts worldwide! 

### 🤝 Why Open Source?
- **Collaborative Learning**: Build together, learn together
- **Global Impact**: Help language learners across the globe
- **Transparent Development**: Open code means no hidden barriers
- **Continuous Improvement**: Community-driven enhancements

### 🌈 How You Can Contribute
- **Developers**: Improve AI models, add features
- **Linguists**: Enhance language datasets
- **UX Designers**: Refine user experience
- **Translators**: Add support for more languages
- **Language Learners**: Provide real-world feedback

## 🔧 Prerequisites

- Node.js (v18+)
- npm (v9+)
- Python (v3.9+)
- Firebase Account

## 🔥 Firebase Setup

### Prerequisites
- Create a Firebase account at [https://firebase.google.com/](https://firebase.google.com/)
- Have a Google account ready

### Firebase Project Configuration

1. **Create a New Firebase Project**
   - Go to the Firebase Console
   - Click "Add project"
   - Name your project (e.g., "zingu-accent-improver")
   - Follow the setup wizard

2. **Enable Authentication**
   - In Firebase Console, go to "Authentication"
   - Enable Sign-In Methods:
     - Email/Password
     - Google Sign-In
     - Optional: Add other providers as needed

3. **Set Up Firestore Database**
   - Go to "Firestore Database"
   - Click "Create database"
   - Choose "Start in test mode" (for development)
   - Select a starting location for your database

4. **Configure Firebase in Your Project**

   Create a `.env` file in the `frontend/` directory with the following structure:
   ```bash
   VITE_FIREBASE_API_KEY=your_api_key
   VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
   VITE_FIREBASE_PROJECT_ID=your_project_id
   VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
   VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
   VITE_FIREBASE_APP_ID=your_app_id
   VITE_FIREBASE_MEASUREMENT_ID=your_measurement_id
   ```

   > 💡 **How to Find These Values**:
   > - Go to Project Settings in Firebase Console
   > - Under "Your apps" section, click on the web app icon (`</>`)
   > - Copy the configuration object values

5. **Install Firebase SDK**
   ```bash
   cd frontend
   npm install firebase
   ```

### Security Rules

We recommend setting up Firestore security rules to protect user data:

```firestore
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /accent_data/{document=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null;
    }
  }
}
```

### Deployment Considerations
- Never commit your `.env` file to version control
- Use Firebase's environment-specific configurations
- Regularly update Firebase SDK and review security settings

### Troubleshooting
- Ensure all environment variables are correctly set
- Check Firebase Console for any configuration issues
- Verify network connectivity and CORS settings

---

**🔒 Always prioritize user data privacy and security! 🛡️**

## 🚀 Full Project Setup

### Local Development

1. Clone the repository
```bash
git clone https://github.com/qkral/zingu.git
cd zingu
```

2. Install Frontend Dependencies
```bash
cd frontend
npm install
```

3. Set Up Environment Variables
- Create `.env.development` and `.env.production` in `frontend/`
- Add necessary configuration (API URLs, Firebase config)

4. Run Development Server
```bash
npm run dev
```

### Backend Setup

1. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

2. Install Backend Dependencies
```bash
cd backend
pip install -r requirements.txt
```

3. Set Up Environment Variables
- Create a `.env` file in the `backend/` directory
- Add necessary configurations:
  ```
  OPENAI_API_KEY=your_openai_key
  SPEECH_SDK_KEY=your_speech_sdk_key
  DATABASE_URL=your_database_connection_string
  ```

4. Initialize Database
```bash
# If using SQLAlchemy or similar ORM
python -m app.db.init_db
```

5. Run Backend Server
```bash
uvicorn app.main:app --reload
```

### 🔍 Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-improvement`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-improvement`)
5. Open a Pull Request

## 💡 Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Celebrate each other's learning journey
- No language barrier is too big to overcome!

## 🤝 Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## 🙏 Acknowledgments

- OpenAI for inspiring AI technologies
- Speech recognition research community
- Language learning enthusiasts worldwide

## 📞 Contact

- Project Maintainer: Quentin Kral
- Project Link: [https://github.com/qkral/zingu](https://github.com/qkral/zingu)

---

**Together, we're breaking down language barriers! 🌍🗣️**
