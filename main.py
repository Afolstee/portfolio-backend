# main.py
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from marshmallow import Schema, fields, ValidationError, validate, post_load
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt
import bcrypt
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import logging
import json

load_dotenv()

app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app initialization
app = FastAPI(
    title="Portfolio API",
    description="Backend API for professional tech portfolio",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://temiladeafo-portfolio.vercel.app",
        "https://portfolio-zm76.onrender.com"
        ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "ud-YFzJu4XJPAx38LLP5ds6u6y2qwu94UCcbiDmOLVY")
ALGORITHM = "HS256"

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class Contact(Base):
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)

class ProjectView(Base):
    __tablename__ = "project_views"
    
    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String(100), nullable=False)
    user_ip = Column(String(45))
    viewed_at = Column(DateTime, default=datetime.utcnow)

# Marshmallow Schemas
class ContactMessageSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True, validate=validate.Length(max=100))
    message = fields.Str(required=True, validate=validate.Length(min=1))
    
    @post_load
    def make_contact_message(self, data, **kwargs):
        return data

class ProjectViewCreateSchema(Schema):
    project_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    user_ip = fields.Str(allow_none=True, validate=validate.Length(max=45))
    
    @post_load
    def make_project_view(self, data, **kwargs):
        return data

class ProjectSchema(Schema):
    id = fields.Int(required=True)
    title = fields.Str(required=True)
    description = fields.Str(required=True)
    tech_stack = fields.List(fields.Str(), required=True)
    features = fields.List(fields.Str(), required=True)
    github_url = fields.Url(required=True)
    demo_url = fields.Url(required=True)
    image_emoji = fields.Str(required=True)
    category = fields.Str(required=True)
    view_count = fields.Int(load_default=0)

class SkillCategorySchema(Schema):
    name = fields.Str(required=True)
    technologies = fields.List(fields.Str(), required=True)
    icon = fields.Str(required=True)

class AnalyticsViewsSchema(Schema):
    total_views = fields.Int()
    project_views = fields.Dict(keys=fields.Str(), values=fields.Int())
    recent_views = fields.Int()

class AnalyticsContactsSchema(Schema):
    total_contacts = fields.Int()
    unread_contacts = fields.Int()
    recent_contacts = fields.Int()

class HealthCheckSchema(Schema):
    status = fields.Str()
    timestamp = fields.DateTime()
    database = fields.Str()

class ApiResponseSchema(Schema):
    message = fields.Str()
    status = fields.Str(load_default="success")

class ErrorResponseSchema(Schema):
    error = fields.Str()
    status_code = fields.Int()

# Schema instances
contact_message_schema = ContactMessageSchema()
project_view_create_schema = ProjectViewCreateSchema()
project_schema = ProjectSchema()
projects_schema = ProjectSchema(many=True)
skill_category_schema = SkillCategorySchema()
skill_categories_schema = SkillCategorySchema(many=True)
analytics_views_schema = AnalyticsViewsSchema()
analytics_contacts_schema = AnalyticsContactsSchema()
health_check_schema = HealthCheckSchema()
api_response_schema = ApiResponseSchema()
error_response_schema = ErrorResponseSchema()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
Base.metadata.create_all(bind=engine)

# Portfolio data
PROJECTS_DATA = [
    {
        "id": 1,
        "title": "Market Days",
        "description": "A location-based web application that helps users discover local markets and preview market days in their area. Built with modern web technologies and real-time data integration.",
        "tech_stack": ["HTML", "CSS", "Vanilla JS"],
        "features": ["Location-based search", "Market day previews", "Real-time data", "Mobile responsive"],
        "github_url": "https://github.com/Afolstee/market-days",
        "demo_url": "https://market-days.vercel.app/",
        "image_emoji": "🏪",
        "category": "Frontend",
        "view_count": 0
    },
    {
        "id": 2,
        "title": "Trading Simulator",
        "description": "A comprehensive paper trading platform with user authentication, real-time market data, and portfolio management. Enables risk-free trading education and strategy testing.",
        "tech_stack": ["Next.js", "Python", "FastAPI", "WebSocket"],
        "features": ["User authentication", "Portfolio tracking", "Performance analytics", "Risk management"],
        "github_url": "https://github.com/Afolstee/trading-simulator",
        "demo_url": "https://trading-sim-brown.vercel.app",
        "image_emoji": "📈",
        "category": "Full Stack",
        "view_count": 0
    },
    {
        "id": 3,
        "title": "Crypto Dashboard",
        "description": "A real-time cryptocurrency tracking dashboard featuring live price updates, market news, and portfolio management. Integrates with multiple APIs for comprehensive market data.",
        "tech_stack": ["Next.js", "Python", "CoinGecko API", "CryptoCompare API", "WebSocket", "Chart.js", "Redis"],
        "features": ["Live price tracking", "Market news", "Portfolio management", "Price alerts", "AI Technical analysis"],
        "github_url": "https://github.com/Afolstee/analyse-crypto",
        "demo_url": "https://analyse-crypto-nine.vercel.app/",
        "image_emoji": "₿",
        "category": "Full Stack",
        "view_count": 0
    },
    {
        "id": 4,
        "title": "Book a Stay",
        "description": "A modern hotel booking platform with elegant design, advanced search functionality, and seamless user experience. Features comprehensive property management and booking system.",
        "tech_stack": ["HTML", "CSS", "JavaScript"],
        "features": ["Advanced search", "Availability Filter", "Review system"],
        "github_url": "https://github.com/Afolstee/book-stay",
        "demo_url": "http://book-stay-99sx.vercel.app",
        "image_emoji": "🏨",
        "category": "Frontend",
        "view_count": 0
    },
    {
        "id": 5,
        "title": "Dakuzon",
        "description": "A modern e-commerce platform with elegant design, advanced search functionality, and seamless user experience. Features comprehensive property management and booking system.",
        "tech_stack": ["HTML", "CSS", "JavaScript"],
        "features": ["Advanced search", "Availability Filter", "Review system"],
        "github_url": "https://github.com/Afolstee/dakuzon",
        "demo_url": "https://dakuzon.vercel.app/",
        "image_emoji": "🏨",
        "category": "Frontend",
        "view_count": 0
    },
    {
        "id": 6,
        "title": "Online-Shop",
        "description": "A modern online shoe shopping platform with elegant design, advanced search functionality, and seamless user experience. Features comprehensive property management and booking system.",
        "tech_stack": ["HTML", "CSS", "JavaScript"],
        "features": ["Advanced search", "Availability Filter", "Review system"],
        "github_url": "https://github.com/Afolstee/online-shop",
        "demo_url": "https://online-shop-flame.vercel.app/",
        "image_emoji": "🏨",
        "category": "Frontend",
        "view_count": 0
    }
]

SKILLS_DATA = [
    {
        "name": "Frontend Development",
        "technologies": ["React", "Next.js", "TypeScript", "JavaScript", "HTML5", "CSS3", "Tailwind CSS", "Bootstrap"],
        "icon": "🎨"
    },
    {
        "name": "Backend Development", 
        "technologies": ["Python", "FastAPI", "Node.js", "Express.js", "RESTful APIs", "GraphQL", "WebSocket"],
        "icon": "⚙️"
    },
    {
        "name": "Database & Storage",
        "technologies": ["PostgreSQL", "MongoDB", "Redis", "SQLAlchemy", "Prisma", "Firebase"],
        "icon": "🗄️"
    },
    {
        "name": "DevOps & Tools",
        "technologies": ["Git", "Docker", "AWS", "Vercel", "Railway", "Nginx", "Linux"],
        "icon": "🚀"
    }
]

# Email configuration
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "your-email@gmail.com")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "your-app-password")

# Utility functions
def validate_and_load_data(schema: Schema, data: dict):
    """Validate and load data using Marshmallow schema"""
    try:
        return schema.load(data)
    except ValidationError as err:
        raise HTTPException(status_code=422, detail=err.messages)

def send_email(to_email: str, subject: str, body: str):
    """Send email notification"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_contact_notification(contact_data: dict):
    """Send notification when new contact message is received"""
    subject = f"New Portfolio Contact: {contact_data['name']}"
    body = f"""
    New contact message received:
    
    Name: {contact_data['name']}
    Email: {contact_data['email']}
    Message: {contact_data['message']}
    
    Received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    return send_email(SENDER_EMAIL, subject, body)

# API Routes
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Portfolio API",
        "version": "1.0.0",
        "endpoints": {
            "projects": "/api/projects",
            "skills": "/api/skills",
            "contact": "/api/contact",
            "analytics": "/api/analytics"
        }
    }

@app.get("/api/projects")
async def get_projects():
    """Get all projects"""
    try:
        validated_projects = projects_schema.dump(PROJECTS_DATA)
        return validated_projects
    except Exception as e:
        logger.error(f"Error fetching projects: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch projects")

@app.get("/api/projects/{project_id}")
async def get_project(project_id: int):
    """Get specific project by ID"""
    try:
        project = next((p for p in PROJECTS_DATA if p["id"] == project_id), None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        validated_project = project_schema.dump(project)
        return validated_project
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch project")

@app.post("/api/projects/{project_id}/view")
async def track_project_view(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Track project view for analytics"""
    try:
        # Get request body
        body = await request.json()
        
        # Validate input data
        view_data = validate_and_load_data(project_view_create_schema, body)
        
        # Verify project exists
        project = next((p for p in PROJECTS_DATA if p["id"] == project_id), None)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create view record
        db_view = ProjectView(
            project_name=project["title"],
            user_ip=view_data.get("user_ip")
        )
        db.add(db_view)
        db.commit()
        
        response_data = {"message": "View tracked successfully"}
        return api_response_schema.dump(response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking view for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track view")

@app.get("/api/skills")
async def get_skills():
    """Get all skill categories"""
    try:
        validated_skills = skill_categories_schema.dump(SKILLS_DATA)
        return validated_skills
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch skills")

@app.post("/api/contact")
async def submit_contact(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit contact form"""
    try:
        # Get request body
        body = await request.json()
        
        # Validate input data
        contact_data = validate_and_load_data(contact_message_schema, body)
        
        # Save to database
        db_contact = Contact(
            name=contact_data["name"],
            email=contact_data["email"],
            message=contact_data["message"]
        )
        db.add(db_contact)
        db.commit()
        
        # Send email notification in background
        background_tasks.add_task(send_contact_notification, contact_data)
        
        response_data = {
            "message": "Contact message submitted successfully",
            "status": "success"
        }
        return api_response_schema.dump(response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit contact message")

@app.get("/api/analytics/views")
async def get_project_views(db: Session = Depends(get_db)):
    """Get project view analytics"""
    try:
        views = db.query(ProjectView).all()
        
        # Group by project
        project_views = {}
        for view in views:
            if view.project_name not in project_views:
                project_views[view.project_name] = 0
            project_views[view.project_name] += 1
        
        analytics_data = {
            "total_views": len(views),
            "project_views": project_views,
            "recent_views": len([v for v in views if v.viewed_at > datetime.now() - timedelta(days=7)])
        }
        
        return analytics_views_schema.dump(analytics_data)
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.get("/api/analytics/contacts")
async def get_contact_analytics(db: Session = Depends(get_db)):
    """Get contact form analytics"""
    try:
        contacts = db.query(Contact).all()
        
        analytics_data = {
            "total_contacts": len(contacts),
            "unread_contacts": len([c for c in contacts if not c.is_read]),
            "recent_contacts": len([c for c in contacts if c.created_at > datetime.now() - timedelta(days=7)])
        }
        
        return analytics_contacts_schema.dump(analytics_data)
    except Exception as e:
        logger.error(f"Error fetching contact analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact analytics")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    health_data = {
        "status": "healthy",
        "timestamp": datetime.now(),
        "database": "connected"
    }
    return health_check_schema.dump(health_data)

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    error_data = {"error": "Endpoint not found", "status_code": 404}
    return error_response_schema.dump(error_data)

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    error_data = {"error": "Internal server error", "status_code": 500}
    return error_response_schema.dump(error_data)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )