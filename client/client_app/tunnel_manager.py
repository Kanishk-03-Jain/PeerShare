from pyngrok import ngrok, conf
import os


def start_ngrok_tunnel(port, auth_token=None):
    """
    Start ngrok tunnel on the given port
    returns public url
    """

    token = auth_token if auth_token else os.getenv("NGROK_AUTHTOKEN")

    if not token:
        print("No ngrok auth token found")
        return None

    try:
        print("Starting ngrok tunnel...")
        conf.get_default().auth_token = token

        tunnel = ngrok.connect(port)
        public_url = tunnel.public_url

        print(f"Ngrok tunnel active at: {public_url}")
        return public_url
    except Exception as e:
        print(f"❌ Failed to start Ngrok: {e}")
        return None
