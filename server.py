import os
import signal
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv
import time
import threading
import traceback

current_dir = Path(__file__).resolve().parent
root_dir = current_dir
sys.path.insert(0, str(root_dir / 'app'))
sys.path.insert(0, str(root_dir / 'streamlit_app'))


class EnvironmentLoader:
    @staticmethod
    def load_environment(env_file):
        print(f"Loading environment from {env_file}")
        load_dotenv(dotenv_path=env_file)


class PortManager:
    @staticmethod
    def get_available_port(start_port):
        port = start_port
        while True:
            with subprocess.Popen(["lsof", "-i", f":{port}"], stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE) as process:
                stdout, _ = process.communicate()
                if 'LISTEN' not in stdout.decode():
                    return port
            port += 1

    @staticmethod
    def kill_process_on_port(port):
        try:
            result = subprocess.run(["lsof", "-t", f"-i:{port}"], stdout=subprocess.PIPE, text=True)
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                if pid:
                    os.kill(int(pid), signal.SIGKILL)
        except Exception as e:
            print(f"No process found running on port {port}. Details: {e}")


class ApplicationRunner:
    backend_process = None
    frontend_process = None

    @staticmethod
    def stream_process_output(process_stream):
        for line in iter(process_stream.readline, b''):
            sys.stdout.write(line.decode())

    @staticmethod
    def is_backend_running(host, port):
        try:
            import socket
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            return False

    @staticmethod
    def run_backend():
        try:
            backend_env_file = root_dir / 'app' / '.env.local'
            EnvironmentLoader.load_environment(backend_env_file)
            backend_port = int(os.getenv('PORT', 8000))
            available_port = PortManager.get_available_port(backend_port)
            if available_port != backend_port:
                print(f"Port {backend_port} is not available. Using port {available_port} for backend.")
                backend_port = available_port
            backend_cmd = f'uvicorn app.main:app --host {os.getenv("HOST", "127.0.0.1")} --port {backend_port} --log-level info --access-log'
            print(f"Starting backend with command: {backend_cmd}")
            ApplicationRunner.backend_process = subprocess.Popen(
                backend_cmd,
                shell=True,
                preexec_fn=os.setsid,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout_thread = threading.Thread(
                target=ApplicationRunner.stream_process_output,
                args=(ApplicationRunner.backend_process.stdout,)
            )
            stderr_thread = threading.Thread(
                target=ApplicationRunner.stream_process_output,
                args=(ApplicationRunner.backend_process.stderr,)
            )
            stdout_thread.start()
            stderr_thread.start()
            print(f"Backend is running on port {backend_port}")
        except Exception as e:
            print(f"Failed to run backend: {e}")
            traceback.print_exc()

    @staticmethod
    def run_frontend():
        try:
            frontend_env_file = root_dir / 'streamlit_app' / '.env.local'
            EnvironmentLoader.load_environment(frontend_env_file)
            backend_host = os.getenv('BACKEND_HOST', '127.0.0.1')
            backend_port = int(os.getenv('BACKEND_PORT', '8000'))
            print("Waiting for backend to start...")
            while not ApplicationRunner.is_backend_running(backend_host, backend_port):
                time.sleep(0.5)
            print("Backend started. Proceeding with frontend.")
            frontend_port = int(os.getenv('STREAMLIT_PORT', 8501))
            available_port = PortManager.get_available_port(frontend_port)
            if available_port != frontend_port:
                print(f"Port {frontend_port} is not available. Using port {available_port} for frontend.")
                frontend_port = available_port
            frontend_file = root_dir / 'streamlit_app' / 'main.py'
            if not frontend_file.is_file():
                raise FileNotFoundError(f"Streamlit file {frontend_file} does not exist.")
            frontend_cmd = f'streamlit run {frontend_file} --server.port {frontend_port}'
            print(f"Starting frontend with command: {frontend_cmd}")
            ApplicationRunner.frontend_process = subprocess.Popen(
                frontend_cmd,
                shell=True,
                preexec_fn=os.setsid,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            print(f"Frontend is running on port {frontend_port}")
        except Exception as e:
            print(f"Failed to run frontend: {e}")
            traceback.print_exc()


def terminate_processes():
    if ApplicationRunner.backend_process:
        os.killpg(os.getpgid(ApplicationRunner.backend_process.pid), signal.SIGTERM)
    if ApplicationRunner.frontend_process:
        os.killpg(os.getpgid(ApplicationRunner.frontend_process.pid), signal.SIGTERM)


def main():
    try:
        ApplicationRunner.run_backend()
        ApplicationRunner.run_frontend()
        print("Backend and Frontend are running.")
        while True:
            pass
    except KeyboardInterrupt:
        print("Shutting down processes...")
        terminate_processes()
        if ApplicationRunner.backend_process:
            ApplicationRunner.backend_process.wait()
        if ApplicationRunner.frontend_process:
            ApplicationRunner.frontend_process.wait()


if __name__ == "__main__":
    main()
