# `guardup` WireGuard CLI Tool

## Building and Testing

To build, init, and test:

```bash
make clean && make install
```

Installs to `/usr/local/guardup`.

To nuke the test:

```bash
make uninstall && make dir && sudo rm /etc/wireguard/wg0.conf
```

## Usage

```bash
# Create the program configuration directory
sudo mkdir -p /var/guardup

# Begin program initialization (mandataory)
sudo ./guardup init

# Generate keys for host (server; mandatory)
sudo ./guardup host

# Adding peer
sudo ./guardup mngr --mode add --peer Nebula --address 10.0.0.11 --allowed 10.0.0.0

# Listing all peers with their truncated keys
sudo ./guardup mngr --mode list

# Showing paste-able configuration for peer
sudo ./guardup mngr --mode client --peer Nebula

# Showing QR code for a peer
sudo ./guardup mngr --mode mobileclient --peer Nebula

# Removing a peer
sudo ./guardup mngr --mode delete --peer Nebula
```

Note that after running `init` sub-command, user can inspect `/var/guardup/guardup.conf` configuration file and modify as needed before running `host` and `mngr` sub-commands.

## Technical Informatiom

`guardup` requires `/var/guardup` for its configuration `guardup.conf`, dumping the output from `genkey` and `pubkey` (deleted after saved to its database), the database `db.sql`, and tunnel configuration (later symlinked to `/etc/wireguard/{interface}.conf`, default to `wg0.conf`).
It has only been tested on recent Fedora machines (sorry, Ubuntu users), but it should work.
`guardup` does not manage installing program binaries such as `wireguard-tools` and `qrencode`, so the user is responsible for installing them.
