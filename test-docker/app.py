from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return """
    <html>
        <head>
            <title>Mon Premier Docker</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 3em; margin: 0; }
                p { font-size: 1.5em; margin-top: 20px; }
                .emoji { font-size: 4em; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="emoji">🐳</div>
                <h1>Hello Docker !</h1>
                <p>Mon premier conteneur fonctionne ! 🎉</p>
                <p style="font-size: 1em; margin-top: 30px;">
                    Projet ISP - Auto-Scaling Intelligent
                </p>
            </div>
        </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
