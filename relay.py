#!/usr/bin/env python3
"""Beacon relay — a tiny rendezvous point for the "Quick code" pairing mode.

It matches the two devices that present the same pairing code and forwards
signaling between them. It never sees your messages or files — those travel
directly between the devices. Run it somewhere both devices can reach.

  pip install websockets

Same network (LAN), plain ws:
  python3 relay.py                       # -> ws://0.0.0.0:8080

Across the internet, or when the app is served over https (e.g. on iOS),
you need wss. Point it at a certificate the devices trust (mkcert for a LAN
name, or a real cert from your host / Caddy / Let's Encrypt for a domain):
  python3 relay.py --cert cert.pem --key key.pem   # -> wss://0.0.0.0:8080

Then in the app's "Quick code" panel put this relay's address and a shared
code on both devices. For pairing across different networks, also fill in a
STUN server in the app (and, for stubborn NATs, a TURN server).
"""

import argparse
import asyncio
import json
import ssl
import sys
from collections import defaultdict

try:
    import websockets
except ImportError:
    sys.exit("Missing dependency. Run:  pip install websockets")

# code -> set of connected sockets (capped at 2)
rooms = defaultdict(set)


async def handler(ws, *_):
    """One connection. Joins a room by code, then relays signaling to its peer."""
    code = None
    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            kind = msg.get("t")

            if kind == "join":
                code = str(msg.get("room", ""))[:64]
                peers = rooms[code]
                if len(peers) >= 2:
                    await ws.send(json.dumps({"t": "full"}))
                    code = None
                    continue
                peers.add(ws)
                await ws.send(json.dumps({"t": "joined", "peers": len(peers)}))

            elif kind == "signal" and code is not None:
                # forward opaque signaling payload to the other occupant
                for peer in list(rooms.get(code, ())):
                    if peer is not ws:
                        try:
                            await peer.send(json.dumps({"t": "signal", "data": msg.get("data")}))
                        except Exception:
                            pass
    finally:
        if code is not None:
            peers = rooms.get(code, set())
            peers.discard(ws)
            for peer in list(peers):
                try:
                    await peer.send(json.dumps({"t": "peer-left"}))
                except Exception:
                    pass
            if not peers:
                rooms.pop(code, None)


async def main():
    ap = argparse.ArgumentParser(description="Beacon rendezvous relay")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--cert", help="TLS certificate (enables wss)")
    ap.add_argument("--key", help="TLS private key (enables wss)")
    args = ap.parse_args()

    sslctx = None
    scheme = "ws"
    if args.cert and args.key:
        sslctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        sslctx.load_cert_chain(args.cert, args.key)
        scheme = "wss"
    elif args.cert or args.key:
        sys.exit("Provide both --cert and --key for wss, or neither for ws.")

    async with websockets.serve(handler, args.host, args.port, ssl=sslctx):
        print(f"Beacon relay listening on {scheme}://{args.host}:{args.port}   (Ctrl-C to stop)")
        await asyncio.Future()  # run forever


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")
