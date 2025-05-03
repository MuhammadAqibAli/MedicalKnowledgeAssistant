from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# SQLAlchemy Base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)