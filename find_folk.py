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
    username = session['username']
    cursor = conn.cursor()
    query = 'SELECT an_event.event_id, title, start_time, location_name, zipcode, group_name '\
            'FROM an_event '\
            'JOIN sign_up ON sign_up.event_id = an_event.event_id '\
            'JOIN (organize JOIN a_group ON organize.group_id = a_group.group_id) ON organize.event_id = an_event.event_id '\
            'WHERE username = %s AND(DATE(start_time) = CURDATE() OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 1 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 2 DAY) OR DATE(start_time) = DATE_ADD(CURDATE(), INTERVAL 3 DAY)) '\
            'ORDER BY start_time'
    cursor.execute(query, (username))
    data = cursor.fetchall()
    cursor.close()
    return render_template('home.html', username=username, events=data)

@app.route('/login')
def login():
    return render_template('login.html')

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

@app.route('/register')
def register():
    return render_template('register.html')

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

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')

app.secret_key = 'some key that you will never guess'

if __name__ == "__main__":
    app.run('127.0.0.1', 5000, debug = True)
