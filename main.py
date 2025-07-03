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
import logging
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

load_dotenv()

# Firebase setup
def initialize_firebase():
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
    except ValueError:
        # Initialize Firebase
        if os.getenv("FIREBASE_CREDENTIALS_PATH"):
            # Use service account file
            cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
        else:
            # Use service account JSON from environment variable
            firebase_config = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_KEY", "{}"))
            cred = credentials.Certificate(firebase_config)
        
        firebase_admin.initialize_app(cred)

# Initialize Firebase
initialize_firebase()
db = firestore.client()

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
        "https://portfolio-3z3s.onrender.com"
        ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("SECRET_KEY", "ud-YFzJu4XJPAx38LLP5ds6u6y2qwu94UCcbiDmOLVY")
ALGORITHM = "HS256"

# Firestore Collections
CONTACTS_COLLECTION = "contacts"
PROJECT_VIEWS_COLLECTION = "project_views"

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

# Firestore Helper Functions
def create_contact_document(contact_data: dict) -> str:
    """Create a new contact document in Firestore"""
    try:
        doc_data = {
            "name": contact_data["name"],
            "email": contact_data["email"],
            "message": contact_data["message"],
            "created_at": firestore.SERVER_TIMESTAMP,
            "is_read": False
        }
        doc_ref = db.collection(CONTACTS_COLLECTION).document()
        doc_ref.set(doc_data)
        return doc_ref.id
    except Exception as e:
        logger.error(f"Error creating contact document: {str(e)}")
        raise

def create_project_view_document(view_data: dict) -> str:
    """Create a new project view document in Firestore"""
    try:
        doc_data = {
            "project_name": view_data["project_name"],
            "user_ip": view_data.get("user_ip"),
            "viewed_at": firestore.SERVER_TIMESTAMP
        }
        doc_ref = db.collection(PROJECT_VIEWS_COLLECTION).document()
        doc_ref.set(doc_data)
        return doc_ref.id
    except Exception as e:
        logger.error(f"Error creating project view document: {str(e)}")
        raise

def get_all_contacts() -> List[dict]:
    """Get all contacts from Firestore"""
    try:
        contacts = []
        docs = db.collection(CONTACTS_COLLECTION).stream()
        for doc in docs:
            contact_data = doc.to_dict()
            contact_data["id"] = doc.id
            contacts.append(contact_data)
        return contacts
    except Exception as e:
        logger.error(f"Error fetching contacts: {str(e)}")
        raise

def get_all_project_views() -> List[dict]:
    """Get all project views from Firestore"""
    try:
        views = []
        docs = db.collection(PROJECT_VIEWS_COLLECTION).stream()
        for doc in docs:
            view_data = doc.to_dict()
            view_data["id"] = doc.id
            views.append(view_data)
        return views
    except Exception as e:
        logger.error(f"Error fetching project views: {str(e)}")
        raise

def get_recent_documents(collection_name: str, days: int = 7) -> List[dict]:
    """Get recent documents from a collection"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        docs = db.collection(collection_name).where(
            filter=FieldFilter("created_at", ">=", cutoff_date)
        ).stream()
        
        documents = []
        for doc in docs:
            doc_data = doc.to_dict()
            doc_data["id"] = doc.id
            documents.append(doc_data)
        return documents
    except Exception as e:
        logger.error(f"Error fetching recent documents from {collection_name}: {str(e)}")
        raise

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
        "message": "Portfolio API with Firebase Firestore",
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
async def track_project_view(project_id: int, request: Request):
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
        
        # Create view record in Firestore
        view_data["project_name"] = project["title"]
        document_id = create_project_view_document(view_data)
        
        response_data = {
            "message": "View tracked successfully",
            "document_id": document_id
        }
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
async def submit_contact(request: Request, background_tasks: BackgroundTasks):
    """Submit contact form"""
    try:
        # Get request body
        body = await request.json()
        
        # Validate input data
        contact_data = validate_and_load_data(contact_message_schema, body)
        
        # Save to Firestore
        document_id = create_contact_document(contact_data)
        
        # Send email notification in background
        background_tasks.add_task(send_contact_notification, contact_data)
        
        response_data = {
            "message": "Contact message submitted successfully",
            "status": "success",
            "document_id": document_id
        }
        return api_response_schema.dump(response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting contact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit contact message")

@app.get("/api/analytics/views")
async def get_project_views():
    """Get project view analytics"""
    try:
        views = get_all_project_views()
        
        # Group by project
        project_views = {}
        for view in views:
            project_name = view.get("project_name", "Unknown")
            if project_name not in project_views:
                project_views[project_name] = 0
            project_views[project_name] += 1
        
        # Get recent views (last 7 days)
        recent_views = get_recent_documents(PROJECT_VIEWS_COLLECTION, days=7)
        
        analytics_data = {
            "total_views": len(views),
            "project_views": project_views,
            "recent_views": len(recent_views)
        }
        
        return analytics_views_schema.dump(analytics_data)
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.get("/api/analytics/contacts")
async def get_contact_analytics():
    """Get contact form analytics"""
    try:
        contacts = get_all_contacts()
        
        # Count unread contacts
        unread_contacts = len([c for c in contacts if not c.get("is_read", False)])
        
        # Get recent contacts (last 7 days)
        recent_contacts = get_recent_documents(CONTACTS_COLLECTION, days=7)
        
        analytics_data = {
            "total_contacts": len(contacts),
            "unread_contacts": unread_contacts,
            "recent_contacts": len(recent_contacts)
        }
        
        return analytics_contacts_schema.dump(analytics_data)
    except Exception as e:
        logger.error(f"Error fetching contact analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch contact analytics")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Firestore connection
        db.collection("health_check").limit(1).get()
        database_status = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        database_status = "disconnected"
    
    health_data = {
        "status": "healthy" if database_status == "connected" else "unhealthy",
        "timestamp": datetime.now(),
        "database": database_status
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