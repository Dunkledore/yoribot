from flask import Flask, request, render_template

app = Flask(__name__)

@app.route('/')
def index():
	return "test"


app.run(host = '50.88.155.128', port = 80)