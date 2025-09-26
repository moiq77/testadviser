# RIASEC Career Test API

This project provides a backend API for a RIASEC career test application. It allows students to take a test, receive scores based on the RIASEC model, and get recommendations for university majors.

## Backend Improvements

This version of the backend includes significant improvements to security, structure, and maintainability.

### Key Features
- **FastAPI Backend**: A modern, high-performance web framework for building APIs.
- **MongoDB Database**: A flexible NoSQL database for storing application data.
- **RIASEC Logic**: Calculates scores and provides recommendations based on the Holland Codes.
- **JWT Authentication**: Secure endpoints for administrators using JSON Web Tokens.
- **Refactored Codebase**: The code is organized into modules for models, utils, and initial data, making it easier to maintain and extend.

## Backend Setup and Usage

### 1. Prerequisites
- Python 3.8+
- MongoDB instance (local or cloud-based, like MongoDB Atlas)

### 2. Installation

Clone the repository and navigate to the `backend` directory.

```bash
git clone <repository_url>
cd testadviser/backend
```

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

Install the required dependencies. For development, use `requirements-dev.txt` to get all tools for testing and linting.

```bash
# For development (recommended)
pip install -r requirements-dev.txt

# For production only
pip install -r requirements.txt
```

### 3. Environment Configuration

The backend requires a `.env` file for configuration. Create a file named `.env` inside the `backend` directory.

```
# backend/.env

# MongoDB connection
MONGO_URL=mongodb://localhost:27017/
DB_NAME=riasec_test

# CORS Origins (comma-separated, * for all)
CORS_ORIGINS=http://localhost:3000

# JWT Settings
SECRET_KEY=your_very_strong_secret_key_for_jwt
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH= # This will be generated in the next step
```

### 4. Setting Up the Admin Account

The admin account is secured with a hashed password. To generate a hash for your desired password, run the following command from within the `backend` directory:

```bash
python hash_password.py your_admin_password
```

Copy the generated hash and paste it into the `ADMIN_PASSWORD_HASH` field in your `.env` file.

**Example:**
If the script outputs `$2b$12$...`, your `.env` file should look like this:
`ADMIN_PASSWORD_HASH=$2b$12$...`

### 5. Running the Backend Server

Once the setup is complete, you can run the server using `uvicorn`.

```bash
uvicorn server:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation at `http://127.0.0.1:8000/docs`.

### 6. Using the Admin Panel

To access the protected admin endpoints, you first need to obtain an access token.

1.  Go to the API docs: `http://127.0.0.1:8000/docs`.
2.  Find the `/api/admin/login` endpoint and open it.
3.  Click "Try it out".
4.  Enter the admin username and password (the one you hashed earlier) in the `request body` fields.
5.  Execute the request. You will receive an `access_token`.

To authorize future requests:
1.  Click the "Authorize" button at the top of the page.
2.  In the "Value" field, type `bearer ` followed by your access token.
3.  Click "Authorize". You can now access the locked admin endpoints.

## Frontend Notice

The source code for the frontend application (`src`, `public`, `package.json`) was not found in the repository. The existing frontend configuration files suggest it is a `Create React App` project. To run the full application, you will need to locate the frontend source code and integrate it with this improved backend.