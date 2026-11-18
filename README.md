
# Money Wallet Ledger API

A production-grade, ACID-compliant double-entry ledger REST API built with Django and PostgreSQL. Designed with strong concurrency controls, pessimistic locking, and request idempotency to guarantee financial data integrity under heavy loads.

---

## 🚀 Key Features

- **Double-Entry Ledger Architecture:** Strict separation of financial transactions ensuring every debit has a matching credit.
- **ACID Compliance & Concurrency Control:** Utilizes PostgreSQL row-level locking (`select_for_update`) to safely manage simultaneous balance updates and prevent race conditions.
- **Idempotency Guarantee:** Custom `IdempotencyMiddleware` ensures duplicate requests (e.g., due to network retries) do not result in duplicate transactions.
- **Robust Automated Testing:** Includes unit, idempotency, and multi-threaded concurrency test suites using Django's `TransactionTestCase` and `ThreadPoolExecutor`.
- **Interactive API Documentation:** Automatically generated OpenAPI/Swagger specification (`swagger.json`) with live Swagger UI and ReDoc interfaces.

---

## 🛠️ Tech Stack

- **Backend Framework:** Django, Django REST Framework (DRF)
- **Database:** PostgreSQL
- **Documentation:** `drf-yasg` (OpenAPI 2.0)
- **Concurrency & Testing:** Python `concurrent.futures`, `TransactionTestCase`

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone [https://github.com/your-username/money-wallet-api.git](https://github.com/your-username/money-wallet-api.git)
cd money-wallet-api

```

### 2. Create and Activate a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate

```

### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the root directory and configure your database settings:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
DB_NAME=wallet_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

```

### 5. Run Database Migrations

```bash
python manage.py makemigrations
python manage.py migrate

```

### 6. Run the Development Server

```bash
python manage.py runserver

```

---

## 🧪 Running Tests

To verify unit logic, idempotency handling, and multi-threaded race condition safety:

```bash
python manage.py test wallets

```

---

## 📚 API Documentation

You can explore and test the endpoints directly using the built-in interactive documentation:

* **Swagger UI:** `http://127.0.0.1:8000/swagger/`
* **ReDoc UI:** `http://127.0.0.1:8000/redoc/`
* **Raw OpenAPI Spec:** A static schema definition file is available at `swagger.json` in the root directory.

### Core Endpoints

| Method | Endpoint | Description | Headers Required |
| --- | --- | --- | --- |
| **POST** | `/api/v1/wallets/` | Create a new wallet | `Content-Type: application/json` |
| **GET** | `/api/v1/wallets/` | List all system wallets | — |
| **POST** | `/api/v1/deposits/` | Deposit funds into a wallet | `Content-Type`, `Idempotency-Key` |
| **POST** | `/api/v1/transfers/` | Execute an atomic wallet-to-wallet transfer | `Content-Type`, `Idempotency-Key` |

```

```