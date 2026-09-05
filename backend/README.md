# LearnLoop Backend

This is the FastAPI backend for the LearnLoop adaptive study system.

## Setup Instructions

1. **Create Python Environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env` and configure your database URL.
   ```bash
   cp .env.example .env
   ```

4. **Start PostgreSQL**:
   Use Docker Compose to start a local Postgres instance.
   ```bash
   docker-compose up -d
   ```

5. **Run FastAPI Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Run Tests**:
   ```bash
   pytest
   ```
