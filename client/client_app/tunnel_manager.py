from pyngrok import ngrok, conf
import os
import logging
import time

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

    # Check for existing tunnels
    try:
        tunnels = ngrok.get_tunnels()
        for t in tunnels:
            # t.config['addr'] comes as "http://localhost:8000" or "localhost:8000"
            if str(port) in t.config.get("addr", ""):
                logger.info(f"Reusing existing ngrok tunnel: {t.public_url}")
                return t.public_url
    except Exception as e:
        logger.warning(f"Could not check existing tunnels: {e}")

    try:
        # Kill any existing tunnels/processes only if we need to start fresh
        # strict kill might be too aggressive if we want to support multiple services later
        # but for now, we want to ensure we don't have zombie processes if we are starting fresh
        kill_tunnels()
        time.sleep(2)  # Give it a moment to cleanup

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
