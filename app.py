from flask import Flask

DATABASE = 'sqlite3.db'
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello Flask!"

if __name__ == "__main__":
    app.run()