from flask import Flask, render_template, request, session, url_for, redirect
import pymysql.cursors

app = Flask(__name__)

conn = pymysql.connect(host='localhost',
                       user='root',
                       password='root',
                       db='find_folk',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

#Default route that will redirect to main page
@app.route('/')
def toMain():
    return redirect('/main')

#Display all event in the next 3 days
#and see group's interest
@app.route('/main')
def main():
    cursor = conn.cursor()
    query = 'SELECT start_time, title FROM an_event WHERE (DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 1 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 2 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 3 DAY)) ORDER BY start_time'
    cursor.execute(query)
    data = cursor.fetchall()
    cursor.close()
    return render_template('main.html', events=data)

#Display user's homepage
@app.route('/home')
def home():
    #Redirect back to main page if not logged in
    if 'username' not in session:
        return redirect(url_for('main'))
    
    else:
        username = session['username']
        cursor = conn.cursor()
        #Display upcoming events for current user
        query = 'SELECT an_event.event_id, title, start_time, location_name, zipcode, group_name '\
                'FROM an_event '\
                    'JOIN sign_up ON sign_up.event_id = an_event.event_id '\
                'JOIN (organize JOIN a_group ON organize.group_id = a_group.group_id) ON organize.event_id = an_event.event_id '\
                'WHERE username = %s AND(DATE(start_time) = CURDATE() OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 1 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 2 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 3 DAY)) '\
                'ORDER BY start_time'
        cursor.execute(query, (username))
        data = cursor.fetchall()

        #Display current user's interests
        interest = 'SELECT category, keyword FROM interested_in WHERE username = %s'
        cursor.execute(interest, (username))
        interest_data = cursor.fetchall()
        
        cursor.close()
        return render_template('home.html', username=username, events=data, interests=interest_data)

#Display form for authorized user to create events
@app.route('/create')
def create():
    #Redirect back to main page if not logged in
    if 'username' not in session:
        return redirect(url_for('main'))
    
    else:
        username = session['username']
        cursor = conn.cursor()

        query = 'SELECT belongs_to.group_id, group_name FROM belongs_to JOIN a_group ON belongs_to.group_id = a_group.group_id WHERE authorized = 1 AND username = %s'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        
        return render_template('create.html', groups=data)

@app.route('/createAuth', methods=['GET', 'POST'])
def createAuth():
    if 'username' not in session:
        return redirect(url_for('main'))
    
    else:
        username = session['username']
        title = request.form['title']
        description = request.form['description']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        location_name = request.form['location_name']
        zipcode = request.form['zipcode']
        group_id = request.form['group_id']

        cursor = conn.cursor()

        check = 'SELECT * FROM an_event WHERE title = %s AND description = %s AND start_time = %s AND end_time = %s AND location_name = %s AND zipcode = %s'
        cursor.execute(check, (title, description, start_time, end_time, location_name, zipcode))
        data = cursor.fetchone()

        #Constraint: no 2 events with same name at same place at same time
        if(data):
            error = 'There is already an event created'
            cursor.close()
            return render_template('create.html', error = error)
        else:
            query = 'INSERT INTO an_event VALUES (NULL, %s, %s, %s, %s, %s, %s)'
            cursor.execute(query, (title, description, start_time, end_time, location_name, zipcode))
            conn.commit()
            
            ins = 'INSERT INTO organize VALUES((SELECT event_id FROM an_event WHERE title = %s AND description = %s AND start_time = %s AND end_time = %s AND location_name = %s AND zipcode = %s LIMIT 1), %s)'
            cursor.execute(ins, (title, description, start_time, end_time, location_name, zipcode, group_id))
            conn.commit()
            
            cursor.close()
            return redirect(url_for('home'))

#Let user search for event of interest and sign up for it
@app.route('/search')
def search():
    #Redirect back to main page if not logged in
    if 'username' not in session:
        return redirect(url_for('main'))
    
    else:            
        username = session['username']
        cursor = conn.cursor()

        query = 'SELECT an_event.event_id, title, start_time, location_name, zipcode, group_name '\
                'FROM about '\
                'JOIN (organize JOIN an_event ON organize.event_id = an_event.event_id) ON organize.group_id = about.group_id '\
                'JOIN interested_in ON about.category = interested_in.category AND about.keyword = interested_in.keyword '\
                'JOIN a_group ON about.group_id = a_group.group_id '\
                'WHERE username = %s AND (DATE(start_time) = CURDATE() OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 1 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 2 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 3 DAY)) '\
                'ORDER BY start_time'
        cursor.execute(query, (username))
        data = cursor.fetchall()
        
        cursor.close()
        return render_template('search.html', events=data)

#Sign up for event
@app.route('/signup', methods=['GET', 'POST'])
def signUp():
    #Redirect back to main page if not logged in
    if 'username' not in session:
        return redirect(url_for('main'))
    
    else:
        username = session['username']
        event_id = request.form['submit']
        
        cursor = conn.cursor()

        check = 'SELECT * FROM sign_up WHERE username = %s AND event_id = %s'
        cursor.execute(check, (username, event_id))

        data = cursor.fetchone()

        if(data):
            error = 'Already signed up'
            cursor.close()
            return render_template('search.html', error = error)
        else:
            query = 'INSERT INTO sign_up (event_id, username) VALUES (%s, %s)'
            cursor.execute(query, (event_id, username))
            conn.commit()
            cursor.close()
            return redirect(url_for('search'))

#Display login page
@app.route('/login')
def login():
    return render_template('login.html')

#Login Authentication
@app.route('/loginAuth', methods=['GET', 'POST'])
def loginAuth():
    username = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()

    query = 'SELECT * FROM member WHERE username = %s AND password = (SELECT MD5(%s))'
    cursor.execute(query, (username, password))

    data = cursor.fetchone()

    cursor.close()
    if(data):
        session['username'] = username
        return redirect(url_for('home'))
    else:
        error = 'Invalid login or username'
        return render_template('login.html', error=error)

#Display register page
@app.route('/register')
def register():
    return render_template('register.html')

#Register Authentication
@app.route('/registerAuth', methods=['GET', 'POST'])
def registerAuth():
    username = request.form['username']
    password = request.form['password']

    cursor = conn.cursor()

    query = 'SELECT * FROM users WHERE username = %s'
    cursor.execute(query, (username))

    data = cursor.fetchone()

    if(data):
        error = "This user already exists"
        cursor.close()
        return render_template('register.html', error = error)
    else:
        ins = 'INSERT INTO users VALUES(%s, (SELECT MD5(%s)))'
        cursor.execute(ins, (username, password))

        conn.commit()
        cursor.close()
        return render_template('index.html')
    

@app.route('/post', methods=['GET', 'POST'])
def post():
    username = session['username']
    cursor = conn.cursor();
    blog = request.form['blog']
    query = 'INSERT INTO blog (blog_post, username) VALUES(%s, %s)'
    cursor.execute(query, (blog, username))
    conn.commit()
    cursor.close()
    return redirect(url_for('home'))

#Logout Authetication
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
