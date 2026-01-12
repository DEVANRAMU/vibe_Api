# vibe_Api : Real-time Polling API

A lightweight RESTful API built for the Backend Internship Challenge. This system allows users to create polls and cast votes while ensuring strict data integrity.

## 🚀 How to Run the App

This project uses **Python 3.12+** and **FastAPI**. Follow these steps to set up the environment locally:

### 1. Clone & Setup

```bash
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux

# Install dependencies
pip install -r requirements.txt

```

### 2. Start the Server

```bash
uvicorn main:app --reload

```

The API will be live at `http://127.0.0.1:8000`.

### 3. Interactive Documentation

FastAPI provides an automatic UI to test the endpoints. Open your browser and navigate to:
**`http://127.0.0.1:8000/docs`**

---

## 🧠 Handling "One Vote Per User" Logic

The core challenge was ensuring a `user_id` can only vote once per `poll_id`. I implemented a **dual-layer protection strategy** to handle this:

### 1. Application Layer Validation

In the `POST /polls/:id/vote` endpoint, the API performs an explicit check before allowing a write operation:

```python
existing_vote = db.query(Vote).filter(
    Vote.poll_id == poll_id, 
    Vote.user_id == request.user_id
).first()

if existing_vote:
    raise HTTPException(status_code=400, detail="User has already voted")

```

This provides immediate feedback to the user with a clear error message.

### 2. Database Layer Enforcement (Unique Constraint)

To prevent race conditions (where two identical requests arrive at the exact same millisecond), I enforced a **Composite Unique Constraint** in the SQLite schema:

```python
__table_args__ = (UniqueConstraint('poll_id', 'user_id', name='_user_poll_uc'),)

```

This ensures that even if the application check somehow passes, the database itself will reject the duplicate entry, maintaining 100% data integrity.

---

## 🛠️ Technical Decisions

* **FastAPI:** Chosen for its high performance and native support for Pydantic validation.
* **SQLAlchemy:** Used for ORM to keep the code clean and database-agnostic.
* **SQLite:** Selected for the database to ensure the reviewer can run the project instantly without setting up a database server.

---

### Final Submission Checklist

1. **`main.py`**: Contains the API and Database models.
2. **`requirements.txt`**: Run `pip freeze > requirements.txt` to generate this.
3. **`README.md`**: This file.
4. **`.gitignore`**: Ensure you are **not** uploading the `venv/` folder or the `.db` file.

**Would you like me to help you format the `.gitignore` file to make sure your repo stays clean?**
