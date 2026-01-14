from pyngrok import ngrok, conf
import os
import logging

logger = logging.getLogger(__name__)


def start_ngrok_tunnel(port, auth_token=None):
    """
    Start ngrok tunnel on the given port
    returns public url
    """

    token = auth_token if auth_token else os.getenv("NGROK_AUTHTOKEN")

    if not token:
        logger.warning("No ngrok auth token found")
        return None

    try:
        # Kill any existing tunnels/processes to avoid "limited to 1 simultaneous ngrok agent session" error
        kill_tunnels()

        logger.info("Starting ngrok tunnel...")
        conf.get_default().auth_token = token

        tunnel = ngrok.connect(port)
        public_url = tunnel.public_url

        logger.info(f"Ngrok tunnel active at: {public_url}")
        return public_url
    except Exception as e:
        logger.error(f"Failed to start Ngrok: {e}")
        return None


def kill_tunnels():
    """Stop all running ngrok tunnels"""
    try:
        ngrok.kill()
        logger.info("Stopped all ngrok tunnels")
    except Exception as e:
        logger.error(f"Failed to kill ngrok tunnels: {e}")
