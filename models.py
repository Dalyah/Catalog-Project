from sqlalchemy import Column,Integer,String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from passlib.apps import custom_app_context as pwd_context
Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(32), index=True)
    password_hash = Column(String(64))

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)
class Category(Base):
    __tablename__ = 'category'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    # item = Column(String)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'id' : self.id,
        'name' : self.name,
        # 'item' : self.item,
            }

class Item(Base):
    __tablename__ = 'item'
    cat_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)
    id = Column(Integer, primary_key=True)
    description = Column(String)
    title = Column(String, nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
        'cat_id' : self.cat_id,
        'description' : self.description,
        'id' : self.id,
        'title': self.title
            }


engine = create_engine('sqlite:///catalog.db')
Base.metadata.create_all(engine)
