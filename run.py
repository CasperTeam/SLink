from flask import Flask, render_template, request, redirect, flash, Response, abort
from flask_sqlalchemy import SQLAlchemy
import datetime
import json
import re
import random
import string

ip_list_block    = []
user_agent_block = ""
banned_path      = ['about']

app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates'
)
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
#sess.init_app(app)
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///short_link.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=True

db = SQLAlchemy(app)
class Short_link(db.Model):
   id = db.Column('id', db.Integer, primary_key = True)
   url_path = db.Column(db.String(200), unique=True)
   url = db.Column(db.String(500))
   date = db.Column(db.String(30))
   viewers_count = db.Column('viewers_count', db.Integer)

   def __init__(self, url_path, url, date, viewers_count):
      self.url_path = url_path
      self.url = url
      self.date = date
      self.viewers_count = viewers_count

@app.before_request
def limit_remote_addr():
    myUserAgent = request.headers.get('User-Agent')
    if request.remote_addr in ip_list_block:
        abort(403)  # Forbidden
    elif user_agent_block and user_agent_block in myUserAgent:
        abort(403)  # Forbidden

@app.errorhandler(403)
def page_error_403(e):
    return "You are not allowed to access this page!", 403

@app.errorhandler(404)
def page_404(e):
    path = request.path.replace('/','')
    data = Short_link.query.filter(Short_link.url_path==str(path)).all()
    if data and data[0]:
       return redirect(data[0].url)
       #return data[0].url
    else:
       return "Page Not Found", 404

@app.route('/')
def Index():
   return render_template('index.html', short_link_data = Short_link.query.all() )

@app.route("/api/add", methods=["GET", "POST"])
def index():
  resp = Response()
  resp.headers['Access-Control-Allow-Origin'] = '*'
  if request.method == "GET":
     return("POST METHOD REQUIRED!",resp)
  else:
      try:
        url_path = request.form["costume"]
        if url_path == 'random' or url_path == '':
           url_path = ''.join(random.choice(string.ascii_lowercase) for i in range(5))
        if re.search('[^a-zA-Z0-9-]', url_path):
            return json.dumps({
              'status'  : str(400),
              'message' : "Invalid Path!",
            })
        elif url_path in banned_path:
            return json.dumps({
                  'status'  : str(400),
                  'message' : "The costume path that you entered is in the banned list",
            })
        url  = request.form['url']
        if not re.search('^http(s)?://',url):
           url = 'http://'+url
        date = re.sub('\.(.+?)$', '', str(datetime.datetime.now()))
        viewers_count = str(1)
        data = Short_link(url_path, url, date, viewers_count)
        db.session.add(data)
        try:
          db.session.commit()
        except:
          return json.dumps({
              'status'  : str(400),
              'message' : 'Error, Maybe custom url already in database, please use another name!',
          })
        data2 = {
          'status'  : str(200),
          'path'    : url_path,
          'url'     : url,
          'date'    : str(date),
          'message' : 'Data added successfully',
        }
        return json.dumps(data2)
      except:
        return json.dumps({
              'status'  : str(400),
              'message' : "Invalid Request!",
        })

@app.route("/api/all")
def all_data():
  data = Short_link.query.all()
  tmp = []
  for x in data:
    tmp.append({
     "id"            : x.id,
     "url_path"      : x.url_path,
     "url"           : x.url,
     "date"          : x.date,
     "viewers_count" : x.viewers_count,
    })
  JSON = json.dumps(tmp)
  return Response(JSON, mimetype='application/javascript')

if __name__ == '__main__':
  db.create_all()
  app.run(host="0.0.0.0",port=3000, debug=True)
