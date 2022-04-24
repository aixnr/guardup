"""WireGuard Linux Server Management Script
Date created: 23 Apr 2022, aizanfahri@gmail.com
Tested on Fedora v34

This script DOES NOT handle the following:
  - Enabling net.ipv4.ip_forward kernel directive.
  - Installing wireguard-tools package.
  - The creation of WG_USER_CONF, please create manually.
"""
# ------------------------------------------------------------------------------
# Import modules
from configparser import ConfigParser
import argparse
import os
import re
import shutil
from rich import print
from pathlib import Path
from subprocess import Popen, PIPE, DEVNULL, run
import sys
from sqlalchemy import create_engine
from lib.db import bind_engine, peer_add, peer_show, peer_manage


# ------------------------------------------------------------------------------
# Static variable
WG_USER_CONF = Path("/var/guardup")

# Default variables; write to /var/guardup/guardup.conf; read by ConfigParser at runtime
program_config = {
    "HOST_INTERNAL_IP": "10.0.0.1",
    "HOST_EXTERNAL_IP": "192.168.1.10",
    "HOST_LISTEN_PORT": "51820",
    "INTERFACE": "wlps03",
    "WG_INTERFACE": "wg0",
    "DNS_SERVER": "1.0.0.1",
}

# ------------------------------------------------------------------------------
# SQL Alchemy main config
if not WG_USER_CONF.is_dir():
    print(f"  [red][WARN][/] {WG_USER_CONF} directory does not exist.")
    print("  [red][WARN][/] sqlite db not initialized. Exiting...")
    sys.exit()
else:
    # print(f"  [green][INFO][/] {WG_USER_CONF} directory does exist.")
    engine = create_engine(f"sqlite:////{WG_USER_CONF}/db.sql")
    bind_engine(engine)


# ------------------------------------------------------------------------------
def generate_config():
    """Generate config for ConfigParser
    """
    with open("configs/guardup.conf", "r") as _guardup_conf_template:
        _content = _guardup_conf_template.read()
        _content = _content.format(
            HOST_INTERNAL_IP=program_config["HOST_INTERNAL_IP"],
            HOST_EXTERNAL_IP=program_config["HOST_EXTERNAL_IP"],
            HOST_LISTEN_PORT=program_config["HOST_LISTEN_PORT"],
            INTERFACE=program_config["INTERFACE"],
            WG_INTERFACE=program_config["WG_INTERFACE"],
            DNS_SERVER=program_config["DNS_SERVER"]
        )

        with open(f"{WG_USER_CONF}/guardup.conf", "w") as _guardup_conf:
            _guardup_conf.write(_content)
            print(f"  [green][INFO][/] Wrote '{WG_USER_CONF}/guardup.conf' file. Please check.")


def read_config():
    """
    """
    # Store config within dictionary
    config = ConfigParser()
    _guardup_conf = Path(f"{WG_USER_CONF}/guardup.conf")
    if not _guardup_conf.is_file():
        print("  [red][WARN][/] Please run 'init' first.")
        sys.exit()

    else:
        config.read(f"{WG_USER_CONF}/guardup.conf")

        # Overwrite config dictionary
        program_config["HOST_INTERNAL_IP"] = config["guardup"]["HOST_INTERNAL_IP"]
        program_config["HOST_EXTERNAL_IP"] = config["guardup"]["HOST_EXTERNAL_IP"]
        program_config["HOST_LISTEN_PORT"] = config["guardup"]["HOST_LISTEN_PORT"]
        program_config["INTERFACE"] = config["guardup"]["INTERFACE"]
        program_config["WG_INTERFACE"] = config["guardup"]["WG_INTERFACE"]
        program_config["DNS_SERVER"] = config["guardup"]["DNS_SERVER"]


def check_status():
    """Check for:
    (1) Wireguard binary
    (2) Wireguard config
    (3) Wireguard user key directories at WG_USER_CONF
    (4) /etc/systctl kernel forwarding status
    """
    # Check for wireguard binaries
    for _wg_exec in ["wg-quick", "wg"]:
        _locate = shutil.which(_wg_exec)
        if _locate is None:
            print(f"  [red][WARN][/] {_wg_exec} does not exist in PATH. Please fix!")
        else:
            print(f"  [green][INFO][/] {_wg_exec} is available in PATH.")

    # Check for /etc/wireguard/*.conf config file
    _wg_config = Path(f"/etc/wireguard/{program_config['WG_INTERFACE']}.conf")
    if not _wg_config.is_file():
        print(f"  [green][INFO][/] The config /etc/wireguard/{program_config['WG_INTERFACE']}.conf does not exist.")
    else:
        print(f"  [red][WARN][/] Found /etc/wireguard/{program_config['WG_INTERFACE']}.conf config.")

    # Check for /etc/systctl forwarding status
    _sysctl_proc = Popen(["sysctl", "net.ipv4.ip_forward"], stdout=PIPE, stderr=PIPE).communicate()[0].decode("utf-8").strip()
    print(f"  [green][INFO][/] Forwarding status: {_sysctl_proc}")


def generate_keys(peer: str = "Host", address: str = None, allowed: str = None):
    """
    Parameter
    ---------
    peer: str
      Name of the peer.
    address: str
      Within-network address of the peer.
    allowed: str
      Allowed subnet.
    """
    # Switch of the IP selection
    if peer == "Host":
        PeerAddress = program_config["HOST_INTERNAL_IP"]
        AllowedIPs = program_config["HOST_EXTERNAL_IP"]
    else:
        PeerAddress = address
        AllowedIPs = allowed

    # Prepare dictionary
    _peer_info = {
        "PublicKey": "",
        "PrivateKey": "",
        "PeerName": peer,
        "PeerAddress": PeerAddress,
        "AllowedIPs": AllowedIPs
    }

    # Generate the keys
    run(f"sudo wg genkey | sudo tee {WG_USER_CONF}/privatekey | sudo wg pubkey | sudo tee {WG_USER_CONF}/publickey ",
        shell=True, stdout=DEVNULL, stderr=DEVNULL)
    print(f"  [green][INFO][/] Generated keys for '{peer}'.")

    # Read the keys into _keys dictionary, then remove the physical files
    for _location, _keytype in zip(["privatekey", "publickey"], ["PrivateKey", "PublicKey"]):
        with open(f"{WG_USER_CONF}/{_location}", "r") as _priv:
            _contents = _priv.read()
            _peer_info[_keytype] = _contents.strip()
        os.remove(f"{WG_USER_CONF}/{_location}")

    # Send the keys into db.sql
    peer_add(_peer_info)
    print(f"  [green][INFO][/] Added '{peer}' information to database.")

    return _peer_info


def generate_wg_keys_host():
    """Generate the keys for Host and commit to database
    """
    generate_keys(peer="Host")


def write_wg_config():
    """Write Wireguard Host config
    """
    # Check for /etc/wireguard/*.conf config file
    _wg_config = Path(f"/etc/wireguard/{program_config['WG_INTERFACE']}.conf")
    if _wg_config.is_file():
        print(f"  [red][WARN][/] Exiting since /etc/wireguard/{program_config['WG_INTERFACE']}.conf already exists...")
        sys.exit()

    # Get Host private key and retrieve the private key
    generate_wg_keys_host()
    _host_peer_info = peer_manage(peer="Host", mode="show")
    _host_private_key = _host_peer_info["PrivateKey"]

    # Open configuration to interpolate fields
    with open("configs/wg_server.conf", "r") as _f:
        _contents = _f.read()
        _contents = _contents.format(
            HOST_INTERNAL_IP=program_config["HOST_INTERNAL_IP"],
            HOST_LISTEN_PORT=program_config["HOST_LISTEN_PORT"],
            INTERFACE=program_config["INTERFACE"],
            HOST_PRIVATE_KEY=_host_private_key
        )

        # Write configuration to WG_USER_CONF/WG_INTERFACE.conf
        with open(f"{WG_USER_CONF}/{program_config['WG_INTERFACE']}.conf", "w") as _server_config:
            for _line in _contents.split("\n"):
                _remove_comments = re.findall("^#", _line)
                if not _remove_comments:
                    _server_config.write(f"{_line}\n")

    print(f"  [green][INFO][/] The {program_config['WG_INTERFACE']}.conf was successfully generated.")

    # Adding symbolic link from WG_USER_CONF/WG_INTERFACE.conf to /etc/wireguard/WG_INTERFACE.conf
    _linker = run(f"sudo ln -s {WG_USER_CONF}/{program_config['WG_INTERFACE']}.conf /etc/wireguard/{program_config['WG_INTERFACE']}.conf", shell=True, stdout=DEVNULL, stderr=DEVNULL)
    if _linker.returncode != 0:
        print(f"  [red][ERR][/] Fatal error linking '{program_config['WG_INTERFACE']}.conf'")
    else:
        print(f"  [green][INFO][/] Successfully linked '{program_config['WG_INTERFACE']}.conf'!")


def manage(peer: str = None, mode: str = "list", address: str = None, allowed: str = None):
    """Manage peers

    Parameter
    ---------
    mode: str
      Legal values are "list", "client", "mobileclient", "add", and "delete"
    """
    if mode == "list":
        peer_show()

    elif mode in ["client", "mobileclient"]:
        # Show paste-able client wg0.conf
        _peer_info = peer_manage(mode="show", peer=peer)
        _host_info = peer_manage(mode="show", peer="Host")

        with open("configs/wg_client.conf", "r") as _f:
            _content = _f.read()
            _content = _content.format(
                PEER_PRIVATE_KEY=_peer_info["PrivateKey"],
                PEER_ADDRESS=_peer_info["PeerAddress"],
                DNS_SERVER=program_config["DNS_SERVER"],
                HOST_PUBLIC_KEY=_host_info["PublicKey"],
                PEER_ALLOWED_IP=_peer_info["AllowedIPs"],
                HOST_INTERNAL_IP=_host_info["PeerAddress"],
                HOST_EXTERNAL_IP=program_config["HOST_EXTERNAL_IP"],
                HOST_LISTEN_PORT=program_config["HOST_LISTEN_PORT"]
            )

            if mode == "client":
                print("----------------- copy below -----------------")
                for _line in _content.split("\n"):
                    print(_line)
                print("----------------- copy above -----------------")

            elif mode == "mobileclient":
                _locate = shutil.which("qrencode")
                if _locate is None:
                    print("  [red][WARN][/] 'qrencode' is not installed. Exiting...")
                    sys.exit()
                else:
                    print(f"  [green][INFO][/] Generating QR code for '{peer}' mobile client...\n")
                    with open(f"{WG_USER_CONF}/mobile_client.conf", "w") as _client_config:
                        _client_config.write(_content)
                    run(f"qrencode -t ansiutf8 < {WG_USER_CONF}/mobile_client.conf", shell=True)
                    os.remove(f"{WG_USER_CONF}/mobile_client.conf")

    elif mode == "add":
        # Add new peer, generate public and private keys
        generate_keys(peer, address, allowed)
        _peer_info = peer_manage(mode="show", peer=peer)
        _host_info = peer_manage(mode="show", peer="Host")

        # Read wg_peer.conf template for adding peer onto Host's WG_INTERFACE.conf
        with open("configs/wg_peer.conf", "r") as _wg_peer:
            _contents = _wg_peer.read()
            _contents = _contents.format(
                PEER=_peer_info["Peer"],
                HOST_PUBLIC_KEY=_host_info["PublicKey"],
                PEER_ADDRESS=_peer_info["PeerAddress"]
            )

            # Add to Host's config
            with open(f"{WG_USER_CONF}/{program_config['WG_INTERFACE']}.conf", "a") as _add_peer:
                _add_peer.write("\n")
                _add_peer.write(_contents)
                _add_peer.write("\n")

    elif mode == "delete":
        # Delete from database.
        peer_manage(mode="delete", peer=peer)

        # Target and placeholders
        _line_lookup = f"[Peer] # {peer}"  # Peer block to find
        _line_number = 0                   # Placeholder for target line number
        _line_all = []                     # Placeholder for storing _server_config

        # Transfer content as list, then find the first line of the target peer block
        with open(f"{WG_USER_CONF}/{program_config['WG_INTERFACE']}.conf", "r") as _server_config:
            _line_all = _server_config.readlines()
            for _n, _line in enumerate(_line_all):
                if _line_lookup in _line:
                    _line_number = _n
                    break

        # If _line_number is equal to zero, indicating that I could not find the peer block, terminate
        if _line_number == 0:
            print(f"  [red][WARN][/] Fatal error, config block for peer '{peer}' not found. Exiting...")
            sys.exit()

        # Remove the section of the specified peer, write as temporary file
        with open(f"{WG_USER_CONF}/{program_config['WG_INTERFACE']}.conf", "w") as _server_config:
            for _n, _line in enumerate(_line_all):
                if _n not in [_i for _i in range(_line_number - 1, _line_number + 4)]:
                    _server_config.write(_line)

        # Print to stdout
        print(f"  [green][INFO][/] Removed '{peer}' from Host's '{program_config['WG_INTERFACE']}.conf'.")


# ------------------------------------------------------------------------------
# Main program wrapper with ArgumentParser
def cli():
    """
    """
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(dest="command")

    init = subparser.add_parser("init")
    init.add_argument("--info", required=False)

    host = subparser.add_parser("host")
    host.add_argument("--info", required=False)

    mngr = subparser.add_parser("mngr")
    mngr.add_argument("--mode", type=str, required=True, default="list", help="Peer operation (list, client, mobileclient, add, delete)")
    mngr.add_argument("--peer", type=str, required=False, help="Show a specific peer")
    mngr.add_argument("--address", type=str, required=False)
    mngr.add_argument("--allowed", type=str, required=False)

    args = parser.parse_args()

    if args.command == "init":
        check_status()
        _guardup_conf = Path(f"{WG_USER_CONF}/guardup.conf")
        if not _guardup_conf.is_file():
            print(f"  [green][INFO][/] '{WG_USER_CONF}/guardup.conf' not found, generating...")
            generate_config()
        else:
            print(f"  [red][WARN][/] '{WG_USER_CONF}/guardup.conf' already exists...")

    elif args.command == "host":
        read_config()       # Read config here
        write_wg_config()   # Write Host's config

    elif args.command == "mngr":
        read_config()  # Read config here

        if args.mode == "list":
            manage(mode="list")
        elif args.mode == "add":
            manage(mode=args.mode, peer=args.peer, address=args.address, allowed=args.allowed)
        elif args.mode in ["client", "mobileclient", "delete"]:
            manage(mode=args.mode, peer=args.peer)

    else:
        parser.print_help()


# ------------------------------------------------------------------------------
# Launch program
if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit()
