"""Network guard for the private training run and its audit (PRIVACY_AND_ETHICS.md). Kept apart from the training code on purpose: the
training modules import no network library at all (tests/test_private_email_pipeline.py checks it); this module imports socket only to block it."""


class NoExternalNetwork:
    """Blocks, and counts, every connection that would leave this machine, for as long as the block is open. Loopback (127.0.0.1, ::1,
    localhost) stays allowed: it never leaves the machine, and Windows' asyncio needs it for its internal self-pipe."""
    LOOPBACK = {"127.0.0.1", "::1", "localhost", None, ""}
    def __init__(self): self.attempts = 0
    def __enter__(self):
        import socket
        self.socket = socket; self.real = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)
        rc, rcc, rg = self.real; me = self
        def host_of(a): return a[0] if isinstance(a, tuple) else a
        def connect(sock, address, *a, **k):
            if host_of(address) in me.LOOPBACK: return rc(sock, address, *a, **k)
            me.attempts += 1; raise OSError("outbound connection blocked (private training run)")
        def create(address, *a, **k):
            if host_of(address) in me.LOOPBACK: return rcc(address, *a, **k)
            me.attempts += 1; raise OSError("outbound connection blocked (private training run)")
        def gai(host, *a, **k):
            if host in me.LOOPBACK: return rg(host, *a, **k)
            me.attempts += 1; raise socket.gaierror("name lookup blocked (private training run)")
        socket.socket.connect, socket.create_connection, socket.getaddrinfo = connect, create, gai
        return self
    def __exit__(self, *e): self.socket.socket.connect, self.socket.create_connection, self.socket.getaddrinfo = self.real
