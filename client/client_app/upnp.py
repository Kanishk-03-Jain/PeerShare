import miniupnpc
# universal plug and play

def forward_port(port: int):
    """
    Asks the router to open a certain tcp port for us
    Returns: a public ip
    """

    try:
        upnp = miniupnpc.UPnP()

        print("Searching for UPnP Router...")
        upnp.discoverdelay = 200
        upnp.discover()
        upnp.selectigd()

        print(f" Found! ({upnp.lanaddr})")

        external_ip = upnp.externalipaddress()
        print(f"Public IP: {external_ip}")

        upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'ShareNotes P2P', '')
        print(f"Port {port} is now OPEN on the internet!")
        
        return external_ip
    except Exception as e:
        print(f"\nUPnP Failed: {e}")
        print("   (Your router might have UPnP disabled, or you are on University/Corporate WiFi)")
        return None