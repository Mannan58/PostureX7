from flask import Flask, Response, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import cv2

from Main import PoseDetector, ExerciseAnalyzer, Renderer

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///project.db"


# -------------------- LOGIN PAGE --------------------
@app.route('/')
def login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def do_login():
    username = request.form.get('username')
    return redirect(url_for('home', user=username))


# -------------------- HOME DASHBOARD --------------------
@app.route('/home')
def home():
    user = request.args.get('user', 'User')
    return render_template('home.html', user=user)


# -------------------- EXERCISE PAGE --------------------
@app.route('/exercise')
def exercise():
    return render_template('exercise.html')


@app.route('/detect')
def detect():
    return render_template('detect.html')


# -------------------- VIDEO STREAM --------------------
@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def generate_frames():
    cap = cv2.VideoCapture(0)

    detector = PoseDetector()
    analyzer = ExerciseAnalyzer()
    analyzer.switch("SQUAT")
    renderer = Renderer()

    try:
        while True:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)

            landmarks, _ = detector.detect(frame)

            if landmarks:
                side = detector.choose_visible_side(landmarks)
                state = analyzer.update(landmarks, side)
            else:
                state = analyzer.state

            renderer.draw(frame, landmarks, detector, state, fps=0)

            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        cap.release()


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)