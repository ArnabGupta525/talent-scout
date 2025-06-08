# 🤖 TalentScout Hiring Assistant 🚀

An intelligent chatbot for initial candidate screening and technical assessment using Django and Streamlit! 🔍

## ✨ Overview

TalentScout is a cutting-edge hiring assistant designed to streamline the initial candidate screening process. Built with **Django** for robust backend operations and **Streamlit** for a user-friendly interface, TalentScout automates the early stages of technical recruitment, saving time and resources. It leverages OpenAI's language models to engage candidates in natural conversations, assess their technical skills, and gather essential information.

## 🚀 Installation

Get started with TalentScout in just a few steps!

- 👯 **Clone the Repository:**
  ```bash
  git clone https://github.com/ArnabGupta525/talent-scout.git
  cd talent-scout
  ```

- 🛠️ **Create a Virtual Environment:**
  ```bash
  python -m venv venv
  source venv/bin/activate  # On Linux/macOS
  venv\Scripts\activate  # On Windows
  ```

- 📦 **Install Dependencies:**
  ```bash
  pip install -r requirements.txt
  ```

- 🔑 **Set Up Environment Variables:**
  Create a `.env` file in the project's root directory and add the following:

  ```
  GITHUB_TOKEN=YOUR_OPENAI_API_KEY
  FIREBASE_TYPE="your_firebase_type"
  FIREBASE_PROJECT_ID="your_firebase_project_id"
  FIREBASE_PRIVATE_KEY_ID="your_firebase_private_key_id"
  FIREBASE_PRIVATE_KEY="your_firebase_private_key"
  FIREBASE_CLIENT_EMAIL="your_firebase_client_email"
  FIREBASE_CLIENT_ID="your_firebase_client_id"
  FIREBASE_AUTH_URI="https://accounts.google.com/o/oauth2/auth"
  FIREBASE_TOKEN_URI="https://oauth2.googleapis.com/token"
  ```

- ⚙️ **Apply Migrations:**
  ```bash
  python manage.py migrate
  ```
  
- 🏃 **Run the Application:**
  ```bash
  streamlit run app.py
  ```

## 💻 Usage

Once installed, you can interact with the TalentScout chatbot through the Streamlit interface. The chatbot will guide candidates through a series of questions to assess their suitability for technical roles.

<details>
<summary><b>Detailed Usage Instructions</b></summary>

1.  **Start a Session**: Click the "Start New Session" button in the sidebar to begin a new screening process.
2.  **Engage with the Chatbot**: The chatbot will greet the candidate and start collecting basic information.
3.  **Technical Assessment**: After gathering the necessary details, the chatbot will ask technical questions based on the candidate's skills.
4.  **Review Progress**: Monitor the interview progress and collected information in the sidebar.
5.  **End the Session**: The chatbot will provide a closing message, and the candidate's information will be saved for review.

</details>

Here's a preview of the application in action:

![TalentScout Screenshot](https://i.imgur.com/your_screenshot.png)

## ✨ Features

- 💬 **Interactive Chat Interface**: Engaging conversation flow powered by Streamlit and OpenAI.
- 🧠 **Intelligent Screening**: Assesses candidate suitability based on technical skills and experience.
- 💾 **Data Handling**: Uses Firebase/Firestore to store candidate information securely.
- 📊 **Real-time Progress Tracking**: Provides a clear overview of the interview progress.
- ⚙️ **Customizable Prompts**: Tailor conversation prompts for different roles and technologies.

## 🛠️ Technologies Used

| Technology         | Description                                                 |
| :----------------- | :---------------------------------------------------------- |
| Django             | Robust backend framework for handling data and logic.        |
| Streamlit          | Simplifies the creation of interactive web apps for the UI.  |
| OpenAI             | Powers the chatbot's natural language processing capabilities. |
| Python             | The primary programming language used.                      |
| Firebase/Firestore | Secure and scalable database for candidate data storage.    |

## 🤝 Contributing

We welcome contributions from the community!

- 🐛 **Report Issues**: If you find a bug, please open an issue on GitHub.
- 💡 **Suggest Enhancements**: Share your ideas for new features or improvements.
- 💻 **Submit Pull Requests**: Contribute code by submitting a pull request.

## 📜 License

This project is licensed under the [MIT License](LICENSE).

## 🧑‍💻 Author Info

- **Arnab Gupta** - [GitHub](https://github.com/ArnabGupta525) | [LinkedIn](your_linkedin_profile) | [Twitter](your_twitter_profile)

## 🛡️ Badges

[![Python](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)

[![Readme was generated by Dokugen](https://img.shields.io/badge/Readme%20was%20generated%20by-Dokugen-brightgreen)](https://www.npmjs.com/package/dokugen)
