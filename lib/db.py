from rich import print
import sys
from tabulate import tabulate
from sqlalchemy import Column, Integer, String, delete
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Initial configuration
Base = declarative_base()
Session = sessionmaker()
session = Session()


def bind_engine(engine):
    """Main program creates engine object, this script 'uses' it.
    Using session so that we could utilize ORM instead of raw SQL commands.
    """
    Base.metadata.bind = engine
    Session.configure(bind=engine)
    Base.metadata.create_all(engine)


class Record(Base):
    """ORM class for handling Wireguard Peer
    """
    __tablename__ = "keys"

    id = Column(Integer, primary_key=True)
    Peer = Column(String)
    PeerAddress = Column(String)
    PublicKey = Column(String)
    PrivateKey = Column(String)
    AllowedIPs = Column(String)

    def __repr__(self):
        return f"Peer {self.Peer}"


def peer_add(peer_info: dict):
    """
    """
    # Check if already exists.
    peer_check(peer=peer_info["PeerName"])

    # Prepare to add to the database.
    adding_peer = Record(
        Peer=peer_info["PeerName"],
        PeerAddress=peer_info["PeerAddress"],
        PublicKey=peer_info["PublicKey"],
        PrivateKey=peer_info["PrivateKey"],
        AllowedIPs=peer_info["AllowedIPs"]
    )

    session.add(adding_peer)
    session.commit()


def peer_show():
    """
    """
    _user_list = []

    for _user in session.query(Record).order_by(Record.id):
        _user_list.append([_user.id, _user.Peer, _user.PeerAddress, _user.AllowedIPs,
                           _user.PublicKey[0:15], _user.PrivateKey[0:15]])

    print("\n")
    print(tabulate(_user_list, headers=["Peer", "Address", "AllowedIPs", "PublicKey", "PrivateKey"]))
    print("\n")


def peer_manage(peer: str, mode: str = "show"):
    """
    Parameter
    ---------
    mode: str
      Legal values are "show" and "delete"
    """
    if mode == "show":
        _peer_info = {}
        _peer = session.query(Record).filter_by(Peer=peer).first()
        _peer_info = {
            "Peer": _peer.Peer,
            "PeerAddress": _peer.PeerAddress,
            "AllowedIPs": _peer.AllowedIPs,
            "PrivateKey": _peer.PrivateKey,
            "PublicKey": _peer.PublicKey
        }

        return _peer_info

    elif mode == "delete":
        _delete_user = session.query(Record).filter_by(Peer=peer).first()
        if _delete_user is None:
            print(f"  [red][WARN][/] Peer '{peer}' not found in the database!")
            sys.exit()
        else:
            session.delete(_delete_user)
            session.commit()
            print(f"  [green][INFO][/] Deleted peer '{peer}' from the database.")


def peer_check(peer: str = "Host"):
    """
    """
    _host = session.query(Record).filter_by(Peer=peer).first()
    if _host is not None:
        print(f"  [red][WARN][/] DB entry for '{peer}' already exists. Exiting...")
        sys.exit()
