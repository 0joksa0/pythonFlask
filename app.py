from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename
import os
from flask_mysqldb import MySQL

app = Flask(__name__)


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'root'
app.config['MYSQL_DB'] = 'flaskapp'
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['UPLOAD_FOLDER'] = '/home/aleksandar/python/webServerSimple/static/uploads'
mysql = MySQL(app)



def init_db():
    cur = mysql.connection.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS users(id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(100), password VARCHAR(100), photo VARCHAR(100) )')
    cur.execute('CREATE TABLE IF NOT EXISTS posts(id INT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(100), content TEXT, author_id INT, FOREIGN KEY (author_id) REFERENCES users(id) )')
    cur.execute('CREATE TABLE IF NOT EXISTS friends(id INT AUTO_INCREMENT PRIMARY KEY, user_id INT, friend_id INT, FOREIGN KEY (user_id) REFERENCES users(id), FOREIGN KEY (friend_id) REFERENCES users(id) )')
    mysql.connection.commit()
    cur.close()

def get_all_posts():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM friends f JOIN posts p ON author_id = friend_id JOIN users u ON p.author_id = u.id WHERE f.user_id = (%s) ', (session['user'][0],))
    posts = cur.fetchall()
    cur.close()
    return posts

def get_all_posts_my():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM posts p JOIN users u ON p.author_id = u.id WHERE u.id = (%s)', (session['user'][0],))
    posts = cur.fetchall()
    cur.close()
    return posts

@app.route('/')
def home():
    init_db()
    if 'user' in session:
        posts = get_all_posts();

        return render_template('home.html', user=session['user'], posts=posts)
    else:
        return redirect('/logIn')

@app.route('/settings')
def settings():
    if 'user' in session:
        return render_template('settings.html', user=session['user'])
    else:
        return redirect('/logIn')

@app.route('/profile')
def profile():
    if 'user' in session:
        posts = get_all_posts_my()
        print(session['user'])
        return render_template('profile.html', user=session['user'], posts=posts)
    else:
        return redirect('/logIn')

@app.route('/createPost', methods=['POST'])
def createPost():
    if 'user' in session:
        user = session['user']
        title = request.form['title']
        content = request.form['content']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO posts(title, content, author_id) VALUES(%s, %s, %s)", (title, content, user[0]))
        mysql.connection.commit()
        cur.close()
        return redirect('/')
    else:
        return redirect('/logIn')

@app.route('/users' , methods=['GET'])
def users():
    if 'user' in session:
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users u left join friends f on u.id = f.friend_id WHERE u.id != (%s) AND (f.user_id != (%s) OR f.user_id is null )",(session['user'][0],session['user'][0],))
        users = cur.fetchall()
        cur.close()
        return render_template('users.html', user= session['user'],users=users)
    else:
        return redirect('/logIn')

@app.route('/friends', methods=['GET'])
def friends():
    if 'user' in session:
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM friends f JOIN users u ON f.friend_id = u.id WHERE f.user_id = (%s)', (session['user'][0], ) )
        friendsDb = cur.fetchall()
        cur.close()
        return render_template("friends.html", user = session['user'], friends = friendsDb )
    else:
        return redirect('/logIn')

@app.route('/addFriend', methods=['POST'])
def addFriend():
    if 'user' in session:
        user = session['user']
        friend_id = request.form['friend_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO friends(user_id, friend_id) VALUES(%s, %s)", (user[0], friend_id))
        mysql.connection.commit()
        cur.close()
        return redirect('/users')
    else:
        return redirect('/logIn')

@app.route('/removeFriend', methods = ['POST'])
def removeFriend():
    if 'user' in session:
        friend_id = request.form['friend_id']
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM friends f WHERE f.friend_id = (%s) AND f.user_id = (%s)', (friend_id , session['user'][0], ) )
        cur.execute('DELETE FROM friends f WHERE f.friend_id = (%s) AND f.user_id = (%s)', (session['user'][0], friend_id, ) )
        mysql.connection.commit()
        cur.close()
        return redirect('/friends')
    else:
        return redirect('/logIn')
    
@app.route('/photo', methods=['POST', 'GET'])
def photo():
    if 'user' in session:
        if request.method == 'POST':
            user = session['user']
            file = request.files['photo']
            if file.filename == '':
                return redirect('/profile')
            filename = secure_filename(file.filename)
            os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], str(user[0])), exist_ok=True)
            if user[4]:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], str(user[0]), user[4]))
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], str(user[0]), filename))
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET photo = %s WHERE id = %s", (filename, user[0]))
            session['user'] = (user[0], user[1], user[2], user[3], filename)

            mysql.connection.commit()
            cur.close()
            return redirect('/profile')
    else:
        return redirect('/logIn')

@app.route('/logIn', methods=['GET'])
def logIn():
    return render_template('logIn.html')

@app.route('/logIn', methods=['POST'])
def logInPost():
    email = request.form['email']
    password = request.form['password']
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE email = %s AND password = %s", (email, password))
    user = cur.fetchone()
    cur.close()
    if user:
        session['user'] = user
        return redirect('/')
    else:
        return render_template('logIn.html', error='Invalid email or password')
    
@app.route('/signUp', methods=['GET'])
def signUp():
    return render_template('signUp.html')

@app.route('/signUp', methods=['POST'])
def signUpPost():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO users(name, email, password) VALUES(%s, %s, %s)", (name, email, password))
    mysql.connection.commit()
    cur.close()
    return redirect('/logIn')

@app.route('/changePassword', methods=['POST'])
def changePassword():
    if 'user' in session:
        user = session['user']
        email = user[2]
        oldPassword = request.form['oldPassw']
        password = request.form['newPassw']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password = %s WHERE email = %s AND password = %s", (password, email, oldPassword))
        
        if cur.rowcount == 0:
            return render_template('profile.html', user=session['user'], error='Invalid old password')
        
        mysql.connection.commit()
        cur.close()
        
        return redirect('/')
    else:
        return redirect('/logIn')

@app.route('/logOut', methods=['POST'])
def logOut():
    session.pop('user', None)
    return redirect('/logIn')



if __name__ == '__main__':
    app.run(debug=True)
    app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico') )
    app.add_url_rule('/uploads/<path:filename>', endpoint='uploads', view_func=app.send_static_file)