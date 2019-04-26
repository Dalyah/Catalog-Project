from models import Base, User, Category, Item
from flask import Flask, jsonify, request, url_for, abort, g, render_template, session, redirect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth
import random
import string

auth = HTTPBasicAuth()


engine = create_engine('sqlite:///catalog.db',
                        connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()
app = Flask(__name__)


@auth.verify_password
def verify_password(username, password):
	print "Looking for user %s" % username
	user = db_session.query(User).filter_by(username = username).first()
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

	user = db_session.query(User).filter_by(username=username).first()
	if user is not None:
		print "existing user"
		return jsonify({'message':'user already exists'}), 200

	user = User(username = username)
	user.hash_password(password)
	db_session.add(user)
	db_session.commit()
	return jsonify({ 'username': user.username }), 201

@app.route('/users/<int:id>')
def get_user(id):
	user = db_session.query(User).filter_by(id=id).one()
	if not user:
		abort(400)
	return jsonify({'username': user.username})

# Get Requests
@app.route('/')
@app.route('/catalog')
# return all the categories and latest added items for each category
def get_all_category_latestItem():
	categories = db_session.query(Category).all()
	items = db_session.query(Item).order_by(Item.id.desc())
	return render_template('catalog.html', categories=categories, items=items )

@app.route('/catalog/<int:cat>/items')
# returns the items of the specified category
def showAllItems(cat):
	items = db_session.query(Item).filter_by(cat_id=cat)
	cat = db_session.query(Category).filter_by(id=cat).first()
	return render_template('items.html', items=items , cat= cat.name)

@app.route('/catalog/<int:cat>/<int:item>')
# returns des of specified item
def showItemDes(item, cat):
	item = db_session.query(Item).filter_by(id=item, cat_id= cat).first()
	return render_template('item.html', item =item)

@app.route('/catalog.json')
# returns all categories in catalog
def showJSON():
	categories = db_session.query(Category).all()

	# for cat in categories:
	# 	items = db_session.query(Item).filter_by( cat_id= cat.id)
	# 	items_cat = []
	# 	for item in items:
	# 		items_cat.append(item.serialize)
	# 	cat.append(items_cat)

	return jsonify(categories = [category.serialize for category in categories])

# PUT, DELETE, POST Requests
@app.route('/catalog/<int:cat>/<int:item>/edit', methods = ['POST', 'GET'])
@auth.login_required
# edits the specified item
def editItem(cat, item):
	if 'logged_in' in session:
		category = db_session.query(Category).filter_by(id=cat).first()
		categories = db_session.query(Category).all()
		item = db_session.query(Item).filter_by(id=item, cat_id= cat).first()

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
			db_session.commit()
			# return "item updated"
			return redirect(url_for('showItemDes', item = item.id,
			                        cat = item.cat_id))
	else:
		return redirect(url_for('login'))


@app.route('/catalog/<int:cat>/<int:item>/delete', methods = ['GET', 'DELETE', 'POST'])
@auth.login_required
# delete the specified item
def deleteItem(cat, item):
	if 'logged_in' in session:
		category = db_session.query(Category).filter_by(id=cat).first()
		currentItem = db_session.query(Item).filter_by(id=item, cat_id= cat).first()
		if request.method == 'GET':
			return render_template('deleteItem.html', item= currentItem)
		else:
			db_session.delete(currentItem)
		  	db_session.commit()
		  	print "Item Deleted"
			return redirect(url_for('get_all_category_latestItem'))
	else:
		return redirect(url_for('login'))


@app.route('/addItem', methods = ['GET', 'POST'])
@auth.login_required
# add the specified item
def addItem():
	if 'logged_in' in session:
		categories = db_session.query(Category).all()
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
			db_session.add(item)
			db_session.commit()
			print "item added"
			return redirect(url_for('get_all_category_latestItem'))
	else:
		return redirect(url_for('login'))

@app.route('/addcat', methods= ['GET'])
@auth.login_required
# add category
def addCategory():
	if 'logged_in' in session:
		id = request.json.get('id')
		name = request.json.get('name')
		cat = db_session.query(Category).filter_by(id = id).first()
		if cat is not None:
			print "existing category"
			return jsonify({'message':'category already exists'}), 200
		cat = Category(id = id, name = name)
		db_session.add(cat)
		db_session.commit()
		return jsonify({ 'id': cat.id, 'name' : cat.name }), 201
	else:
		return redirect(url_for('login'))

@app.route('/login', methods = ['POST', 'GET'])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	else:
		username = request.form['username']
		password = request.form['password']
		if verify_password(username, password):
			session['logged_in'] = True
			print "Successful Login"
			return redirect(url_for('get_all_category_latestItem'))
		else:
			print "Sorry Wrong Credintials"
			return redirect(url_for('login'))
@app.route('/logout', methods = ['GET'])
def logout():
	if 'logged_in' in session:
		del session['logged_in']
		# session['logged_in'] = False
		print "logout suceessfully"
		return redirect(url_for('get_all_category_latestItem'))


if __name__ == '__main__':
	app.debug = True
	app.config['SECRET_KEY'] = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	app.run(host='0.0.0.0', port=5000)
