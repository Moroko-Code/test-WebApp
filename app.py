from flask import Flask

# Create a Flask instance
app = Flask(__name__)

# Define a simple route
@app.route("/")
def hello():
    return "Hello, World! 👋 This Flask app is running on Azure App Service."

# Run the app (only when run directly)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)