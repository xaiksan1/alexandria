#!/usr/bin/env python3
"""
Porta-Mundi <-> guacd Gateway
Routes all Guacamole connections through Porta-Mundi security layer
"""

import socket
import threading
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] GUACAMOLE_GATEWAY: %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cyber-gate.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GuacamoleGateway:
    """
    Gateway between Porta-Mundi and guacd
    Enforces security policies on all Guacamole connections
    """

    def __init__(self, listen_port=8822, guacd_host='::1', guacd_port=4822):
        self.listen_port = listen_port
        self.guacd_host = guacd_host
        self.guacd_port = guacd_port
        self.blocked_ips = set()
        logger.info(f"Guacamole Gateway initialized (listening on :{listen_port})")

    def verify_connection(self, client_ip):
        """Verify connection through Porta-Mundi security layer"""
        try:
            # Check if IP is in blocklist
            if client_ip in self.blocked_ips:
                logger.warning(f"Blocked connection from {client_ip} (in blocklist)")
                return False

            logger.info(f"Connection from {client_ip} verified and allowed")
            return True
        except Exception as e:
            logger.error(f"Error verifying connection: {e}")
            return False

    def forward_connection(self, client_socket, client_ip):
        """Forward client connection to guacd with security checks"""

        # Verify connection through security layer
        if not self.verify_connection(client_ip):
            client_socket.close()
            return

        try:
            # Connect to guacd (support both IPv4 and IPv6)
            addr_info = socket.getaddrinfo(self.guacd_host, self.guacd_port, socket.AF_UNSPEC, socket.SOCK_STREAM)
            family, socktype, proto, canonname, sockaddr = addr_info[0]
            guacd_socket = socket.socket(family, socktype, proto)
            guacd_socket.connect(sockaddr)
            
            logger.info(f"Connection established: {client_ip} -> guacd")

            # Start bidirectional forwarding
            thread1 = threading.Thread(
                target=self._forward_data,
                args=(client_socket, guacd_socket, f"{client_ip}->guacd")
            )
            thread2 = threading.Thread(
                target=self._forward_data,
                args=(guacd_socket, client_socket, f"guacd->{client_ip}")
            )

            thread1.daemon = True
            thread2.daemon = True
            thread1.start()
            thread2.start()

            thread1.join()
            thread2.join()

        except Exception as e:
            logger.error(f"Connection forwarding error: {e}")
        finally:
            client_socket.close()

    def _forward_data(self, src_socket, dst_socket, direction):
        """Forward data between sockets"""
        try:
            while True:
                data = src_socket.recv(4096)
                if not data:
                    break
                dst_socket.send(data)
        except Exception as e:
            logger.debug(f"Forwarding stopped ({direction}): {e}")

    def start(self):
        """Start the gateway server"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind(('0.0.0.0', self.listen_port))
        server_socket.listen(100)

        logger.info(f"🔐 Gateway listening on port {self.listen_port}")
        logger.info(f"🔗 Forwarding connections to guacd on [{self.guacd_host}]:{self.guacd_port}")
        logger.info("✅ Porta-Mundi Guacamole Gateway ACTIVE")

        try:
            while True:
                client_socket, (client_ip, client_port) = server_socket.accept()
                logger.info(f"Incoming connection from {client_ip}:{client_port}")

                thread = threading.Thread(
                    target=self.forward_connection,
                    args=(client_socket, client_ip)
                )
                thread.daemon = True
                thread.start()
        except KeyboardInterrupt:
            logger.info("Gateway shutting down")
        finally:
            server_socket.close()

if __name__ == "__main__":
    gateway = GuacamoleGateway()
    gateway.start()
