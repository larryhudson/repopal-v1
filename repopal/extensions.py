"""Flask extensions and shared instances"""

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
from repopal.utils.crypto import CredentialEncryption

# Database setup
engine = create_engine("postgresql://localhost/repopal")  # TODO: Get from config
db_session = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )
)

# Credential encryption setup
credential_encryption = CredentialEncryption(
    master_key="dev-key-replace-in-prod"  # TODO: Get from config
)
