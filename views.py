from models import Base, User, Category, Item
from flask import Flask, jsonify, request, url_for, abort, g
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()


engine = create_engine('sqlite:///catalog.db')

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()
app = Flask(__name__)


@auth.verify_password
def verify_password(username, password):
    print "Looking for user %s" % username
    user = session.query(User).filter_by(username = username).first()
    if not user:
        print "User not found"
        return False
    elif not user.verify_password(password):
        print "Unable to verify password"
        return False
    else:
        g.user = user
        return True


@app.route('/users', methods = ['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')
    if username is None or password is None:
        print "missing arguments"
        abort(400)

    user = session.query(User).filter_by(username=username).first()
    if user is not None:
        print "existing user"
        return jsonify({'message':'user already exists'}), 200s

    user = User(username = username)
    user.hash_password(password)
    session.add(user)
    session.commit()
    return jsonify({ 'username': user.username }), 201
@app.route('/users/<int:id>')
def get_user(id):
    user = session.query(User).filter_by(id=id).one()
    if not user:
        abort(400)
    return jsonify({'username': user.username})

# Get Requests
@app.route('/')
# return all the categories and latest added items for each category
def get_all_category_latestItem():
    categories = session.query(Category).all()
    return jsonify(categories = [cat.serialize for cat in categories])
    # return jsonify({ 'Categories': 'Here are all the categories',
    #                  'Items' : 'Here are all the latest items'})

@app.route('/catalog/<string:cat>/items')
# returns the items of the specified category
def showAllItems(cat):
    # bagels = session.query(Category).filter_by()
    return jsonify('items of %s', cat)

@app.route('/catalog/<string:cat>/<string:item>')
# returns des of specified item
def showItemDes(item):
    return jsonify('description of %s', item)

@app.route('/catalog.json')
# returns des of specified item
def showJSON():
    return jsonify('JSON file')

# PUT, DELETE, POST Requests

@app.route('/catalog.json')
# returns des of specified item
@app.route('/catalog/<string:cat>/<string:item>/edit', methods = ['PUT'])
# edits the specified item
def editItem(item):
    return jsonify('editing %s', item)
@app.route('/catalog/<string:cat>/<string:item>/delete', methods = ['DELETE'])
# delete the specified item
def deleteItem(item):
    return jsonify('deleting %s', item)
@app.route('/additem', methods = ['POST'])
# add the specified item
def addItem(item):
    return jsonify('Adding %s', item)

@app.route('/addcat', methods= ['GET'])
# add cat
def addCategory():
    id = request.json.get('id')
    name = request.json.get('name')
    cat = session.query(Category).filter_by(id = id).first()
    if cat is not None:
        print "existing category"
        return jsonify({'message':'category already exists'}), 200
    cat = Category(id = id, name = name)
    session.add(cat)
    session.commit()
    return jsonify({ 'id': cat.id, 'name' : cat.name }), 201





if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
