import os
from functools import wraps

from flask import Flask, request, Response, render_template_string
from flask_cors import CORS, cross_origin
from random import randrange
import simplejson as json
import boto3
from multiprocessing import Pool
from multiprocessing import cpu_count

app = Flask(__name__)

VOTES_PASSWORD = os.getenv('VOTES_PASSWORD', 'admin123')

def check_auth(password):
    return password == VOTES_PASSWORD

def authenticate():
    return Response('Access denied', 401, {'WWW-Authenticate': 'Basic realm="Votes Page"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

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
        .btn { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; font-size: 1rem; font-weight: 600; transition: opacity 0.2s, transform 0.1s; width: 100%; }
        .btn:hover { opacity: 0.9; }
        .btn:active { transform: scale(0.98); }
        .btn:disabled { opacity: 0.6; cursor: not-allowed; }
        .msg { position: fixed; top: 1rem; right: 1rem; background: #10b981; color: #fff; padding: 1rem 1.5rem; border-radius: 8px; display: none; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <div class="container">
        <h1>🍽️ Restaurant Votes</h1>
        <div class="grid" id="grid"></div>
    </div>
    <div class="msg" id="msg"></div>
    <script>
        const restaurants = ['outback', 'bucadibeppo', 'ihop', 'chipotle'];
        const names = { outback: 'Outback', bucadibeppo: 'Buca di Beppo', ihop: 'IHOP', chipotle: 'Chipotle' };
        
        async function loadVotes() {
            const res = await fetch('/api/getvotes');
            const data = await res.json();
            const grid = document.getElementById('grid');
            grid.innerHTML = data.map(r => `
                <div class="card">
                    <h2>${names[r.name] || r.name}</h2>
                    <div class="votes" id="v-${r.name}">${r.value}</div>
                    <button class="btn" onclick="vote('${r.name}')">Vote</button>
                </div>
            `).join('');
        }
        
        async function vote(name) {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Voting...';
            const res = await fetch('/api/' + name);
            const newVotes = await res.text();
            document.getElementById('v-' + name).textContent = newVotes;
            btn.disabled = false;
            btn.textContent = 'Vote';
            const msg = document.getElementById('msg');
            msg.textContent = `Voted for ${names[name]}!`;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display = 'none', 2000);
        }
        
        loadVotes();
    </script>
</body>
</html>'''

@app.route('/votes')
@requires_auth
def votes_page():
    return render_template_string(VOTES_HTML)

if __name__ == '__main__':
   app.run(host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
   app.debug =True
