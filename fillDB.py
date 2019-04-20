from models import Base, User, Category, Item
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask import Flask, jsonify, request, url_for, abort, g

engine = create_engine('sqlite:///catalog.db')

# clear DB
Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)


Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


def addCategory(id, name):
    cat = session.query(Category).filter_by(id = id).first()
    if cat is not None:
        print "existing category"
        # return jsonify({'message':'category already exists'})
    cat = Category(name = name)
    session.add(cat)
    session.commit()
    # return jsonify({ 'id': cat.id, 'name' : cat.name })

def addItem(id,title, des, cat_id):

    item = session.query(Item).filter_by(id = id).first()
    if item is not None:
        print "existing item"
        # return jsonify({'message':'item already exists'})
    item = Item(description = des, title= title, cat_id = cat_id)
    session.add(item)
    session.commit()
    # return jsonify({ 'id': item.id, 'description' : item.description,
    #                  'title': item.title, 'cat ID': item.cat_id })

if __name__ == '__main__':
    addCategory(1, 'Hobbies')
    addItem(1, 'Reading', 'Reading is helpful to gain knowledge and relax', 1 )
    addItem(2, 'Shopping', 'Some people feel great while shopping', 1 )

    addCategory(2, 'Sports')
    addItem(1, 'Running', 'Running is needed for Heart Health', 2)

    addCategory(3, 'Art')
    addItem(1, 'Drawing', 'Drawing is a stress relief exercise', 3)
    addItem(2, 'Science', 'Yes :) Science is Art', 3)

    # check items in DB
    cats = session.query(Category).all()
    print [cat.name for cat in cats]

    items = session.query(Item).all()
    print [item.title for item in items]
