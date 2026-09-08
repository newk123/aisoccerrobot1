from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import time
import RPi.GPIO as GPIO


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "best_ncnn_model"

CONF_THRESHOLD = 0.50

IMG_SIZE = 320

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================================
# GPIO SETTINGS
# ============================================================

GPIO_PIN_1 = 17
GPIO_PIN_2 = 27
GPIO_PIN_3 = 22

GPIO.setmode(GPIO.BCM)

GPIO.setup(GPIO_PIN_1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(GPIO_PIN_2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(GPIO_PIN_3, GPIO.OUT, initial=GPIO.LOW)


# ============================================================
# 3 SECOND OUTPUT
# ============================================================

PULSE_TIME = 3.0

pulse_active = False
pulse_start_time = 0.0


def gpio_on():

    global pulse_active
    global pulse_start_time

    GPIO.output(GPIO_PIN_1, GPIO.HIGH)
    GPIO.output(GPIO_PIN_2, GPIO.HIGH)
    GPIO.output(GPIO_PIN_3, GPIO.HIGH)

    pulse_active = True
    pulse_start_time = time.monotonic()

    print("GPIO 3 PINS = HIGH")
    print("3 SECOND PULSE STARTED")


def gpio_off():

    global pulse_active

    GPIO.output(GPIO_PIN_1, GPIO.LOW)
    GPIO.output(GPIO_PIN_2, GPIO.LOW)
    GPIO.output(GPIO_PIN_3, GPIO.LOW)

    pulse_active = False

    print("GPIO 3 PINS = LOW")


# ============================================================
# LOAD MODEL
# ============================================================

print("==============================================")
print("   SOCCER BALL DETECTION")
print("==============================================")

print("Loading NCNN model...")

model = YOLO(MODEL_PATH)

print("Model loaded!")
print("Classes:", model.names)


# ============================================================
# CAMERA
# ============================================================

print("Starting camera...")

picam2 = Picamera2()

camera_config = picam2.create_preview_configuration(
    main={
        "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
        "format": "XRGB8888"
    },
    buffer_count=2
)

picam2.configure(camera_config)
picam2.start()

time.sleep(2)

print("Camera started!")
print("Press Q to quit.")


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        # ====================================================
        # CAPTURE FRAME
        # ====================================================

        frame = picam2.capture_array()

        # XRGB8888 → OpenCV compatible
        frame = frame[:, :, :3].copy()


        # ====================================================
        # BALL DETECTION
        # ====================================================

        results = model.predict(
            source=frame,
            imgsz=IMG_SIZE,
            conf=CONF_THRESHOLD,
            verbose=False,
            max_det=5
        )

        result = results[0]


        # ====================================================
        # CHECK BALL
        # ====================================================

        ball_detected = False

        best_confidence = 0.0

        best_box = None


        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Class 0 = Ball

                if class_id == 0:

                    if confidence > best_confidence:

                        best_confidence = confidence

                        best_box = box.xyxy[0].tolist()

                        ball_detected = True


        # ====================================================
        # BALL DETECTED
        # ====================================================

        if ball_detected:

            # ----------------------------------------------
            # IMPORTANT:
            #
            # Start 3-second pulse ONLY if currently OFF.
            #
            # If ball disappears during these 3 seconds,
            # GPIO remains HIGH.
            # ----------------------------------------------

            if not pulse_active:

                gpio_on()


            # ------------------------------------------------
            # DRAW DETECTION
            # ------------------------------------------------

            if best_box is not None:

                x1, y1, x2, y2 = map(
                    int,
                    best_box
                )

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

                label = f"BALL {best_confidence * 100:.1f}%"

                cv2.putText(
                    frame,
                    label,
                    (x1, max(y1 - 10, 20)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                    cv2.LINE_AA
                )


        # ====================================================
        # 3 SECOND TIMER
        # ====================================================

        if pulse_active:

            elapsed = time.monotonic() - pulse_start_time

            remaining = PULSE_TIME - elapsed

            if elapsed >= PULSE_TIME:

                gpio_off()

                remaining = 0


        else:

            remaining = 0


        # ====================================================
        # DISPLAY STATUS
        # ====================================================

        if pulse_active:

            status = "GPIO ACTIVE"

            status_color = (0, 255, 0)

        elif ball_detected:

            status = "BALL DETECTED"

            status_color = (0, 255, 0)

        else:

            status = "NO BALL"

            status_color = (0, 0, 255)


        cv2.putText(
            frame,
            status,
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
            cv2.LINE_AA
        )


        # ====================================================
        # GPIO STATUS
        # ====================================================

        gpio_status = "HIGH" if pulse_active else "LOW"

        cv2.putText(
            frame,
            f"GPIO: {gpio_status}",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )


        # ====================================================
        # TIMER DISPLAY
        # ====================================================

        if pulse_active:

            cv2.putText(
                frame,
                f"Remaining: {remaining:.1f}s",
                (15, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
                cv2.LINE_AA
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.imshow(
            "Soccer Ball Detection",
            frame
        )


        # ====================================================
        # QUIT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print("Q pressed.")

            break


# ============================================================
# CLEANUP
# ============================================================

except KeyboardInterrupt:

    print("\nStopped by user.")


finally:

    # ALWAYS turn GPIO OFF
    gpio_off()

    picam2.stop()

    cv2.destroyAllWindows()

    GPIO.cleanup()

    print("Camera stopped.")
    print("GPIO cleaned.")
    print("Program finished.")