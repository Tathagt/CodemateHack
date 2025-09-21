
import os
import re
import subprocess
import logging
import platform
import threading
from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import psutil
import openai


IS_WINDOWS = platform.system() == "Windows"
if not IS_WINDOWS:
    import pty
    import select

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


app = Flask(__name__, static_folder='.')
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


openai.api_key = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")


user_session = { 'current_directory': os.getcwd() }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

def is_openai_configured():
    """Checks if the OpenAI API key is properly configured."""
    return openai.api_key and "YOUR_OPENAI_API_KEY" not in openai.api_key

def intelligent_offline_ai(query: str) -> str:
    
    logging.info(f"Using Intelligent Offline AI for query: '{query}'")
    query = query.lower()
    commands = []
    
    created_folder_context = None

    
    list_cmd = "dir" if IS_WINDOWS else "ls -l"
    move_cmd = "move" if IS_WINDOWS else "mv"
    copy_cmd = "copy" if IS_WINDOWS else "cp"
    read_cmd = "type" if IS_WINDOWS else "cat"
    del_file_cmd = "del" if IS_WINDOWS else "rm"
    del_folder_cmd = "rmdir" if IS_WINDOWS else "rm -r"
    
    
    if "create a folder" in query or "make a folder" in query or "make a directory" in query:
        match = re.search(r'(?:folder|directory) (?:called |named )?([\w.-]+)', query)
        if match:
            folder_name = match.group(1)
            commands.append(f"mkdir {folder_name}")
            created_folder_context = folder_name

    
    if "create a file" in query or "make a file" in query:
        match = re.search(r'file (?:called |named )?([\w.-]+)', query)
        if match:
            file_name = match.group(1)
            content = "hello world" 
            
           
            content_match_quoted = re.search(r'(?:write|with text|containing)\s+["\'](.*?)["\']', query)
            if content_match_quoted:
                content = content_match_quoted.group(1)
            else:
                
                content_match_unquoted = re.search(r'(?:write|with text|containing)\s+(.*)', query)
                if content_match_unquoted:
                    content = content_match_unquoted.group(1).strip()

            commands.append(f'echo "{content}" > {file_name}')

    
    if "move file" in query:
        file_match = re.search(r'move file ([\w.-]+)', query)
        if file_match:
            file_name = file_match.group(1)
            
            dest_match = re.search(r'(?:to|into) ([\w.-]+)', query)
            if dest_match and dest_match.group(1) != 'it':
                dest_folder = dest_match.group(1)
                commands.append(f"{move_cmd} {file_name} {dest_folder}")
            elif created_folder_context:
                commands.append(f"{move_cmd} {file_name} {created_folder_context}")

    
    if "delete file" in query or "remove file" in query:
        match = re.search(r'(?:delete|remove) file ([\w.-]+)', query)
        if match:
            commands.append(f"{del_file_cmd} {match.group(1)}")

    
    if "delete folder" in query or "remove directory" in query:
        match = re.search(r'(?:delete|remove) (?:folder|directory) ([\w.-]+)', query)
        if match:
            commands.append(f"{del_folder_cmd} {match.group(1)}")

    
    if "copy file" in query:
        match = re.search(r'copy file ([\w.-]+) to ([\w.-]+)', query)
        if match:
            commands.append(f"{copy_cmd} {match.group(1)} {match.group(2)}")
            
   
    if "read file" in query or "show content of" in query or "display file" in query:
        match = re.search(r'file ([\w.-]+)', query)
        if match:
            commands.append(f"{read_cmd} {match.group(1)}")

    
    if "list files" in query or "show files" in query:
        commands.append(list_cmd)
    if "current location" in query or "where am i" in query:
        commands.append("cd" if IS_WINDOWS else "pwd")

    if commands:
        return " && ".join(commands)
    else:
        return f'echo "Offline AI: I couldn\'t understand that. Please try another command."'

def translate_nl_to_command(query: str) -> str:
    """Uses live OpenAI API if available, otherwise falls back to the intelligent offline AI."""
    if is_openai_configured():
        try:
            logging.info(f"Translating with live OpenAI: '{query}'")
            system_prompt = (
                f"You are a helpful assistant that translates natural language into a single, "
                f"executable shell command for a {platform.system()} environment. "
                "Return only the command, with no explanation, preamble, or markdown formatting."
            )
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ]
            )
            command = response.choices[0].message.content.strip()
            logging.info(f"Live AI translated '{query}' to '{command}'")
            return command
        except Exception as e:
            logging.error(f"OpenAI API call failed: {e}. Falling back to Offline AI.")
            emit('command_error', f"Live AI failed (e.g., quota issue). Using Offline AI.")
            return intelligent_offline_ai(query)
    else:
        return intelligent_offline_ai(query)


def system_stats_emitter():
    logging.info("Starting system stats emitter thread.")
    while True:
        try:
            stats = { 'cpu': psutil.cpu_percent(interval=1), 'memory': psutil.virtual_memory().percent }
            socketio.emit('system_stats', stats)
        except (psutil.NoSuchProcess, psutil.AccessDenied): pass
        socketio.sleep(2)

@socketio.on('connect')
def handle_connect():
    if not hasattr(app, 'stats_thread_started'):
        app.stats_thread_started = True
        socketio.start_background_task(target=system_stats_emitter)
    emit('command_output', f"Welcome! Current directory: {user_session['current_directory']}")
    emit('cwd_update', os.path.basename(user_session['current_directory']))

def _execute_command_windows(command: str):
    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=user_session['current_directory'], text=True, encoding='utf-8', errors='replace')
        def stream_reader(pipe):
            try:
                for line in iter(pipe.readline, ''): socketio.emit('command_output', line)
            finally: pipe.close()
        threading.Thread(target=stream_reader, args=[process.stdout]).start()
        threading.Thread(target=stream_reader, args=[process.stderr]).start()
        process.wait()
    except Exception as e:
        emit('command_error', str(e))
    finally:
        emit('command_done')

def _execute_command_unix(command: str):
    master_fd = None
    try:
        master_fd, slave_fd = pty.openpty()
        process = subprocess.Popen(command, shell=True, stdout=slave_fd, stderr=slave_fd, cwd=user_session['current_directory'], text=True, close_fds=True)
        os.close(slave_fd)
        while process.poll() is None:
            r, _, _ = select.select([master_fd], [], [], 0.1)
            if r:
                try:
                    output = os.read(master_fd, 1024).decode(errors='ignore')
                    if output: emit('command_output', output)
                except OSError: break
    except Exception as e:
        emit('command_error', str(e))
    finally:
        if master_fd: os.close(master_fd)
        emit('command_done')

@socketio.on('execute_command')
def handle_command(data: dict):
    command = data.get('command', '').strip()
    is_ai_query = data.get('ai', False)
    if not command: return
    if is_ai_query:
        try:
            translated_command = translate_nl_to_command(command)
            emit('command_output', f"~ AI translated to: `{translated_command}`")
            command = translated_command
        except Exception as e:
            logging.error(f"AI translation failed: {e}")
            emit('command_error', f"AI translation failed: {e}")
            emit('command_done')
            return
    if command.startswith('cd '):
        try:
            path = command.split(None, 1)[1]
            new_dir = os.path.abspath(os.path.join(user_session['current_directory'], os.path.expanduser(path)))
            if os.path.isdir(new_dir):
                user_session['current_directory'] = new_dir
                emit('command_output', f"Directory changed to: {new_dir}")
            else:
                emit('command_error', f"Directory not found: {path}")
        except Exception as e:
            emit('command_error', str(e))
        emit('cwd_update', os.path.basename(user_session['current_directory']))
        emit('command_done')
        return
    if IS_WINDOWS: _execute_command_windows(command)
    else: _execute_command_unix(command)

if __name__ == '__main__':
    logging.info(f"Starting Flask-SocketIO server on {platform.system()}...")
    socketio.run(app, port=5000, debug=False)

