"""
AI Study Assistant - Backend Server
A beginner-friendly Python HTTP server using only standard libraries.
Serves frontend static files and routes chat queries to Google Gemini or OpenAI.
"""

import http.server
import json
import os
import socketserver
import sys
import urllib.error
import urllib.request

# Configuration
PORT = 8000
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")
ENV_PATH = os.path.join(BASE_DIR, ".env")


def load_env_file():
    """Simple parser to read .env key-value pairs without requiring external packages."""
    env_vars = {}
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        env_vars[key.strip()] = val.strip().strip("\"'")
        except Exception as e:
            print(f"Warning reading .env file: {e}")
    return env_vars


def get_ai_config():
    """Retrieve current AI API Key, Provider, and Model."""
    file_env = load_env_file()
    api_key = file_env.get("AI_API_KEY") or os.environ.get("AI_API_KEY", "").strip()
    
    # Detect provider based on key format or explicit configuration
    explicit_provider = file_env.get("AI_PROVIDER", "").lower()
    if explicit_provider:
        provider = explicit_provider
    elif api_key.startswith("sk-"):
        provider = "openai"
    elif api_key.startswith("AQ.") or api_key.startswith("AIza"):
        provider = "gemini"
    elif api_key:
        provider = "gemini"
    else:
        provider = "none"

    if provider == "openai":
        model = file_env.get("OPENAI_MODEL") or os.environ.get("OPENAI_MODEL", "gpt-4o-mini").strip()
    else:
        model = file_env.get("GEMINI_MODEL") or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite").strip()

    return api_key, provider, model


def mask_key(key):
    """Return a masked preview of the API key for safe display."""
    if not key:
        return ""
    if len(key) <= 12:
        return f"{key[:3]}***"
    return f"{key[:7]}...{key[-4:]}"


def query_gemini(user_message, api_key, model="gemini-2.5-flash-lite"):
    """
    Call Google Gemini generateContent API using standard library urllib.request.
    Includes automatic fallback to alternative flash models if a 503 is encountered.
    """
    candidate_models = [model, "gemini-3.5-flash", "gemini-2.5-flash-lite"]
    seen = set()
    models_to_try = [m for m in candidate_models if not (m in seen or seen.add(m))]

    study_prompt = (
        "You are an encouraging, clear, and beginner-friendly AI Study Assistant.\n"
        "Help the student understand concepts simply, provide concise explanations, "
        "helpful examples, and key study takeaways. Use markdown formatting where appropriate.\n\n"
        f"Student Question: {user_message}"
    )

    last_error = ""
    for candidate in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{candidate}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [{"text": study_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
            },
        }

        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                res_body = json.loads(response.read().decode("utf-8"))
                candidates = res_body.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts and "text" in parts[0]:
                        return True, parts[0]["text"], candidate
                return False, "Received an empty response from Gemini.", candidate

        except urllib.error.HTTPError as http_err:
            raw_err = http_err.read().decode("utf-8")
            if http_err.code == 503:
                last_error = f"Gemini model {candidate} was temporarily busy (503)."
                continue  # Try fallback model
            try:
                err_json = json.loads(raw_err)
                err_msg = err_json.get("error", {}).get("message", raw_err)
            except Exception:
                err_msg = raw_err
            return False, f"⚠️ Gemini API Error ({http_err.code}): {err_msg}", candidate

        except urllib.error.URLError as url_err:
            last_error = f"Network Error: {url_err.reason}"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    return False, f"⚠️ Gemini Service Unavailable: {last_error}", model


def query_openai(user_message, api_key, model="gpt-4o-mini"):
    """
    Call OpenAI Chat Completions API using standard library urllib.request.
    """
    url = "https://api.openai.com/v1/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a friendly, encouraging, and clear AI Study Assistant. "
                    "Help the student understand complex topics with simple analogies, "
                    "concise summaries, step-by-step explanations, and key takeaways."
                ),
            },
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.7,
        "max_tokens": 1000,
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res_body = json.loads(response.read().decode("utf-8"))
            reply_text = res_body["choices"][0]["message"]["content"]
            return True, reply_text, model
    except urllib.error.HTTPError as http_err:
        raw_err = http_err.read().decode("utf-8")
        try:
            err_json = json.loads(raw_err)
            err_msg = err_json.get("error", {}).get("message", raw_err)
        except Exception:
            err_msg = raw_err
        return False, f"⚠️ OpenAI API Error ({http_err.code}): {err_msg}", model
    except Exception as e:
        return False, f"⚠️ Error calling OpenAI: {str(e)}", model


class StudyAssistantHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler serving static files and API endpoints."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def _set_json_headers(self, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_json_headers(204)

    def do_GET(self):
        if self.path == "/api/status":
            api_key, provider, model = get_ai_config()
            provider_name = "Google Gemini" if provider == "gemini" else ("OpenAI" if provider == "openai" else "None")
            self._set_json_headers(200)
            response_data = {
                "status": "online",
                "backend": "online",
                "ai_configured": bool(api_key),
                "provider": provider_name if bool(api_key) else None,
                "model": model if bool(api_key) else None,
                "masked_key": mask_key(api_key),
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        return super().do_GET()

    def do_POST(self):
        if self.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)

            try:
                payload = json.loads(post_data.decode("utf-8"))
                user_message = payload.get("message", "").strip()
            except Exception:
                self._set_json_headers(400)
                error_response = {"error": "Invalid JSON payload."}
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
                return

            if not user_message:
                self._set_json_headers(400)
                error_response = {"error": "Message cannot be empty."}
                self.wfile.write(json.dumps(error_response).encode("utf-8"))
                return

            api_key, provider, model = get_ai_config()

            if not api_key:
                self._set_json_headers(200)
                unconfigured_response = {
                    "ai_configured": False,
                    "received_message": user_message,
                    "reply": "No API key configured. Add your API key in the `.env` file to enable live AI responses.",
                }
                self.wfile.write(json.dumps(unconfigured_response).encode("utf-8"))
                return

            # Route to appropriate provider
            if provider == "gemini":
                success, ai_reply, used_model = query_gemini(user_message, api_key, model)
            else:
                success, ai_reply, used_model = query_openai(user_message, api_key, model)

            self._set_json_headers(200)
            response_payload = {
                "ai_configured": True,
                "success": success,
                "reply": ai_reply,
                "model": used_model,
                "provider": "Google Gemini" if provider == "gemini" else "OpenAI",
            }
            self.wfile.write(json.dumps(response_payload).encode("utf-8"))
            return

        self._set_json_headers(404)
        not_found = {"error": "Endpoint not found"}
        self.wfile.write(json.dumps(not_found).encode("utf-8"))


def run_server():
    socketserver.TCPServer.allow_reuse_address = True
    api_key, provider, model = get_ai_config()
    provider_name = "Google Gemini" if provider == "gemini" else ("OpenAI" if provider == "openai" else "None")

    try:
        with socketserver.TCPServer((HOST, PORT), StudyAssistantHandler) as httpd:
            print("=" * 60)
            print("  AI Study Assistant Backend is running!")
            print(f"  Local Address:  http://{HOST}:{PORT}")
            print(f"  Static Folder:  {PUBLIC_DIR}")
            print(f"  AI Key Set:     {bool(api_key)} ({mask_key(api_key)})")
            print(f"  AI Provider:    {provider_name}")
            print(f"  AI Model:       {model}")
            print("=" * 60)
            print("Press Ctrl+C to stop the server.\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server gracefully...")
        sys.exit(0)
    except Exception as e:
        print(f"Error starting server: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_server()
