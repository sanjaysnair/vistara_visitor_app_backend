from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pydantic import BaseModel, EmailStr
from typing import Optional
import os
from dotenv import load_dotenv
import resend
import base64
from fastapi import Depends
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/apartment_security")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Visitor(Base):
    __tablename__ = "visitors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    flat_number = Column(String, nullable=False)
    photo_path = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    email_sent = Column(String, default="pending")  # pending, sent, failed
    
# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic models
class VisitorCreate(BaseModel):
    name: str
    phone: str
    flat_number: str
    flat_owner_email: Optional[str] = None

class VisitorResponse(BaseModel):
    id: int
    name: str
    phone: str
    flat_number: str
    timestamp: datetime
    email_sent: str
    
    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title="Apartment Visitor Security System")

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Email configuration with Resend
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL", "onboarding@resend.dev")  # Replace with your verified domain
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "getsanjaysnair@gmail.com")

# Configure Resend
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY
    logger.info(f"Email Configuration: Resend API configured with FROM_EMAIL={FROM_EMAIL}")
else:
    logger.warning("RESEND_API_KEY not set - email notifications will fail")

def send_email_notification(visitor_data: dict, photo_base64: str, flat_owner_email: Optional[str] = None):
    """Send email notification to admin and flat owner using Resend"""
    try:
        if not RESEND_API_KEY:
            logger.error("RESEND_API_KEY not configured")
            return False
            
        # Main recipients: prominentvistararwa@gmail.com + flat owner email (if provided)
        recipients = ["prominentvistararwa@gmail.com"]
        if flat_owner_email and flat_owner_email != "prominentvistararwa@gmail.com":
            recipients.append(flat_owner_email)
        
        # BCC: Admin email only
        bcc_recipients = []
        if ADMIN_EMAIL and ADMIN_EMAIL not in recipients:
            bcc_recipients.append(ADMIN_EMAIL)
        
        # Prepare photo data URI for HTML embedding
        photo_data_uri = ""
        if photo_base64:
            # Remove data URI prefix if present
            if ',' in photo_base64:
                photo_data_uri = photo_base64  # Already has data:image prefix
            else:
                photo_data_uri = f"data:image/jpeg;base64,{photo_base64}"
        
        # Create HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e0e0e0;
                }}
                .info-box {{
                    background: #f8f9fa;
                    border-left: 4px solid #667eea;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }}
                .info-row {{
                    display: flex;
                    padding: 8px 0;
                    border-bottom: 1px solid #e9ecef;
                }}
                .info-label {{
                    font-weight: 600;
                    color: #495057;
                    min-width: 140px;
                }}
                .info-value {{
                    color: #212529;
                }}
                .photo-container {{
                    text-align: center;
                    margin: 20px 0;
                }}
                .photo-container img {{
                    max-width: 100%;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #6c757d;
                    border-radius: 0 0 10px 10px;
                }}
                .alert-badge {{
                    display: inline-block;
                    background: #dc3545;
                    color: white;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1 style="margin: 0;">🏢 Visitor Check-In Alert</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">Security Notification System</p>
            </div>
            
            <div class="content">
                <div class="alert-badge">NEW VISITOR</div>
                <h2 style="color: #667eea; margin-top: 0;">Visitor Details</h2>
                
                <div class="info-box">
                    <div class="info-row">
                        <span class="info-label">👤 Name:</span>
                        <span class="info-value">{visitor_data['name']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">📱 Phone:</span>
                        <span class="info-value">{visitor_data['phone']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">🏠 Visiting Flat:</span>
                        <span class="info-value">{visitor_data['flat_number']}</span>
                    </div>
                    <div class="info-row">
                        <span class="info-label">🕐 Check-In Time:</span>
                        <span class="info-value">{visitor_data['timestamp']}</span>
                    </div>
                </div>
                
                <h3 style="color: #667eea;">📸 Visitor Photo</h3>
                <div class="photo-container">
                    <img src="{photo_data_uri}" alt="Visitor Photo">
                </div>
            </div>
            
            <div class="footer">
                <p style="margin: 0;"><strong>Automated Security System</strong></p>
                <p style="margin: 5px 0 0 0;">This notification was generated automatically by the Apartment Visitor Management System</p>
                <p style="margin: 10px 0 0 0; font-size: 11px;">Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}</p>
            </div>
        </body>
        </html>
        """
        
        # Send email via Resend API
        logger.info(f"Sending email via Resend to: {', '.join(recipients)}, BCC: {', '.join(bcc_recipients)}")
        
        params = {
            "from": FROM_EMAIL,
            "to": recipients,
            "subject": f"🏢 New Visitor Check-In - {visitor_data['name']}",
            "html": html_body,
        }
        
        # Add BCC if present
        if bcc_recipients:
            params["bcc"] = bcc_recipients
        
        response = resend.Emails.send(params)
        logger.info(f"Email sent successfully via Resend. Response: {response}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        logger.error(f"Email sending failed: {str(e)}")
        return False

# API Endpoints
@app.get("/")
def read_root():
    return {
        "message": "Apartment Visitor Security API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/visitors": "Create new visitor entry",
            "GET /api/visitors": "Get all visitors",
            "GET /api/visitors/{id}": "Get visitor by ID",
            "GET /api/stats": "Get visitor statistics"
        }
    }

@app.post("/api/visitors", response_model=VisitorResponse)
async def create_visitor(
    name: str = Form(...),
    phone: str = Form(...),
    flat_number: str = Form(...),
    flat_owner_email: Optional[str] = Form(None),
    photo: str = Form(...),  # Base64 encoded photo
    db: Session = Depends(get_db)
):
    """Create a new visitor entry and send email notifications"""
    try:
        # Create visitor record
        visitor = Visitor(
            name=name,
            phone=phone,
            flat_number=flat_number,
            photo_path=f"visitor_{datetime.now().timestamp()}.jpg"
        )
        
        # Save photo to disk (optional - you can also store in DB or S3)
        photo_dir = "uploads/photos"
        os.makedirs(photo_dir, exist_ok=True)
        
        if ',' in photo:
            photo_data = photo.split(',')[1]
        else:
            photo_data = photo
            
        photo_bytes = base64.b64decode(photo_data)
        photo_path = os.path.join(photo_dir, visitor.photo_path)
        
        with open(photo_path, 'wb') as f:
            f.write(photo_bytes)
        
        # Prepare visitor data for email
        visitor_data = {
            'name': name,
            'phone': phone,
            'flat_number': flat_number,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Send email notification
        try:
            send_email_notification(visitor_data, photo, flat_owner_email)
            visitor.email_sent = "sent"
        except Exception as email_error:
            logger.error(f"Email sending failed: {email_error}")
            visitor.email_sent = "failed"
        
        # Save to database
        db.add(visitor)
        db.commit()
        db.refresh(visitor)
        
        return visitor
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating visitor: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create visitor: {str(e)}")

@app.get("/api/visitors")
def get_visitors(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all visitors with pagination"""
    visitors = db.query(Visitor).order_by(Visitor.timestamp.desc()).offset(skip).limit(limit).all()
    total = db.query(Visitor).count()
    
    return {
        "total": total,
        "visitors": visitors
    }

@app.get("/api/visitors/{visitor_id}", response_model=VisitorResponse)
def get_visitor(visitor_id: int, db: Session = Depends(get_db)):
    """Get a specific visitor by ID"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return visitor

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    """Get visitor statistics"""
    from sqlalchemy import func, desc
    
    total_visitors = db.query(Visitor).count()
    today_visitors = db.query(Visitor).filter(
        func.date(Visitor.timestamp) == datetime.now().date()
    ).count()
    
    # Most visited flats
    top_flats = db.query(
        Visitor.flat_number,
        func.count(Visitor.id).label('count')
    ).group_by(Visitor.flat_number).order_by(desc('count')).limit(5).all()
    
    # Visitors per day (last 7 days)
    from datetime import timedelta
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_visitors = db.query(
        func.date(Visitor.timestamp).label('date'),
        func.count(Visitor.id).label('count')
    ).filter(Visitor.timestamp >= seven_days_ago).group_by(
        func.date(Visitor.timestamp)
    ).order_by('date').all()
    
    return {
        "total_visitors": total_visitors,
        "today_visitors": today_visitors,
        "top_flats": [{"flat": flat, "visits": count} for flat, count in top_flats],
        "email_success_rate": db.query(Visitor).filter(Visitor.email_sent == "sent").count() / max(total_visitors, 1) * 100,
        "daily_visitors": [{"date": str(date), "count": count} for date, count in daily_visitors]
    }

@app.get("/api/visitors/search/{query}")
def search_visitors(query: str, db: Session = Depends(get_db)):
    """Search visitors by name, phone, or flat number"""
    from sqlalchemy import or_
    visitors = db.query(Visitor).filter(
        or_(
            Visitor.name.ilike(f"%{query}%"),
            Visitor.phone.ilike(f"%{query}%"),
            Visitor.flat_number.ilike(f"%{query}%")
        )
    ).order_by(Visitor.timestamp.desc()).all()
    
    return {
        "query": query,
        "total": len(visitors),
        "visitors": visitors
    }

@app.put("/api/visitors/{visitor_id}")
def update_visitor(
    visitor_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    flat_number: str = Form(...),
    flat_owner_email: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Update a visitor record"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    visitor.name = name
    visitor.phone = phone
    visitor.flat_number = flat_number
    db.commit()
    db.refresh(visitor)
    
    return visitor

@app.delete("/api/visitors/{visitor_id}")
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)):
    """Delete a visitor record"""
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Delete photo file
    photo_path = os.path.join("uploads/photos", visitor.photo_path)
    if os.path.exists(photo_path):
        os.remove(photo_path)
    
    db.delete(visitor)
    db.commit()
    
    return {"message": "Visitor deleted successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
