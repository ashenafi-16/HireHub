# HireHub Authentication

Django backend providing:

- JWT authentication (`djangorestframework-simplejwt`)
- Google OAuth2 social login (`django-allauth` + `dj-rest-auth`)
- Email-based registration and login (no username)
- Environment variable configuration with `.env`

## Setup

1. Clone repo and create virtual environment:
   ```bash
   git clone https://github.com/ashenafi-16/HireHub.git
   cd HireHub
   python -m venv vir-env
   source vir-env/Scripts/activate  # Windows
````

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create `.env` file with:

   ```
   SECRET_KEY=your_secret_key
   DEBUG=True
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_email_app_password
   CLIENT_ID=your_google_client_id
   CLIENT_SECRET=your_google_client_secret
   ```

4. Run migrations and start server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## API Endpoints

| Method | URL                              | Description                  |
| ------ | -------------------------------- | ---------------------------- |
| POST   | `/register/`                     | Register user                |
| POST   | `/login/`                        | Login with email/password    |
| POST   | `/logout/`                       | Logout                       |
| POST   | `auth/google/`                   | Google OAuth login           |
| POST   | `/request-reset-email/`          | Request password reset email |
| POST   | `/password-reset/<uid>/<token>/` | Verify password reset token  |
| POST   | `/password-reset-complete/`      | Set new password             |


