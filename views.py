from models import Base, User, Category, Item
from flask import Flask, jsonify, request, url_for, abort, g, render_template, redirect
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
@app.route('/catalog')
# return all the categories and latest added items for each category
def get_all_category_latestItem():
	categories = session.query(Category).all()
	items = session.query(Item).order_by(Item.id.desc())
	return render_template('catalog.html', categories=categories, items=items )

@app.route('/catalog/<int:cat>/items')
# returns the items of the specified category
def showAllItems(cat):
	items = session.query(Item).filter_by(cat_id=cat)
	cat = session.query(Category).filter_by(id=cat).first()
	# return jsonify(items = [item.serialize for item in items])
	return render_template('items.html', items=items , cat= cat.name)

@app.route('/catalog/<int:cat>/<string:item>')
# returns des of specified item
def showItemDes(item, cat):
	item = session.query(Item).filter_by(title=item, cat_id= cat).first()
	item_des = item.description
	return render_template('item.html', item =item)

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
@app.route('/catalog/<int:cat>/<int:item>/edit', methods = ['POST', 'GET'])
# edits the specified item
def editItem(cat, item):
	category = session.query(Category).filter_by(id=cat).first()
	categories = session.query(Category).all()
	item = session.query(Item).filter_by(id=item, cat_id= cat).first()
	# title = request.args.get('title')
	# description = request.args.get('des')

	if request.method == 'GET':
		 return render_template('editItem.html', categories = categories,
		                         item = item)
	else:
		if request.form['itemTitle']:
			 item.title = request.form['itemTitle']
		if request.form['itemDes']:
			 item.description = request.form['itemDes']
		if request.form['category']:
			 item.cat_id = request.form['category']
		session.commit()
		# return "item updated"
		return redirect(url_for('showItemDes', item = item.id,
		                        cat = item.cat_id))

@app.route('/catalog/<int:cat>/<int:item>/delete', methods = ['GET', 'DELETE'])
# delete the specified item
def deleteItem(cat, item):
	category = session.query(Category).filter_by(id=cat).first()
	currentItem = session.query(Item).filter_by(id=item, cat_id= cat).first()
	if request.method == 'GET':
		return render_template('deleteItem.html')
	else:
		session.delete(currentItem)
	  	session.commit()
	  	return "Item Deleted"

@app.route('/addItem', methods = ['GET', 'POST'])
# add the specified item
def addItem():
	categories = session.query(Category).all()
	if request.method == 'GET':
		 return render_template('addItem.html', categories = categories)
	else:
		if request.form['itemTitle']:
			 title = request.form['itemTitle']
		if request.form['itemDes']:
			 description = request.form['itemDes']
		if request.form['category']:
			 cat_id = request.form['category']
		item = Item(description = description, title= title, cat_id = cat_id)
		session.add(item)
		session.commit()
		return "item added"
		# return redirect(url_for('showItemDes', item = item.id,
		#                         cat = item.cat_id))

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
