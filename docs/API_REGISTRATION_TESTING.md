# API Registration Endpoint - Manual Testing Guide

## Endpoint Details
- **URL**: `http://localhost:8000/api/auth/registration/`
- **Method**: `POST`
- **Content-Type**: `application/json`
- **Authentication**: None (publicly accessible)

## Test Case 1: Successful Registration

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Expected Response (201 Created)
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user_id": 1,
  "email": "testuser@example.com"
}
```

---

## Test Case 2: Email Already Exists

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@example.com",
    "password": "AnotherPass456!",
    "password_confirm": "AnotherPass456!"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "email": ["Użytkownik z tym adresem email już istnieje."]
}
```

---

## Test Case 3: Password Mismatch

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "password_confirm": "DifferentPass456!"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "password_confirm": ["Hasła nie są identyczne."]
}
```

---

## Test Case 4: Weak Password (Too Short)

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "weakpass@example.com",
    "password": "short",
    "password_confirm": "short"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "password": [
    "To hasło jest zbyt krótkie. Musi zawierać co najmniej 8 znaków."
  ]
}
```

---

## Test Case 5: Common Password

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "common@example.com",
    "password": "password123",
    "password_confirm": "password123"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "password": [
    "To hasło jest zbyt powszechne."
  ]
}
```

---

## Test Case 6: Invalid Email Format

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "invalid-email",
    "password": "SecurePass123!",
    "password_confirm": "SecurePass123!"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "email": ["Wprowadź prawidłowy adres e-mail."]
}
```

---

## Test Case 7: Missing Required Fields

### Request
```bash
curl -X POST http://localhost:8000/api/auth/registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com"
  }'
```

### Expected Response (400 Bad Request)
```json
{
  "password": ["Hasło jest wymagane."],
  "password_confirm": ["Potwierdzenie hasła jest wymagane."]
}
```

---

## Verification Steps

After successful registration:

1. **Verify User in Database**:
```bash
docker compose exec app python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); print(User.objects.filter(email='testuser@example.com').exists())"
```

2. **Verify Token in Database**:
```bash
docker compose exec app python manage.py shell -c "from rest_framework.authtoken.models import Token; from django.contrib.auth import get_user_model; User = get_user_model(); user = User.objects.get(email='testuser@example.com'); print(Token.objects.filter(user=user).exists())"
```

3. **Test Token Authentication** (use token from registration response):
```bash
curl -X GET http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b"
```

---

## Rate Limiting

The endpoint is protected by rate limiting:
- **Anonymous users**: 5 requests per minute
- Exceeding this limit will return `429 Too Many Requests`

---

## Security Features

✅ **Email Normalization**: Emails are converted to lowercase  
✅ **Password Validation**: Django's built-in password validators  
✅ **Password Hashing**: Automatic secure password hashing  
✅ **Transaction Atomic**: User and token created in single transaction  
✅ **Rate Limiting**: Protection against brute force attacks  
✅ **CSRF Exempt**: API endpoint (for API clients)
