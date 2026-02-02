import os

from flask import Flask, request, session, redirect, url_for, render_template_string
from flask_cors import CORS, cross_origin
from random import randrange
import simplejson as json
import boto3
from multiprocessing import Pool
from multiprocessing import cpu_count

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'votingapp-secret-key-change-in-production')
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

LOGIN_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Voting App</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; min-height: 100vh; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
        .login-card { background: white; padding: 2.5rem; border-radius: 1rem; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.25); width: 100%; max-width: 400px; }
        h1 { color: #1f2937; margin-bottom: 1.5rem; text-align: center; }
        .error { background: #fee2e2; color: #dc2626; padding: 0.75rem; border-radius: 0.5rem; margin-bottom: 1rem; text-align: center; }
        label { display: block; color: #374151; font-weight: 500; margin-bottom: 0.5rem; }
        input[type="password"] { width: 100%; padding: 0.75rem 1rem; border: 2px solid #e5e7eb; border-radius: 0.5rem; font-size: 1rem; transition: border-color 0.2s; }
        input[type="password"]:focus { outline: none; border-color: #667eea; }
        button { width: 100%; padding: 0.875rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 0.5rem; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 1rem; transition: transform 0.2s, box-shadow 0.2s; }
        button:hover { transform: translateY(-2px); box-shadow: 0 10px 20px -10px rgba(102,126,234,0.5); }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>🗳️ Voting App</h1>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST">
            <label for="password">Password</label>
            <input type="password" id="password" name="password" required autofocus>
            <button type="submit">Login</button>
        </form>
    </div>
</body>
</html>'''

VOTES_HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Votes - Voting App</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: system-ui, -apple-system, sans-serif; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; }
        .container { max-width: 800px; margin: 0 auto; }
        header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
        h1 { color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .logout { color: white; text-decoration: none; padding: 0.5rem 1rem; border: 2px solid white; border-radius: 0.5rem; transition: all 0.2s; }
        .logout:hover { background: white; color: #667eea; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1.5rem; }
        .card { background: white; border-radius: 1rem; padding: 1.5rem; text-align: center; box-shadow: 0 10px 40px -10px rgba(0,0,0,0.2); transition: transform 0.2s; }
        .card:hover { transform: translateY(-5px); }
        .card h2 { color: #1f2937; font-size: 1.1rem; margin-bottom: 0.5rem; text-transform: capitalize; }
        .votes { font-size: 2.5rem; font-weight: 700; color: #667eea; margin: 0.5rem 0; }
        .vote-btn { width: 100%; padding: 0.75rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 0.5rem; font-size: 0.9rem; font-weight: 600; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; }
        .vote-btn:hover { transform: scale(1.05); box-shadow: 0 5px 15px -5px rgba(102,126,234,0.5); }
        .vote-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🗳️ Restaurant Votes</h1>
            <a href="/votes/logout" class="logout">Logout</a>
        </header>
        <div class="grid">
            {% for r in restaurants %}
            <div class="card">
                <h2>{{ r.name }}</h2>
                <div class="votes" id="votes-{{ r.name }}">{{ r.value }}</div>
                <button class="vote-btn" onclick="vote('{{ r.name }}')">Vote</button>
            </div>
            {% endfor %}
        </div>
    </div>
    <script>
        async function vote(name) {
            const btn = event.target;
            btn.disabled = true;
            try {
                const res = await fetch('/api/' + name);
                if (res.ok) {
                    const newVotes = await res.text();
                    document.getElementById('votes-' + name).textContent = newVotes;
                }
            } finally {
                btn.disabled = false;
            }
        }
    </script>
</body>
</html>'''

@app.route('/votes', methods=['GET', 'POST'])
def votes_page():
    if request.method == 'POST':
        if request.form.get('password') == VOTES_PASSWORD:
            session['authenticated'] = True
            return redirect(url_for('votes_page'))
        return render_template_string(LOGIN_HTML, error='Invalid password')
    if not session.get('authenticated'):
        return render_template_string(LOGIN_HTML, error=None)
    restaurants = [
        {'name': 'outback', 'value': readvote('outback')},
        {'name': 'bucadibeppo', 'value': readvote('bucadibeppo')},
        {'name': 'ihop', 'value': readvote('ihop')},
        {'name': 'chipotle', 'value': readvote('chipotle')}
    ]
    return render_template_string(VOTES_HTML, restaurants=restaurants)

@app.route('/votes/logout')
def votes_logout():
    session.pop('authenticated', None)
    return redirect(url_for('votes_page'))

if __name__ == '__main__':
   app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
   app.debug =True
