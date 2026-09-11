# Tax Shield - Tax Readiness Intelligence Platform

A full-stack tax readiness platform built with Next.js, FastAPI, and MongoDB.

## Features

- **Dashboard** - Tax readiness score, income breakdown, obligations, and deadlines
- **Transactions** - Manual entry and CSV import for income, expenses, investments, and deductions
- **Documents** - Upload and manage tax-related documents
- **Obligations** - Rule-based detection of tax obligations with risk levels
- **Deadlines** - Track important tax dates and filing deadlines
- **Scenarios** - Compare alternative financial decisions and their tax impact
- **Settings** - User profile and preferences management

## Tech Stack

- **Frontend**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11+
- **Database**: MongoDB
- **Authentication**: JWT-based auth with bcrypt password hashing

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB 6+

### Using Docker (Recommended)

```bash
# Clone the repository
cd tax-shield

# Start all services
docker-compose up -d

# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your MongoDB connection string
# MONGODB_URL=mongodb://localhost:27017

# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
tax-shield/
├── backend/
│   ├── app/
│   │   ├── api.py          # API routes
│   │   ├── auth.py         # Authentication
│   │   ├── analysis.py     # Tax analysis engine
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # MongoDB connection
│   │   ├── main.py         # FastAPI app
│   │   └── models.py       # Pydantic models
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js App Router pages
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities and API client
│   │   └── types/          # TypeScript types
│   ├── package.json
│   └── tailwind.config.ts
└── docker-compose.yml
```

## Demo Mode

The platform includes a demo mode with sample data:
1. Register or login with any credentials
2. Click "Load Demo Data" on the dashboard
3. Explore pre-populated transactions, investments, deductions, and scenarios

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login
- `GET /api/auth/me` - Get current user

### Transactions
- `GET /api/transactions` - List transactions
- `POST /api/transactions` - Create transaction
- `POST /api/transactions/upload-csv` - Upload CSV
- `DELETE /api/transactions/{id}` - Delete transaction

### Investments
- `GET /api/investments` - List investments
- `POST /api/investments` - Create investment

### Deductions
- `GET /api/deductions` - List deductions
- `POST /api/deductions` - Create deduction

### Documents
- `GET /api/documents` - List documents
- `POST /api/documents` - Upload document

### Obligations
- `GET /api/obligations` - List obligations
- `PATCH /api/obligations/{id}` - Update obligation status

### Deadlines
- `GET /api/deadlines` - List deadlines
- `PATCH /api/deadlines/{id}` - Update deadline status

### Scenarios
- `GET /api/scenarios` - List scenarios
- `POST /api/scenarios` - Create scenario
- `POST /api/scenarios/compare` - Compare scenarios

### Dashboard
- `GET /api/dashboard` - Get dashboard summary
- `GET /api/readiness-score` - Get tax readiness score

## Tax Analysis Rules

The analysis engine implements rules for:
- Multiple income source detection
- Missing document identification
- Freelance income documentation requirements
- Capital gains purchase documentation
- Deduction proof verification
- Advance tax liability estimation

## License

MIT License - feel free to use for your hackathon or project!