from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Form, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Field, Session, SQLModel, create_engine, select
from contextlib import asynccontextmanager
from sqlalchemy import or_
import razorpay
import os

# ================================
# CONFIG
# ================================
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "your_key_id")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "your_key_secret")

DATABASE_URL = "sqlite:///./tourism.db"

engine = create_engine(DATABASE_URL, echo=True)

# ================================
# DB MODELS
# ================================
class Attraction(SQLModel, table=True):
    __tablename__ = "attraction"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    description: Optional[str] = None
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None


class TouristBooking(SQLModel, table=True):
    __tablename__ = "tourist_bookings"

    id: Optional[int] = Field(default=None, primary_key=True)
    tourist_name: str = Field(index=True)
    email: str = Field(index=True)
    package: str
    amount: float
    currency: str = "INR"
    order_id: str = Field(unique=True)
    payment_id: Optional[str] = None
    status: str = "PENDING"


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str


class Booking(SQLModel, table=True):
    __tablename__ = "booking"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    attraction_id: int
    date: str


# ================================
# Pydantic Models
# ================================
class AttractionCreate(SQLModel):
    name: str
    description: Optional[str] = None
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None


class AttractionRead(Attraction):
    pass


class AttractionUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None
    historical_background: Optional[str] = None
    scenic_spots: Optional[str] = None
    nearby_restaurants_hotels: Optional[str] = None
    entry_fee: Optional[str] = None
    food_cost_range: Optional[str] = None
    travel_cost_estimate: Optional[str] = None
    stay_cost_per_night: Optional[str] = None
    best_time_visit: Optional[str] = None


# ================================
# DB SESSION
# ================================
def get_session():
    with Session(engine) as session:
        yield session


# ================================
# SEED DATA
# ================================
def seed_data():
    sample = [
        {
            "name": "Baba Baidyanath Temple, Deoghar",
            "description": "One of the 12 Jyotirlingas, a major Shiva temple and pilgrimage center.",
            "historical_background": "Linked to Hindu mythology; center of faith for centuries.",
            "scenic_spots": "Nandan Pahar hills with panoramic views.",
            "nearby_restaurants_hotels": "Shree Mithila Bhojnalaya, Hotel Satyam",
            "entry_fee": "₹60",
            "food_cost_range": "150 – 400",
            "travel_cost_estimate": "500 – 1500",
            "stay_cost_per_night": "600 – 1200",
            "best_time_visit": "July–Aug (Shravan Mela) & Oct–Feb | 4:00 AM – 9:00 PM"
        }
    ]

    with Session(engine) as session:
        existing = session.exec(select(Attraction)).first()

        if not existing:
            for item in sample:
                session.add(Attraction(**item))

            session.commit()
            print("Sample data inserted")


# ================================
# APP LIFESPAN
# ================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Creating database tables...")
    SQLModel.metadata.create_all(engine)

    seed_data()

    yield

    print("Shutting down...")


# ================================
# FASTAPI APP
# ================================
app = FastAPI(lifespan=lifespan)

# ================================
# CORS
# ================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================================
# Razorpay Setup
# ================================
razorpay_client = razorpay.Client(
    auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
)

# ================================
# ROUTES
# ================================
@app.get("/")
def root():
    return {"message": "Server is running"}


@app.get("/destinations")
def get_destinations():
    return {
        "destinations": [
            {"id": 1, "name": "Ranchi"},
            {"id": 2, "name": "Jamshedpur"},
            {"id": 3, "name": "Dhanbad"},
            {"id": 4, "name": "Hazaribagh"}
        ]
    }


@app.get("/attractions", response_model=List[AttractionRead])
def get_attractions(
    q: Optional[str] = Query(None),
    db: Session = Depends(get_session)
):
    statement = select(Attraction)

    if q:
        statement = statement.where(
            or_(
                Attraction.name.contains(q),
                Attraction.description.contains(q)
            )
        )

    return db.exec(statement).all()


@app.get("/attractions/{attraction_id}", response_model=AttractionRead)
def get_attraction(
    attraction_id: int,
    db: Session = Depends(get_session)
):
    attraction = db.get(Attraction, attraction_id)

    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")

    return attraction


@app.post("/attractions", response_model=AttractionRead)
def create_attraction(
    attraction: AttractionCreate,
    db: Session = Depends(get_session)
):
    db_attraction = Attraction.model_validate(attraction)

    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)

    return db_attraction


@app.put("/attractions/{attraction_id}", response_model=AttractionRead)
def update_attraction(
    attraction_id: int,
    data: AttractionUpdate,
    db: Session = Depends(get_session)
):
    db_attraction = db.get(Attraction, attraction_id)

    if not db_attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")

    update_data = data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_attraction, key, value)

    db.add(db_attraction)
    db.commit()
    db.refresh(db_attraction)

    return db_attraction


@app.delete("/attractions/{attraction_id}")
def delete_attraction(
    attraction_id: int,
    db: Session = Depends(get_session)
):
    attraction = db.get(Attraction, attraction_id)

    if not attraction:
        raise HTTPException(status_code=404, detail="Attraction not found")

    db.delete(attraction)
    db.commit()

    return {"ok": True}


@app.post("/create_order")
async def create_order(
    tourist_name: str = Form(...),
    email: str = Form(...),
    package: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_session)
):
    if RAZORPAY_KEY_ID == "your_key_id":
        raise HTTPException(
            status_code=500,
            detail="Razorpay keys not configured"
        )

    amount_paise = int(amount * 100)

    try:
        order = razorpay_client.order.create({
            "amount": amount_paise,
            "currency": "INR",
            "payment_capture": 1
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    booking = TouristBooking(
        tourist_name=tourist_name,
        email=email,
        package=package,
        amount=amount,
        order_id=order["id"]
    )

    db.add(booking)
    db.commit()
    db.refresh(booking)

    return {
        "order_id": order["id"],
        "amount": amount_paise,
        "currency": "INR",
        "key": RAZORPAY_KEY_ID
    }


@app.post("/verify_payment")
async def verify_payment(
    request: Request,
    db: Session = Depends(get_session)
):
    data = await request.json()

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")

    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=400,
            detail="Invalid payment signature"
        )

    booking = db.exec(
        select(TouristBooking).where(
            TouristBooking.order_id == razorpay_order_id
        )
    ).first()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    booking.payment_id = razorpay_payment_id
    booking.status = "PAID"

    db.add(booking)
    db.commit()

    return {
        "status": "success",
        "message": "Payment verified"
    }
