# `guardup` WireGuard CLI Tool

There are quite a number of WireGuard administration tools already, for instance [WG UI](https://github.com/EmbarkStudios/wg-ui), [wireguard-ui](https://github.com/ngoduykhanh/wireguard-ui), [Subspace (community)](https://github.com/subspacecommunity/subspace), [wg-manager](https://github.com/perara/wg-manager), [Mistborn](https://gitlab.com/cyber5k/mistborn), etc.
Here we quickly notice that they mostly have a rather unimaginative name.

`guardup` was born out of boredom and I was plagued with curiosity to try to code something useful.
I have been managing WireGuard peers for a few years now, and decided it was time to create a CLI tool to make my life a little easier.
The name came from *Monster Hunter: World*, a reference to shield-based skill *Guard Up* that allows player to guard against ordinarily unblockable attacks, e.g. Teostra's supernova.

## Building and Testing

`guardup` is built using `pyinstaller`.
Before building, prepare a virtual environment.
Example here is using `pipenv`, installing packages as described in `Pipfile`.

```bash
pipenv install
pipenv shell
```

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

# Begin program initialization (mandatory)
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
