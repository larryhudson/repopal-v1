"""Flask extensions and shared instances"""

from flask_sqlalchemy import SQLAlchemy
from repopal.utils.crypto import CredentialEncryption

# Initialize Flask-SQLAlchemy
db = SQLAlchemy()

# Credential encryption setup
credential_encryption = CredentialEncryption(
    master_key="dev-key-replace-in-prod"  # TODO: Get from config
)
