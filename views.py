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


@app.route('/users', methods = ['POST']) # not working
def new_user():
	username = request.args.get('username')
	password = request.args.get('password')
	if username is None or password is None:
		print "missing arguments"
		abort(400)

	user = session.query(User).filter_by(username=username).first()
	if user is not None:
		print "existing user"
		return jsonify({'message':'user already exists'}), 200

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

@app.route('/catalog/<string:cat>/items')
# returns the items of the specified category
def showAllItems(cat):
	category = session.query(Category).filter_by(name=cat).first()
	cat_id = category.id
	items = session.query(Item).filter_by(cat_id=cat_id)
	# render html template by sending items and category

	return jsonify(items = [item.serialize for item in items])

@app.route('/catalog/<string:cat>/<string:item>')
# returns des of specified item
def showItemDes(cat, item):
	category = session.query(Category).filter_by(name=cat).first()
	item = session.query(Item).filter_by(title=item, cat_id= category.id).first()
	item_des = item.description
	# render html template by sending item_des
	return jsonify(item.description)

@app.route('/catalog.json')
# returns all categories in catalog
def showJSON():
	categories = session.query(Category).all()

	# for cat in categories:
	# 	items = session.query(Item).filter_by( cat_id= cat.id)
	# 	items_cat = []
	# 	for item in items:
	# 		items_cat.append(item.serialize)
	# 	cat.append(items_cat)

	return jsonify(categories = [category.serialize for category in categories])

# PUT, DELETE, POST Requests
@app.route('/catalog/<string:cat>/<string:item>/edit', methods = ['PUT'])
# edits the specified item
def editItem(cat, item):
	category = session.query(Category).filter_by(name=cat).first()
	item = session.query(Item).filter_by(title=item, cat_id= category.id).first()
	title = request.args.get('title')
	description = request.args.get('des')
	if title:
		item.title = title
	if description:
		item.description = description
	session.commit()
	return jsonify(item.serialize)

@app.route('/catalog/<string:cat>/<string:item>/delete', methods = ['DELETE'])
# delete the specified item
def deleteItem(cat, item):
	category = session.query(Category).filter_by(name=cat).first()
	item = session.query(Item).filter_by(title=item, cat_id= category.id).first()
	session.delete(item)
  	session.commit()
  	return "Item Deleted"

@app.route('/additem', methods = ['GET', 'POST'])
# add the specified item
def addItem():
	if request.method == 'GET':
	  	# render html template to add items
		print "go to html tempalte"
	elif request.method == 'POST':
		des = request.args.get('description','')
		title = request.args.get('title','')
		cat_id = request.args.get('cat_id','')
		print des
		print title
		print cat_id
		# item = session.query(Item).filter_by(title = title).first()
		# if item is not None:
		# 	print "existing item"
		# 	return jsonify({'message':'item already exists'})
		item = Item(description = des, title= title, cat_id = cat_id)
		session.add(item)
		session.commit()
		return jsonify({ 'id': item.id, 'description' : item.description,
		'title': item.title, 'cat ID': item.cat_id })
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
