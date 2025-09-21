**Visual Command Center**
A real-time, AI-powered web terminal built for the CodeMate Hackathon (Problem Statement 1).

The Visual Command Center is a modern, web-based terminal that not only executes standard system commands but also provides a rich, interactive user experience with live system monitoring and an intelligent command translation engine. Built with a robust Python backend and a sleek, responsive frontend, this project demonstrates a unique approach to a classic tool.

**Features**
This project meets and exceeds all the requirements of the hackathon's "Python-Based Command Terminal" problem statement.

Real-Time Terminal: A fully functioning terminal that streams command output instantly using WebSockets.

Cross-Platform Support: Works seamlessly on both Windows and Unix-like systems (macOS, Linux).

Live System Monitoring: A graphical dashboard displays real-time CPU and Memory usage, pushed directly from the backend via psutil.

Hybrid AI Engine:

Live AI Mode: Uses the OpenAI API to translate any complex natural language query into an executable command.

Intelligent Offline AI: A powerful, rule-based parser acts as a fallback, allowing for a full-featured demo without requiring a paid API key. It can handle multi-step commands and context.

Full File & Directory Operations: Supports all standard commands (dir, ls, cd, mkdir, rm, move, copy, etc.).

Command History: Easily navigate through previous commands using the up and down arrow keys.

Clean & Responsive UI: A modern interface built with Tailwind CSS that looks great on any device.

**Tech Stack**
Backend: Python, Flask, Flask-SocketIO, psutil, OpenAI

Frontend: HTML, Tailwind CSS, Vanilla JavaScript, Chart.js, Socket.IO Client

Core Technologies: WebSockets, Pseudo-terminals (pty)

**Project Structure**
The project is contained within two self-sufficient files for simplicity and easy deployment.

/visual-command-center/
├── backend.py        # The Python backend server (Flask, SocketIO, AI logic)
└── index.html        # The single-file frontend (HTML, CSS, JS, UI logic)

**Local Setup & Installation**
To run the Visual Command Center on your local machine, follow these steps:

1. Clone the Repository

git clone [https://github.com/your-username/visual-command-center.git](https://github.com/your-username/visual-command-center.git)
cd visual-command-center

2. Install Python Dependencies
Make sure you have Python 3 installed. Then, install the required libraries using pip.

# It's recommended to use a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

# Install all required packages
pip install Flask Flask-SocketIO psutil openai flask-cors

3. Configure the AI (Optional)
To use the live OpenAI mode, you need to add your API key:

Open the backend.py file.

On line 48, replace "YOUR_OPENAI_API_KEY" with your actual key.

If you don't add a key, the project will automatically use the powerful "Intelligent Offline AI" for demo purposes.

4. Run the Backend Server

python backend.py

The server will start and be listening on http://127.0.0.1:5000.

5. Open the Frontend

Open your web browser and navigate to: http://127.0.0.1:5000

The Visual Command Center should load and be ready to use.

**How to Use**
Standard Commands: Type any standard command for your operating system (dir, ls, echo "hello", etc.) and press Enter.

AI Mode:

Click the "AI Mode: OFF" button to toggle it on. The button will turn green.

Type a natural language query (e.g., "create a file named report.txt with the text 'Project complete'").

Press Enter. The AI will translate your query into a command, display it, and then execute it.

Remember to toggle AI Mode OFF to run standard commands again.


Command History: Use the Up Arrow and Down Arrow keys to cycle through your command history.
