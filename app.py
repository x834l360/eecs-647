import pymysql
from flask import Flask, request, jsonify, render_template, session, redirect


DB_HOST = 'mysql.eecs.ku.edu'
DB_USER = 'x8341340'
DB_PASSWORD = 'ien9eWei'
DB_DB = 'x8341340'

db = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DB)

app = Flask(__name__)
app.config["SECRET_KEY"] = "........"
app.secret_key = '........'
app.session_cookie_name = "f.session.id"


def list_posts():
    cursor = db.cursor()
    cursor.execute(""" select post.*, count(*) as comment_count
    from post
        left join comment on comment.post_id = post.id
    group by post.id
    """)
    return [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]


def find_users_post_something():
    cursor = db.cursor()
    cursor.execute("""select user.username, count(post.id) as cnt
        from user left join post on user.id = post.user_id
        group by user.username
        having cnt > 0
        order by cnt desc 
    """)
    return [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]


def list_comments(post_id: int):
    cursor = db.cursor()
    cursor.execute("""
        select * from comment where post_id = %s
    """, (post_id,))
    return [dict(zip(cursor.description, row)) for row in cursor.fetchall()]


def retrieve_post(pid):
    cursor = db.cursor()
    cursor.execute(""" select * from post where id = %s """, (pid,))
    post = dict(zip([x[0] for x in cursor.description], cursor.fetchone()))

    cursor.execute(""" select * from comment where post_id = %s""", (pid))
    comments = [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]
    post['comments'] = comments
    return post


def comment_post(pid, user, comment):
    cursor = db.cursor()
    cursor.execute("""
        insert into comment(post_id, comment, author, user_id) values (%s, %s, %s, %s)
    """, (pid, comment, user['username'], user['id']))
    db.commit()


def list_posts_of_user(userid):
    cursor = db.cursor()
    cursor.execute("""
        select * from post where user_id = %s
    """, (userid,))
    return [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]


def list_topics():
    cursor = db.cursor()
    cursor.execute(""" select * from category; """)
    return [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]


def retrieve_topic(topic):
    cursor = db.cursor()
    cursor.execute(""" select * from post where category_topic = %s """, (topic,))
    posts = [dict(zip([x[0] for x in cursor.description], row)) for row in cursor.fetchall()]
    return posts


@app.context_processor
def login_user():
    return {
        "is_authenticated": session.get("user") is not None,
        "user": session.get("user"),
    }


@app.route('/')
def index_view():
    posts = list_posts()
    return render_template("index.html", posts=posts)


@app.route('/my')
def my_posts():
    user = session.get("user")
    posts = list_posts_of_user(user['id'])
    return render_template("index.html", posts=posts)


@app.route("/topics/<topic>")
def retrieve_topics_view(topic):
    posts = retrieve_topic(topic)
    return render_template("index.html", posts=posts)


@app.route("/topics")
def topics_view():
    topics = list_topics()
    return render_template("topics.html", topics=topics)


@app.route('/user')
def users():
    user = find_users_post_something()
    return render_template("users.html", users=user)


@app.route('/users/<id>')
def user_posts(id):
    posts = list_posts_of_user(id)
    return render_template("index.html", posts=posts)


@app.route("/posts/<id>", methods=["GET", "POST"])
def post_view(id):
    if request.method == "GET":
        post = retrieve_post(id)
        return render_template("post.html", post=post)

    user = session.get("user")
    comment_post(id, user, request.form.get("comment"))
    return redirect("/posts/" + id)


@app.route("/login", methods=["GET", "POST"])
def login_view():
    if request.method == "GET":
        return render_template("login.html")

    form = request.form.to_dict()
    cursor = db.cursor()
    cursor.execute("select * from user where username = %s", (form['username'],))
    row = cursor.fetchone()
    if row:
        user = dict(zip([x[0] for x in cursor.description], row))
        print(user)
        if user['password'] != form['password']:
            return render_template("login.html", error="Password not match")
        session['user'] = user
    else:
        print("NOTFOUND")
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register_view():
    if request.method == "GET":
        return render_template("register.html")

    user = request.form.to_dict()
    cursor = db.cursor()
    cursor.execute("select * from user where username = %s", (user['username'],))
    if cursor.fetchone():
        ctx = {"status": "error", "message": f"user with name {user['username']} already exists."}
        return render_template("register.html", **ctx)

    cursor.execute("""insert into user(username, password, email, phone, is_admin)
                   values(%s, %s, %s, %s, %s)
                   """, (user['username'], user['password'], user['email'], user['phone'], 0))
    print(cursor.rowcount)
    db.commit()
    ctx = {"status": "ok", "message": f"register success."}
    return render_template("registered.html", **ctx)


@app.route("/api/register")
def register():
    user = request.json
    cursor = db.cursor()
    cursor.execute("select count(1) from user where username = %s", (user['username'],))
    if cursor.rowcount > 0:
        return jsonify({"status": "error", "message": f"user with name {user['username']} already exists."})

    cursor.execute("""insert into user(username, password, email, phone, is_admin)
                   values(%(username)s, %(password)s, %(email)s, %(phone)s, %(is_admin)s)
                   """, user)
    print(cursor.rowcount)
    return jsonify({"status": "ok", "id": cursor.lastrowid})


@app.route("/new", methods=["GET", "POST"])
def create_post():
    user = session.get("user")
    if not user:
        return redirect("/login")

    if request.method == "GET":
        return render_template("new-post.html")

    form = request.form.to_dict()
    category = form['category']
    cursor = db.cursor()

    cursor.execute("select * from category where topic = %s", (category,))
    if not cursor.fetchone():
        cursor.execute("insert into category(topic) values(%s)", (category,))
        db.commit()

    cursor.execute("""
        insert into post(title, category_topic, content, author, user_id)
        values (%s, %s, %s, %s, %s)
    """, (form['title'], category, form['content'], user['username'], user['id']))
    db.commit()
    return redirect("/")


if __name__ == '__main__':
    app.run(debug=True)
