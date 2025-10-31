from flask import Flask, jsonify
import os
import mysql.connector
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)
metrics.info("app_info", "Flask App info", version="1.1")

db_config = {
    'host': os.getenv('MYSQL_HOST', 'db'),
    'user': os.getenv('MYSQL_USER', 'appuser'),
    'password': os.getenv('MYSQL_PASSWORD', 'apppass'),
    'database': os.getenv('MYSQL_DATABASE', 'appdb')
}

@app.route('/')
def hello():
    return "Hello Flask + MySQL (secured env vars)!"

@app.route('/users')
def users():
    cnx = mysql.connector.connect(**db_config)
    cursor = cnx.cursor(dictionary=True)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255)
        )
    """)
    cursor.execute("INSERT INTO users (name) VALUES ('Ali')")
    cnx.commit()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    cursor.close()
    cnx.close()
    return jsonify(rows)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
