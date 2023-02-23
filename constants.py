import os

from dotenv import load_dotenv

load_dotenv()

lnd_dir = os.environ.get("LND_DIR") 
tls_cert_path= os.environ.get("TLS_CERT_PATH") 
grpc_host = os.environ.get("GRPC_HOST")
grpc_port = os.environ.get("GRPC_PORT")
macaroon_path = os.environ.get("MACAROON_PATH") 
network = os.environ.get("NETWORK") 