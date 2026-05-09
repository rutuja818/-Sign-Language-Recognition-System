# sign_to_arduino.py
import cv2
import mediapipe as mp
import numpy as np
import time
import joblib
import serial
from sklearn.neighbors import KNeighborsClassifier
import os

# ------------- USER PARAMETERS -------------
SERIAL_PORT = 'COM3'      # <-- change this to your Arduino port (e.g., 'COM3' or '/dev/ttyACM0')
BAUDRATE = 9600
MODEL_FILE = 'sign_knn.joblib'
DATA_FILE = 'sign_dataset.npz'
CAPTURE_FRAMES = 40       # frames captured per label when collecting
STABILITY_FRAMES = 5      # frames of same prediction needed before sending
# -------------------------------------------

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


def open_serial():
    """Try to open the Arduino serial port"""
    try:
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        time.sleep(2)  # allow Arduino to reset
        print(f"[INFO] Opened serial {SERIAL_PORT} @ {BAUDRATE}")
        return ser
    except Exception as e:
        print("[ERROR] Could not open serial:", e)
        return None


def extract_features(hand_landmarks):
    """Extract normalized (x, y, z) features relative to wrist"""
    lm = [(p.x, p.y, p.z) for p in hand_landmarks.landmark]
    wrist = lm[0]
    feats = []
    for (x, y, z) in lm:
        feats += [x - wrist[0], y - wrist[1], z - wrist[2]]

    # scale normalization
    max_abs = max(abs(v) for v in feats) or 1.0
    feats = [v / max_abs for v in feats]
    return np.array(feats, dtype=np.float32)


def save_dataset(X, y):
    np.savez_compressed(DATA_FILE, X=np.array(X), y=np.array(y))
    print(f"[INFO] Saved dataset: {DATA_FILE}")


def load_dataset():
    if not os.path.exists(DATA_FILE):
        return None, None
    d = np.load(DATA_FILE)
    return d['X'], d['y']


def train_and_save(X, y):
    print("[INFO] Training KNN...")
    knn = KNeighborsClassifier(n_neighbors=3)
    knn.fit(X, y)
    joblib.dump(knn, MODEL_FILE)
    print(f"[INFO] Saved model to {MODEL_FILE}")
    return knn


def main():
    ser = None
    model = None
    X, y = [], []

    # Try loading existing dataset/model
    X_loaded, y_loaded = load_dataset()
    if X_loaded is not None:
        X = list(X_loaded)
        y = list(y_loaded)
        print(f"[INFO] Loaded dataset with {len(X)} samples.")
    if os.path.exists(MODEL_FILE):
        model = joblib.load(MODEL_FILE)
        print(f"[INFO] Loaded model: {MODEL_FILE}")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Camera not accessible.")
        return

    with mp_hands.Hands(min_detection_confidence=0.5,
                        min_tracking_confidence=0.5,
                        max_num_hands=1) as hands:

        pred_history = []
        sent_label = ""
        mode = 'idle'  # idle / run
        print("\n[CONTROLS] c=collect | t=train | r=run | s=save dataset | q=quit\n")

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Camera not opened properly.")
                break

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            display_text = ""

            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                feats = extract_features(hand)

                if mode == 'run' and model is not None:
                    pred = model.predict([feats])[0]
                    pred_history.append(pred)

                    if len(pred_history) > STABILITY_FRAMES:
                        pred_history.pop(0)

                    if len(pred_history) == STABILITY_FRAMES and all(p == pred_history[0] for p in pred_history):
                        display_text = f"Pred: {pred}"
                        if ser and pred != sent_label:
                            try:
                                ser.write((str(pred) + '\n').encode())
                                sent_label = pred
                                print(f"[SENT] {pred}")
                            except Exception as e:
                                print("[ERROR] Serial write:", e)
                else:
                    display_text = "Hand detected (idle)."
            else:
                pred_history = []

            cv2.putText(frame, display_text, (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.imshow("Sign -> Arduino", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                print("[INFO] Quitting...")
                break

            elif key == ord('s'):
                if len(X) > 0:
                    save_dataset(X, y)
                else:
                    print("[WARN] No data to save.")

            elif key == ord('c'):
                label = input("Enter label for capture (e.g., HELLO, A, 1): ").strip()
                if label == "":
                    print("[WARN] Empty label, skipping.")
                    continue

                print(f"[INFO] Capturing {CAPTURE_FRAMES} frames for '{label}'...")
                captured = 0
                while captured < CAPTURE_FRAMES:
                    ret2, f2 = cap.read()
                    if not ret2:
                        break
                    f2 = cv2.flip(f2, 1)
                    rgb2 = cv2.cvtColor(f2, cv2.COLOR_BGR2RGB)
                    res2 = hands.process(rgb2)
                    if res2.multi_hand_landmarks:
                        feats2 = extract_features(res2.multi_hand_landmarks[0])
                        X.append(feats2)
                        y.append(label)
                        captured += 1
                        cv2.putText(f2, f"Capturing {captured}/{CAPTURE_FRAMES} '{label}'",
                                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                    else:
                        cv2.putText(f2, "No hand detected...", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    cv2.imshow("Sign -> Arduino", f2)
                    cv2.waitKey(1)
                print(f"[INFO] Captured {captured} frames for '{label}'. Total: {len(X)} samples.")

            elif key == ord('t'):
                if len(X) < 5:
                    print("[WARN] Not enough samples to train (collect more).")
                else:
                    model = train_and_save(np.array(X), np.array(y))

            elif key == ord('r'):
                if model is None:
                    if os.path.exists(MODEL_FILE):
                        model = joblib.load(MODEL_FILE)
                        print(f"[INFO] Loaded model: {MODEL_FILE}")
                    else:
                        print("[ERROR] No model found. Train first.")
                        continue
                if ser is None:
                    ser = open_serial()
                if ser is None:
                    print("[WARN] Serial not opened. Running without Arduino.")
                mode = 'run'
                print("[INFO] Run mode activated. Press 'q' to stop.")

    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()
        print("[INFO] Serial connection closed.")


if __name__ == "__main__":
    main()
