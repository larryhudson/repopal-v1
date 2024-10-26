# RepoPal Setup Instructions

## 1. GitHub OAuth App Setup

1. Go to GitHub Developer Settings:
   - Log into GitHub
   - Click your profile photo
   - Go to Settings > Developer settings > OAuth Apps
   - Click "New OAuth App"

2. Register the OAuth application:
   - Application name: `RepoPal`
   - Homepage URL: `http://localhost:5000`
   - Authorization callback URL: `http://localhost:5000/api/auth/github/callback`
   - Description: (optional) "AI-powered repository management assistant"

3. After registration, you'll receive:
   - Client ID
   - Client Secret (click "Generate a new client secret")

   Save these values securely - you'll need them for the environment variables.

## 2. Environment Variables Setup

Create a `.env` file in the project root:

```bash
# Flask
FLASK_APP=repopal.app:create_app()
FLASK_ENV=development
SECRET_KEY=your-secure-random-key

# GitHub OAuth
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret
GITHUB_APP_ID=your-app-id

# Database
DATABASE_URL=sqlite:///repopal.db

# Redis
REDIS_URL=redis://localhost:6379/0
```

Replace the placeholder values with your actual credentials.

## 3. Generate a Secure Secret Key

For the `SECRET_KEY`, use Python to generate a secure random key:

```python
import secrets
print(secrets.token_hex(32))
```

Copy the output into your `.env` file.

## 4. Install Dependencies

```bash
pip install -r requirements.txt
pip install python-dotenv alembic
```

## 5. Initialize the Database

```bash
# Initialize Alembic if this is your first time
alembic init migrations

# Apply database migrations
alembic upgrade head
```

## 6. Start Redis Server

Make sure Redis is installed and running:

```bash
# macOS (using Homebrew)
brew install redis
brew services start redis
```

## 7. Start the Application

```bash
flask run
```

The application will be available at http://localhost:5000

## Security Notes

1. Never commit the `.env` file to version control
2. Keep your GitHub OAuth credentials secure
3. Use strong, unique values for `SECRET_KEY`
4. Restrict OAuth app access to necessary scopes only

## Troubleshooting

1. If you get a "No module named 'dotenv'" error:
   ```bash
   pip install python-dotenv
   ```

2. If Redis connection fails:
   ```bash
   redis-cli ping
   ```
   Should return "PONG"

3. To check if environment variables are loaded:
   ```bash
   flask shell
   >>> import os
   >>> print(os.environ.get('GITHUB_CLIENT_ID'))
   ```