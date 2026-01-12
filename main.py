from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, create_engine
from sqlalchemy.orm import relationship, sessionmaker, Session, declarative_base
from pydantic import BaseModel
from typing import List

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./vibe_check.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---
class Poll(Base):
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(String, nullable=False)
    options = relationship("Option", back_populates="poll", cascade="all, delete-orphan")

class Option(Base):
    __tablename__ = "options"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    option_text = Column(String, nullable=False)
    vote_count = Column(Integer, default=0)
    poll = relationship("Poll", back_populates="options")

class Vote(Base):
    __tablename__ = "votes"
    id = Column(Integer, primary_key=True, index=True)
    poll_id = Column(Integer, ForeignKey("polls.id"))
    user_id = Column(String, nullable=False)
    
    # Ensures a user can only vote once per poll
    __table_args__ = (UniqueConstraint('poll_id', 'user_id', name='_user_poll_uc'),)

# Create tables
Base.metadata.create_all(bind=engine)

# --- SCHEMAS (Pydantic) ---
class OptionCreate(BaseModel):
    text: str

class PollCreate(BaseModel):
    question: str
    options: List[str]

class VoteRequest(BaseModel):
    user_id: str
    option_id: int

# --- API HELPERS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(title="Vibe Check Polling API")

# --- ENDPOINTS ---

@app.post("/polls", status_code=201)
def create_poll(poll_data: PollCreate, db: Session = Depends(get_db)):
    new_poll = Poll(question=poll_data.question)
    db.add(new_poll)
    db.flush()  # Get the poll ID before committing
    
    for opt_text in poll_data.options:
        db.add(Option(poll_id=new_poll.id, option_text=opt_text))
    
    db.commit()
    return {"message": "Poll created successfully", "poll_id": new_poll.id}

@app.get("/polls/{poll_id}")
def get_poll(poll_id: int, db: Session = Depends(get_db)):
    poll = db.query(Poll).filter(Poll.id == poll_id).first()
    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    
    return {
        "question": poll.question,
        "options": [{"id": o.id, "text": o.option_text, "votes": o.vote_count} for o in poll.options]
    }

@app.post("/polls/{poll_id}/vote")
def cast_vote(poll_id: int, request: VoteRequest, db: Session = Depends(get_db)):
    # 1. Check if user already voted in this poll
    existing_vote = db.query(Vote).filter(Vote.poll_id == poll_id, Vote.user_id == request.user_id).first()
    if existing_vote:
        raise HTTPException(status_code=400, detail="User has already voted in this poll")

    # 2. Check if the option belongs to this poll
    option = db.query(Option).filter(Option.id == request.option_id, Option.poll_id == poll_id).first()
    if not option:
        raise HTTPException(status_code=404, detail="Option not found for this poll")

    # 3. Record vote and increment counter
    new_vote = Vote(poll_id=poll_id, user_id=request.user_id)
    option.vote_count += 1
    db.add(new_vote)
    db.commit()
    
    return {"message": "Vote cast successfully"}