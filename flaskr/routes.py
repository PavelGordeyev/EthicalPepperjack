from flaskr import app, db_connect
from flask import render_template, request, redirect, jsonify, url_for, flash, session
from .forms import LoginForm, SignUpForm
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from .db_connect import execute_query
from werkzeug.security import generate_password_hash, check_password_hash

login_manager = LoginManager()
login_manager.init_app(app)

# User Model for Flash-Login
class User(UserMixin):
    # Constructor for User Model
    def __init__(self, username, id, active=True):
        self.username = username
        self.id = id
        self.active = active
    # Returns true because users are always active
    def is_active(self):
        return True
    # Returns false because users are always not anonymous
    def is_anonymous(self):
        return False
    def is_authenticated(self):
        return True
    def get_id(self):
        return self.id
    @login_manager.user_loader
    def load_user(id):
        user_id = int(id)
        query = """SELECT id, username FROM users WHERE id = %d;""" %(user_id)
        dbuser = list(execute_query(query))
        print(dbuser)
        if(dbuser):
            user_obj = User(username=dbuser[0][1], id=dbuser[0][0])
            print(type(user_obj))
            return user_obj
        else:
            return None

# Route to the login page
@app.route('/', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = execute_query("""SELECT id, username, password FROM users WHERE username = \'%s\';""" %(form.username.data))
        user_list = list(user)
        if user_list:
            if(check_password_hash(user_list[0][2], form.password.data)):
                user_obj = User(username=user_list[0][1], id=user_list[0][0])
                login_user(user_obj)
                return redirect('/profile')
            else:
                flash("Password is incorrect")
        else:
            flash("Account is not found")
    return render_template('login.html', form=form)


# Route to the signup page
@app.route('/signup', methods=('GET', 'POST'))
def signup():
    form = SignUpForm()
    if form.validate_on_submit():
        user = execute_query("""SELECT id, username, password FROM users WHERE username = \'%s\';""" %(form.username.data))
        if(user):
            flash("There is already an account with that name.")
        else:
            query = """INSERT INTO users (username, f_name, l_name, email, password) VALUES (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\')""" % (form.username.data, form.f_name.data,
            form.l_name.data, form.email.data, generate_password_hash(form.password.data))
            try:
                insert = execute_query(query)
                return_id = list(execute_query("""SELECT id FROM users WHERE username = \'%s\';""" %(form.username.data)))
                user_obj = User(username=form.username.data, id=return_id[0][0])
                login_user(user_obj)
                flash("You have successfully signed up!")
                return redirect('/profile')
                #alert successful
            except:
                #alert not successful
                flash("The username or email has already been used!")
    return render_template('signup.html', form=form)




@app.route('/profile')
@login_required
def profile():
    user_id = current_user.get_id()
    try:
        user = list(execute_query("""SELECT username, f_name, l_name, email FROM users WHERE id = %d;""" %(user_id)))
        return render_template('profile.html', profile=user[0])
    except:
        flash("Error")
        return render_template('404.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Account has been logged out")
    return redirect('/login')

# Route for guest
@app.route('/guest')
def guest():
    return render_template('search_category.html')


@app.route('/search_category', methods=['GET', 'POST'])
def search_category():
    if request.method == 'GET':
        return render_template('search_category.html')

    elif request.method == 'POST':
        user_data = request.form
        ethical_category = user_data['search_category']

        query_categories = """SELECT * FROM ethical_categories WHERE name =
        \'%s\';""" %(ethical_category)

        data = execute_query(query_categories)

        query_ingredients = """ SELECT ingredients.name
                                FROM ingredients
                                INNER JOIN(
                                    SELECT ia.alt_ingredient_id
                                    FROM ingredient_alts ia
                                    WHERE ia.ingredient_id = (
                                        SELECT ingredients.id FROM ingredients
                                        INNER JOIN ingredients_concerns ON ingredients.id = ingredients_concerns.ingredient_id
                                        INNER JOIN ethical_concerns ec on ingredients_concerns.concern_id = ec.id
                                        INNER JOIN ethical_categories e on ec.category_id = e.id
                                        WHERE e.id = %d )) alts
                                ON ingredients.id = alts.alt_ingredient_id; """ %(data[0][0])

        data2 = execute_query(query_ingredients)
        return render_template('search_category.html', name=ethical_category,
                               ingredients=data2)


# This will be all of the routes for the recipe book function. There will be a
# Get to get the current users recipe
# book. Delete will remove a recipe.

@app.route('/recipe_book')
def recipebook():
    return render_template('recipe_book/user.html')

# Route to handle the display of ingredients after searching for a recipe.
# Recipe name is the input and will return list of all ingredients
@app.route('/recipe_display')
def recipe_display():
#   Get the recipe name  from the search bar
    recipe_name = request.args.get("recipe_name")

    # Use session cookie if name not in the url
    if recipe_name == None:
        recipe_name = session['recipe_name']

#    print(recipe_name)
#    recipe_name = "tomato soup"
#   Find the associated recipe ID with the recipe name
    id_query = "SELECT id FROM recipes WHERE name =\'%s\';" %(recipe_name)
    result = execute_query(id_query)
    print(type(result))
    #   Convert result tuple to integer
    recipe_id = result[0][0]

    session['recipe_id'] = recipe_id
    session['recipe_name'] = recipe_name

    query = "SELECT i.id, i.name, i.description, i.origin FROM ingredients AS i\
    INNER JOIN recipes_ingredients ON i.id = recipes_ingredients.ingredient_id\
    WHERE recipes_ingredients.recipe_id = %d;" %(recipe_id)
    #   Convert result tuple to list and then just get the first element of the tuple
    ingredient_list = list(execute_query(query))
    #   ingredient_list =[item for t in result for item in t]
    #   Pass the search query and the list of ingredients to the new html for display.
    return render_template('recipe_display.html', name=recipe_name,recipeID=recipe_id, ingredients=ingredient_list)


@app.route('/search_recipe', methods=['GET', 'POST'])
def search_recipe():
    if request.method == 'GET':
        return render_template('search_recipe.html')

    elif request.method == 'POST':
        user_data = request.form
        recipe_name = user_data['search_recipe_name']

        query = """SELECT name,id FROM recipes WHERE name =
        \'%s\';""" %(recipe_name)

        recipes = list(execute_query(query))


        if(recipes):
            return render_template('search_recipe.html', names=recipes)
        else:
            error_message=[("No recipes found, please try again",)]
            return render_template('search_recipe.html', names=error_message)


@app.route('/user_recipebook')
def user_recipebook():
    username = "KC"
    recipe_list = ['tomato soup', 'tuna sandwich', 'mashed potatoes']

    return render_template('recipe_book/user.html', name=username, recipes=recipe_list)

@app.route('/alternatives', methods=['GET','POST'])
def alternatives():

    if request.method == 'GET': # Show alternatives

        session['recipe_id_alt'] = int(request.args.get('recipeID'))
        session['ingredient_id_alt'] = int(request.args.get('ingredientID'))
        session['recipe_name'] = request.args.get('recipe_name')

        query_name = """ SELECT name, description
                         FROM ingredients
                         WHERE id = %d """ %(session['ingredient_id_alt'])

        ingredient = list(execute_query(query_name))[0]

        query_ingredients = """ SELECT ingredients.id,
                                       ingredients.name,
                                       ingredients.description
                                FROM ingredients
                                INNER JOIN(
                                    SELECT ia.alt_ingredient_id
                                    FROM ingredient_alts ia
                                    WHERE ia.ingredient_id = %d) alts
                                ON ingredients.id = alts.alt_ingredient_id """ %(session['ingredient_id_alt'])

        alternative_list = list(execute_query(query_ingredients))

        unethical_reason = "water intensive to produce and high in greenhouse gas emissions."

        return render_template('alternative_display.html', ingredient=ingredient, unethical=unethical_reason, alternatives = alternative_list)

    else: # POST request to switch ingredient

        recipe_id = session['recipe_id_alt']

        ingredient_id = session['ingredient_id_alt']

        new_ingredient_id = int(request.form['ingredient_id'])

        query_recipe_ing = """UPDATE recipes_ingredients
                              SET ingredient_id = %d
                              WHERE recipe_id = %d
                              AND ingredient_id = %d; """ %(new_ingredient_id,recipe_id,ingredient_id)

        update = execute_query(query_recipe_ing)

        return redirect(url_for('recipe_display'))

@app.route('/add_ingredients', methods=['GET','POST'])
def add_ingredients():

	if request.method == "GET":

		if request.args.get('ingredient_name'):

			query = """SELECT i.id,
					i.name,
					i.description,
					rankings.ranking
					FROM ingredients i
					LEFT JOIN ingredients_concerns ic ON i.id = ic.ingredient_id
					LEFT JOIN ethical_concerns ec ON ic.concern_id = ec.id
					LEFT JOIN rankings ON ec.ranking_id = rankings.id
					WHERE i.name LIKE (\'%%%s%%\');""" %(request.args.get('ingredient_name'))

			ingredients = list(execute_query(query))

		else:

			ingredients = []


		return render_template('add_ingredient.html',ingredients=ingredients)

	if request.method == 'POST':

		recipe_id = int(session['recipe_id'])
		ingredient_id = int(request.form['submit_ing_id'])
		quantity = int(request.form['quantity'])
		unit = request.form['unit']

		query = """INSERT INTO recipes_ingredients
					(recipe_id, ingredient_id, quantity, unit)
					VALUES (%d,%d,%d,\'%s\');""" %(recipe_id, ingredient_id, quantity, unit)

		execute_query(query)

		return redirect(url_for('recipe_display'))


@app.errorhandler(404)
def pageNotFound(error):
	return render_template('404.html', title='Page Not Found')

@app.errorhandler(500)
def majorError(error):
	return render_template('500.html', title='Major Error')
