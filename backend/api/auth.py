"""
Auth API routes.
POST /api/auth/register — Create a new user
POST /api/auth/login    — Authenticate and return JWT token
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from core.security import hash_password, verify_password, create_access_token
from models.user import User, UserRole
from schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, SubjectSection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    """Register a new user (student, teacher, or hod)."""

    # Check if email already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # Check unique IDs based on role
    if payload.role == "student" and payload.enrollment_no:
        existing_enroll = db.query(User).filter(User.enrollment_no == payload.enrollment_no).first()
        if existing_enroll:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This enrollment number is already registered.")

    if payload.role == "teacher" and payload.teacher_id:
        existing_tid = db.query(User).filter(User.teacher_id == payload.teacher_id).first()
        if existing_tid:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This Teacher ID is already registered.")

    if payload.role == "hod" and payload.hod_id:
        existing_hid = db.query(User).filter(User.hod_id == payload.hod_id).first()
        if existing_hid:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This HOD ID is already registered.")

    # Validate role
    try:
        role = UserRole(payload.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {payload.role}. Must be student, teacher, or hod.",
        )

    # Build subjects_sections as list of dicts
    ss_data = None
    if payload.subjects_sections:
        ss_data = [{"subject": s.subject, "section": s.section} for s in payload.subjects_sections]

    user = User(
        name=payload.name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=role,
        phone=payload.phone,
        section=payload.section,
        branch=payload.branch,
        enrollment_no=payload.enrollment_no,
        father_phone=payload.father_phone,
        mother_phone=payload.mother_phone,
        session=payload.session,
        teacher_id=payload.teacher_id,
        subjects_sections=ss_data,
        hod_id=payload.hod_id,
        department=payload.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"User registered: {user.email} ({user.role})")
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return a JWT access token."""

    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    access_token = create_access_token(data={"sub": str(user.id), "role": user.role.value})

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.put("/teacher/subjects", response_model=UserResponse)
def update_teacher_subjects(
    payload: List[SubjectSection],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Allow authenticated teachers to update their subject-section list.
    """
    if current_user.role.value != "teacher":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Only teachers can update their subjects & sections.",
        )

    # Convert SubjectSection schemas to a list of dicts for JSON storage
    ss_data = [{"subject": s.subject, "section": s.section} for s in payload]
    
    current_user.subjects_sections = ss_data
    db.commit()
    db.refresh(current_user)

    logger.info(f"Teacher {current_user.email} updated subjects/sections list: {ss_data}")
    return current_user
