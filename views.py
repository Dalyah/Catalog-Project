from models import Base, User, Category, Item
from flask import Flask, jsonify, request, url_for, abort, g
from flask import render_template, session, flash, redirect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy import create_engine
from flask_httpauth import HTTPBasicAuth

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import random
import string
import json
import httplib2
import requests

from flask import session as session
auth = HTTPBasicAuth()


engine = create_engine('sqlite:///catalog.db',
                       connect_args={'check_same_thread': False})

Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
db_session = DBSession()
app = Flask(__name__)
CLIENT_ID = json.loads(open(
                 'client_secrets.json', 'r').read())['web']['client_id']


@auth.verify_password
def verify_password(username, password):
    print "Looking for user %s" % username
    user = db_session.query(User).filter_by(username=username).first()
    if not user:
        print "User not found"
        return False
    elif not user.verify_password(password):
        print "Unable to verify password"
        return False
    else:
        g.user = user
        return True


@app.route('/users', methods=['POST'])
def new_user():
    username = request.args.get('username')
    password = request.args.get('password')
    if username is None or password is None:
        print "missing arguments"
        abort(400)

    user = db_session.query(User).filter_by(username=username).first()
    if user is not None:
        print "existing user"
        return jsonify({'message': 'user already exists'}), 200

    user = User(username=username)
    user.hash_password(password)
    db_session.add(user)
    db_session.commit()
    return jsonify({'username': user.username}), 201


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
    return render_template('catalog.html', categories=categories, items=items)


@app.route('/catalog/<int:cat>/items')
# returns the items of the specified category
def showAllItems(cat):
    items = db_session.query(Item).filter_by(cat_id=cat)
    cat = db_session.query(Category).filter_by(id=cat).first()
    return render_template('items.html', items=items, cat=cat.name)


@app.route('/catalog/<int:cat>/<int:item>')
# returns des of specified item
def showItemDes(item, cat):
    item = db_session.query(Item).filter_by(id=item, cat_id=cat).first()
    return render_template('item.html', item=item)


@app.route('/catalog.json')
# returns all categories in catalog
def showJSON():
    categories = db_session.query(Category).all()
    return jsonify(categories=[category.serialize for category in categories])


# PUT, DELETE, POST Requests
@app.route('/catalog/<int:cat>/<int:item>/edit', methods=['POST', 'GET'])
@auth.login_required
# edits the specified item
def editItem(cat, item):
    if 'logged_in' in session:
        category = db_session.query(Category).filter_by(id=cat).first()
        categories = db_session.query(Category).all()
        item = db_session.query(Item).filter_by(id=item, cat_id=cat).first()

        if request.method == 'GET':
            return render_template('editItem.html', categories=categories,
                                   item=item)
        else:
            if request.form['itemTitle']:
                item.title = request.form['itemTitle']
            if request.form['itemDes']:
                item.description = request.form['itemDes']
            if request.form['category']:
                item.cat_id = request.form['category']
            db_session.commit()
            # return "item updated"
            return redirect(url_for('showItemDes', item=item.id,
                                    cat=item.cat_id))
    else:
        return redirect(url_for('login'))


@app.route('/catalog/<int:cat>/<int:item>/delete', methods=['GET', 'POST'])
@auth.login_required
# delete the specified item
def deleteItem(cat, item):
    if 'logged_in' in session:
        category = db_session.query(Category).filter_by(id=cat).first()
        currentItem = db_session.query(Item).filter_by(id=item,
        cat_id=cat).first()
        if request.method == 'GET':
            return render_template('deleteItem.html', item=currentItem)
        else:
            db_session.delete(currentItem)
            db_session.commit()
            print "Item Deleted"
            return redirect(url_for('get_all_category_latestItem'))
    else:
        return redirect(url_for('login'))


@app.route('/addItem', methods=['GET', 'POST'])
@auth.login_required
# add the specified item
def addItem():
    if 'logged_in' in session:
        categories = db_session.query(Category).all()
        if request.method == 'GET':
            return render_template('addItem.html', categories=categories)
        else:
            if request.form['itemTitle']:
                title = request.form['itemTitle']
            if request.form['itemDes']:
                description = request.form['itemDes']
            if request.form['category']:
                cat_id = request.form['category']
            item = Item(description=description, title=title, cat_id=cat_id)
            db_session.add(item)
            db_session.commit()
            print "item added"
            return redirect(url_for('get_all_category_latestItem'))
    else:
        return redirect(url_for('login'))


@app.route('/addcat', methods=['GET'])
@auth.login_required
# add category
def addCategory():
    if 'logged_in' in session:
        id = request.json.get('id')
        name = request.json.get('name')
        cat = db_session.query(Category).filter_by(id=id).first()
        if cat is not None:
            print "existing category"
            return jsonify({'message': 'category already exists'}), 200
        cat = Category(id=id, name=name)
        db_session.add(cat)
        db_session.commit()
        return jsonify({'id': cat.id, 'name': cat.name}), 201
    else:
        return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    state = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for x in range(32))
    session['state'] = state
    if request.method == 'GET':
        # return "The current session state is %s" % session['state']
        return render_template('login.html', STATE=state)
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


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = session.get('access_token')
    stored_gplus_id = session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps(
                                'Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    session['access_token'] = credentials.access_token
    session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    session['username'] = data['name']
    session['picture'] = data['picture']
    session['email'] = data['email']
    session['logged_in'] = True
    print "successful login with google"
    return "successful login with google"


@app.route('/logout', methods=['GET'])
def logout():
    if 'logged_in' in session:
        del session['logged_in']
        print "logout suceessfully"
        return redirect(url_for('get_all_category_latestItem'))


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = session.get('access_token')

    if access_token is None:
        response = make_response(json.dumps(
                                    'Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
                                 json.dumps('Fail to revoke token'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


if __name__ == '__main__':
    app.debug = True
    app.config['SECRET_KEY'] = ''.join(random.choice(
                                string.ascii_uppercase + string.digits)
                                for x in range(32))
    app.run(host='0.0.0.0', port=5000)
