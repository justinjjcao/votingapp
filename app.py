import os

from flask import Flask, request, render_template_string, redirect, url_for, session
from flask_cors import CORS, cross_origin
from random import randrange
import simplejson as json
import boto3
from multiprocessing import Pool
from multiprocessing import cpu_count
from functools import wraps

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', os.urandom(24))
VOTES_PASSWORD = os.getenv('VOTES_PASSWORD', 'admin123')

cors = CORS(app, resources={r"/api/*": {"Access-Control-Allow-Origin": "*"}})

cpustressfactor = os.getenv('CPUSTRESSFACTOR', 1)
memstressfactor = os.getenv('MEMSTRESSFACTOR', 1)
ddb_aws_region = os.getenv('DDB_AWS_REGION')
ddb_table_name = os.getenv('DDB_TABLE_NAME', "votingapp-restaurants")

ddb = boto3.resource('dynamodb', region_name=ddb_aws_region)
ddbtable = ddb.Table(ddb_table_name)

print("The cpustressfactor variable is set to: " + str(cpustressfactor))
print("The memstressfactor variable is set to: " + str(memstressfactor))
memeater=[]
memeater=[0 for i in range(10000)] 

## https://gist.github.com/tott/3895832
def f(x):
    for x in range(1000000 * int(cpustressfactor)):
        x*x

def readvote(restaurant):
    response = ddbtable.get_item(Key={'name': restaurant})
    # this is required to convert decimal to integer 
    normilized_response = json.dumps(response)
    json_response = json.loads(normilized_response)
    votes = json_response["Item"]["restaurantcount"]
    return str(votes)

def updatevote(restaurant, votes):
    ddbtable.update_item(
        Key={
            'name': restaurant
        },
        UpdateExpression='SET restaurantcount = :value',
        ExpressionAttributeValues={
            ':value': votes
        },
        ReturnValues='UPDATED_NEW'
    )
    return str(votes)

@app.route('/')
def home():
    return "<h1>Welcome to the Voting App</h1><p><b>To vote, you can call the following APIs:</b></p><p>/api/outback</p><p>/api/bucadibeppo</p><p>/api/ihop</p><p>/api/chipotle</p><b>To query the votes, you can call the following APIs:</b><p>/api/getvotes</p><p>/api/getheavyvotes (this generates artificial CPU/memory load)</p>"

@app.route("/api/outback")
def outback():
    string_votes = readvote("outback")
    votes = int(string_votes)
    votes += 1
    string_new_votes = updatevote("outback", votes)
    return string_new_votes 

@app.route("/api/bucadibeppo")
def bucadibeppo():
    string_votes = readvote("bucadibeppo")
    votes = int(string_votes)
    votes += 1
    string_new_votes = updatevote("bucadibeppo", votes)
    return string_new_votes 

@app.route("/api/ihop")
def ihop():
    string_votes = readvote("ihop")
    votes = int(string_votes)
    votes += 1
    string_new_votes = updatevote("ihop", votes)
    return string_new_votes 

@app.route("/api/chipotle")
def chipotle():
    string_votes = readvote("chipotle")
    votes = int(string_votes)
    votes += 1
    string_new_votes = updatevote("chipotle", votes)
    return string_new_votes 

@app.route("/api/getvotes")
def getvotes():
    string_outback = readvote("outback")
    string_ihop = readvote("ihop")
    string_bucadibeppo = readvote("bucadibeppo")
    string_chipotle = readvote("chipotle")
    string_votes = '[{"name": "outback", "value": ' + string_outback + '},' + '{"name": "bucadibeppo", "value": ' + string_bucadibeppo + '},' + '{"name": "ihop", "value": '  + string_ihop + '}, ' + '{"name": "chipotle", "value": '  + string_chipotle + '}]'
    return string_votes

@app.route("/api/getheavyvotes")
def getheavyvotes():
    string_outback = readvote("outback")
    string_ihop = readvote("ihop")
    string_bucadibeppo = readvote("bucadibeppo")
    string_chipotle = readvote("chipotle")
    string_votes = '[{"name": "outback", "value": ' + string_outback + '},' + '{"name": "bucadibeppo", "value": ' + string_bucadibeppo + '},' + '{"name": "ihop", "value": '  + string_ihop + '}, ' + '{"name": "chipotle", "value": '  + string_chipotle + '}]'
    print("You invoked the getheavyvotes API. I am eating 100MB * " + str(memstressfactor) + " at every votes request")
    memeater[randrange(10000)] = bytearray(1024 * 1024 * 100 * memstressfactor, encoding='utf8') # eats 100MB * memstressfactor
    print("You invoked the getheavyvotes API. I am eating some cpu * " + str(cpustressfactor) + " at every votes request")
    processes = cpu_count()
    pool = Pool(processes)
    pool.map(f, range(processes))
    return string_votes

def require_password(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('authenticated'):
            return redirect(url_for('votes_login'))
        return f(*args, **kwargs)
    return decorated

VOTES_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restaurant Votes</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 2rem; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #fff; text-align: center; margin-bottom: 2rem; font-size: 2.5rem; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }
        .card { background: #fff; border-radius: 16px; padding: 1.5rem; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.2); transition: transform 0.2s, box-shadow 0.2s; }
        .card:hover { transform: translateY(-5px); box-shadow: 0 15px 50px rgba(0,0,0,0.3); }
        .card h2 { color: #333; font-size: 1.2rem; margin-bottom: 0.5rem; text-transform: capitalize; }
        .votes { font-size: 2.5rem; font-weight: bold; color: #667eea; margin: 1rem 0; }
        .vote-btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-size: 1rem; cursor: pointer; transition: opacity 0.2s, transform 0.1s; }
        .vote-btn:hover { opacity: 0.9; }
        .vote-btn:active { transform: scale(0.95); }
        .logout { display: block; text-align: center; margin-top: 2rem; color: #fff; text-decoration: none; opacity: 0.8; }
        .logout:hover { opacity: 1; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍽️ Restaurant Votes</h1>
        <div class="grid">
            {% for r in restaurants %}
            <div class="card">
                <h2>{{ r.name }}</h2>
                <div class="votes">{{ r.value }}</div>
                <form method="POST" style="display:inline;">
                    <input type="hidden" name="restaurant" value="{{ r.name }}">
                    <button type="submit" class="vote-btn">Vote</button>
                </form>
            </div>
            {% endfor %}
        </div>
        <a href="/votes/logout" class="logout">Logout</a>
    </div>
</body>
</html>'''

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Restaurant Votes</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
        .login-box { background: #fff; padding: 2.5rem; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); width: 100%; max-width: 360px; }
        h1 { color: #333; text-align: center; margin-bottom: 1.5rem; font-size: 1.5rem; }
        input[type="password"] { width: 100%; padding: 0.75rem 1rem; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 1rem; margin-bottom: 1rem; transition: border-color 0.2s; }
        input[type="password"]:focus { outline: none; border-color: #667eea; }
        button { width: 100%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 0.75rem; border-radius: 8px; font-size: 1rem; cursor: pointer; transition: opacity 0.2s; }
        button:hover { opacity: 0.9; }
        .error { color: #e74c3c; text-align: center; margin-bottom: 1rem; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="login-box">
        <h1>🔐 Enter Password</h1>
        {% if error %}<p class="error">{{ error }}</p>{% endif %}
        <form method="POST">
            <input type="password" name="password" placeholder="Password" required autofocus>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>'''

@app.route('/votes/login', methods=['GET', 'POST'])
def votes_login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == VOTES_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('votes'))
        error = 'Invalid password'
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/votes/logout')
def votes_logout():
    session.pop('authenticated', None)
    return redirect(url_for('votes_login'))

@app.route('/votes', methods=['GET', 'POST'])
@require_password
def votes():
    if request.method == 'POST':
        restaurant = request.form.get('restaurant')
        if restaurant in ['outback', 'bucadibeppo', 'ihop', 'chipotle']:
            current = int(readvote(restaurant))
            updatevote(restaurant, current + 1)
        return redirect(url_for('votes'))
    
    restaurants = [
        {'name': 'outback', 'value': int(readvote('outback'))},
        {'name': 'bucadibeppo', 'value': int(readvote('bucadibeppo'))},
        {'name': 'ihop', 'value': int(readvote('ihop'))},
        {'name': 'chipotle', 'value': int(readvote('chipotle'))}
    ]
    return render_template_string(VOTES_HTML, restaurants=restaurants)

if __name__ == '__main__':
   app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
   app.debug =True
