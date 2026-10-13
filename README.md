# 🎓 AI Study Assistant (Beginner-Friendly Full-Stack Web App)

A clean, responsive full-stack study assistant web application built with **HTML5**, **CSS3**, and **vanilla JavaScript** on the frontend, paired with a lightweight **Python backend**.

---

## 📁 Project Structure

```
ai-study-assistant/
├── public/                  # Frontend client directory
│   ├── index.html           # Main HTML structure, chat layout, and badges
│   ├── style.css            # Responsive styles, design system, and animations
│   └── app.js               # Client-side logic, API calls, auto-scroll, & event handling
├── server.py                # Beginner-friendly Python HTTP backend (zero dependencies)
├── .env                     # Current active AI configuration (Gemini / OpenAI)
├── .env.example             # Template for API key configuration
└── README.md                # Project documentation and guide
```

---

## 📄 File-by-File Explanation

1. **[`public/index.html`](file:///c:/Users/GANESH/Downloads/ai-study-assistant/public/index.html)**
   - Defines the user interface: header branding, live status pills (Backend & AI status), quick study prompt suggestions, message feed, and the input form with a Send button.
   - Designed with semantic HTML tags and responsive viewports for both mobile and desktop screens.

2. **[`public/style.css`](file:///c:/Users/GANESH/Downloads/ai-study-assistant/public/style.css)**
   - Styled with CSS custom properties (variables) for consistent color palettes, typography, spacing, and smooth transitions.
   - Includes distinct styling for user messages, assistant responses, status badges, and mobile breakpoints (`@media (max-width: 640px)`).

3. **[`public/app.js`](file:///c:/Users/GANESH/Downloads/ai-study-assistant/public/app.js)**
   - Handles user interactions: sending messages via the Send button or `Enter` key, auto-resizing the input, rendering message bubbles, and managing loading states.
   - Communicates with the backend using the browser's native `fetch()` API (`POST /api/chat` and `GET /api/status`).
   - Formats study responses with clean markdown (bold, headers, bullet points, code blocks).

4. **[`server.py`](file:///c:/Users/GANESH/Downloads/ai-study-assistant/server.py)**
   - Built using Python's standard `http.server` library so it runs immediately on any computer with Python without requiring `pip install`.
   - Serves the frontend files in the `public/` folder.
   - Intelligently routes study questions to **Google Gemini** or **OpenAI** based on the configured key format.
   - Includes automatic model fallback for high reliability.

---

## 🔑 AI Configuration (.env)

Your **Google Gemini API Key** is configured in [`.env`](file:///c:/Users/GANESH/Downloads/ai-study-assistant/.env):
```env
AI_API_KEY=AQ.Ab8RN6...E5NA
AI_PROVIDER=gemini
GEMINI_MODEL=gemini-2.5-flash-lite
PORT=8000
HOST=127.0.0.1
```

> **Multi-Provider Support:**
> The backend automatically detects whether your key is Google Gemini (`AQ.` / `AIza...`) or OpenAI (`sk-...`). You can switch providers or update your key anytime in `.env` without modifying code!

---

## 🚀 How to Run the App

1. Open your terminal in the `ai-study-assistant` folder:
   ```powershell
   cd c:\Users\GANESH\Downloads\ai-study-assistant
   ```

2. Start the Python server:
   ```powershell
   python server.py
   ```

3. Open your web browser and visit:
   ```
   http://127.0.0.1:8000
   ```

---

## 🧪 How to Test It

1. **Verify Live Status**:
   - The top right header displays **`Backend: Online`** (green) and **`AI: Google Gemini (gemini-2.5-flash-lite)`**.
2. **Ask Any Study Question**:
   - Type a question (e.g. *"Explain photosynthesis"* or *"Python lists vs tuples"*) into the input box and click **Send**.
3. **Enjoy Live AI Answers**:
   - The assistant generates structured, beginner-friendly explanations with examples, analogies, and study takeaways!
