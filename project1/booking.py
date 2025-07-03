from fastapi import APIRouter
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, String, ARRAY
from datetime import datetime
from typing import List, Optional, Union
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from database import engine#  FastAPI app creation

 #  This line ensures your tables are created on app start
booking_router=APIRouter()

# ==================== DB MODELS ====================

class Room(SQLModel, table=True):
    room_id: Optional[int] = Field(default=None, primary_key=True)
    room_name: str
    room_type: str
    capacity: int
    hourly_rate: float
    amenities: List[str] = Field(sa_column=Column(ARRAY(String)))
    location: str
    floor: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Booking(SQLModel, table=True):
    booking_id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int
    start_time: datetime
    end_time: datetime
    booked_by: str
    booking_status: str  # confirmed, cancelled, etc.
    total_cost: float
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# ==================== RESPONSE MODELS ====================

class RoomDetails(SQLModel):
    room_id: int
    room_name: str
    room_type: str
    capacity: int
    hourly_rate: float
    total_cost: float
    amenities: List[str]
    location: str
    floor: int

class RequestDetails(SQLModel):
    start_time: datetime
    end_time: datetime
    duration_hours: int

class SuccessResponse(SQLModel):
    status: str
    request_details: RequestDetails
    available_rooms: List[RoomDetails]
    total_available: int
    message: Optional[str] = None

class ErrorResponse(SQLModel):
    status: str
    error_code: str
    message: str
    details: dict

# ==================== UTILITY FUNCTION ====================

def calculate_duration_hours(start: datetime, end: datetime) -> int:
    return int((end - start).total_seconds() // 3600)

# ==================== MAIN API ====================

@booking_router.post("/check-availability")
def check_availability(start_time: datetime, end_time: datetime):
    if end_time <= start_time:
        return ErrorResponse(
            status="error",
            error_code="INVALID_TIME_RANGE",
            message="End time must be after start time",
            details={
                "start_time": start_time,
                "end_time": end_time
            }
        )

    with Session(engine) as session:
        # Step 1: Only active rooms
        all_rooms = session.exec(
            select(Room).where(Room.is_active == True)
        ).all()

        available_rooms = []

        for room in all_rooms:
            # Step 2: Check booking conflict (confirmed only)
            conflict = session.exec(
                select(Booking).where(
                    (Booking.room_id == room.room_id) &
                    (Booking.booking_status == "confirmed") &
                    (
                        (Booking.start_time < end_time) &
                        (Booking.end_time > start_time)
                    )
                )
            ).first()

            if not conflict:
                duration = calculate_duration_hours(start_time, end_time)
                total_cost = room.hourly_rate * duration

                available_rooms.append(RoomDetails(
                    room_id=room.room_id,
                    room_name=room.room_name,
                    room_type=room.room_type,
                    capacity=room.capacity,
                    hourly_rate=room.hourly_rate,
                    total_cost=total_cost,
                    amenities=room.amenities,
                    location=room.location,
                    floor=room.floor
                ))

        duration = calculate_duration_hours(start_time, end_time)

        if not available_rooms:
            return JSONResponse(
                content=jsonable_encoder(SuccessResponse(
                    status="success",
                    request_details=RequestDetails(
                        start_time=start_time,
                        end_time=end_time,
                        duration_hours=duration
                    ),
                    available_rooms=[],
                    total_available=0,
                    message="No rooms available for the requested time slot"
                ), exclude_none=True)
            )

        response = SuccessResponse(
            status="success",
            request_details=RequestDetails(
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration
            ),
            available_rooms=available_rooms,
            total_available=len(available_rooms)
        )
        return JSONResponse(content=jsonable_encoder(response, exclude_none=True))