from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import time


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "best_ncnn_model"

# Confidence
CONF_THRESHOLD = 0.45

# Smaller = faster NCNN
IMG_SIZE = 320

# Camera
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================================
# TRACKING SETTINGS
# ============================================================

# Number of consecutive detections required
DETECT_CONFIRM_FRAMES = 2

# Number of frames allowed without detection
MAX_MISSED_FRAMES = 5

# Position smoothing
SMOOTHING = 0.65


# ============================================================
# MOTOR COMMAND SETTINGS
# ============================================================

# Horizontal dead zone
LEFT_ZONE = 0.40
RIGHT_ZONE = 0.60


# ============================================================
# LOAD MODEL
# ============================================================

print("==============================================")
print("   REAL-TIME SOCCER BALL TRACKING - NCNN")
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
# VARIABLES
# ============================================================

last_command = "S"

missed_frames = 0
confirmed_frames = 0

smooth_cx = None
smooth_cy = None

fps = 0.0

previous_time = time.perf_counter()


# ============================================================
# MOTOR COMMAND FUNCTION
# ============================================================

def send_motor_command(command):

    global last_command

    # Send only when command changes
    if command != last_command:

        print("MOTOR:", command)

        # ====================================================
        # LATER:
        # Bluetooth / Serial command goes here
        #
        # Example:
        # bluetooth.write(command.encode())
        # ====================================================

        last_command = command


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        # ====================================================
        # CAPTURE LATEST FRAME
        # ====================================================

        frame = picam2.capture_array()

        # XRGB8888
        frame = frame[:, :, :3].copy()


        # ====================================================
        # YOLO NCNN
        # ====================================================

        results = model.predict(
            source=frame,
            imgsz=IMG_SIZE,
            conf=CONF_THRESHOLD,
            verbose=False,
            max_det=1
        )

        result = results[0]


        # ====================================================
        # BALL VARIABLES
        # ====================================================

        ball_found = False

        ball_confidence = 0.0

        ball_box = None


        # ====================================================
        # GET BALL
        # ====================================================

        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(box.cls[0])

                confidence = float(box.conf[0])


                # Class 0 = Ball
                if class_id == 0:

                    ball_found = True

                    ball_confidence = confidence

                    ball_box = box.xyxy[0].tolist()

                    break


        # ====================================================
        # BALL DETECTED
        # ====================================================

        if ball_found:

            missed_frames = 0

            confirmed_frames += 1


            x1, y1, x2, y2 = map(
                int,
                ball_box
            )


            # ------------------------------------------------
            # BALL CENTER
            # ------------------------------------------------

            cx = (x1 + x2) // 2
            cy = (y1 + y2) // 2


            # ------------------------------------------------
            # SMOOTH POSITION
            # ------------------------------------------------

            if smooth_cx is None:

                smooth_cx = cx
                smooth_cy = cy

            else:

                smooth_cx = (
                    SMOOTHING * smooth_cx
                    +
                    (1 - SMOOTHING) * cx
                )

                smooth_cy = (
                    SMOOTHING * smooth_cy
                    +
                    (1 - SMOOTHING) * cy
                )


            draw_cx = int(smooth_cx)
            draw_cy = int(smooth_cy)


            # ------------------------------------------------
            # DRAW BALL BOX
            # ------------------------------------------------

            cv2.rectangle(
                frame,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


            # ------------------------------------------------
            # DRAW CENTER
            # ------------------------------------------------

            cv2.circle(
                frame,
                (draw_cx, draw_cy),
                6,
                (0, 0, 255),
                -1
            )


            # ------------------------------------------------
            # LABEL
            # ------------------------------------------------

            label = f"BALL {ball_confidence * 100:.0f}%"

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


            # =================================================
            # CONFIRM DETECTION
            # =================================================

            if confirmed_frames >= DETECT_CONFIRM_FRAMES:

                # ---------------------------------------------
                # NORMALIZED BALL X POSITION
                # ---------------------------------------------

                normalized_x = draw_cx / CAMERA_WIDTH


                # ---------------------------------------------
                # LEFT
                # ---------------------------------------------

                if normalized_x < LEFT_ZONE:

                    command = "L"


                # ---------------------------------------------
                # RIGHT
                # ---------------------------------------------

                elif normalized_x > RIGHT_ZONE:

                    command = "R"


                # ---------------------------------------------
                # CENTER
                # ---------------------------------------------

                else:

                    command = "F"


                send_motor_command(command)


        # ====================================================
        # BALL NOT DETECTED
        # ====================================================

        else:

            confirmed_frames = 0

            missed_frames += 1


            # Keep previous command for a few frames
            # to prevent unstable motor switching

            if missed_frames > MAX_MISSED_FRAMES:

                send_motor_command("S")

                smooth_cx = None
                smooth_cy = None


        # ====================================================
        # TRACKING GUIDE
        # ====================================================

        center_x = CAMERA_WIDTH // 2

        left_x = int(CAMERA_WIDTH * LEFT_ZONE)
        right_x = int(CAMERA_WIDTH * RIGHT_ZONE)


        # Vertical guide lines

        cv2.line(
            frame,
            (left_x, 0),
            (left_x, CAMERA_HEIGHT),
            (255, 255, 255),
            1
        )

        cv2.line(
            frame,
            (right_x, 0),
            (right_x, CAMERA_HEIGHT),
            (255, 255, 255),
            1
        )


        # Center line

        cv2.line(
            frame,
            (center_x, 0),
            (center_x, CAMERA_HEIGHT),
            (255, 255, 255),
            1
        )


        # ====================================================
        # STATUS
        # ====================================================

        if ball_found:

            status = "BALL TRACKING"

            status_color = (0, 255, 0)

        else:

            status = "SEARCHING..."

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
        # MOTOR COMMAND DISPLAY
        # ====================================================

        cv2.putText(
            frame,
            f"MOTOR: {last_command}",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )


        # ====================================================
        # FPS
        # ====================================================

        current_time = time.perf_counter()

        elapsed = current_time - previous_time

        if elapsed > 0:

            fps = 1.0 / elapsed

        previous_time = current_time


        cv2.putText(
            frame,
            f"FPS: {fps:.1f}",
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
            "REAL-TIME BALL TRACKING",
            frame
        )


        # ====================================================
        # QUIT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print("Q pressed.")

            send_motor_command("S")

            break


# ============================================================
# ERROR HANDLING
# ============================================================

except KeyboardInterrupt:

    print("\nStopped by user.")


except Exception as e:

    print("\nERROR:")
    print(e)


# ============================================================
# CLEANUP
# ============================================================

finally:

    print("Stopping motors...")

    send_motor_command("S")

    print("Stopping camera...")

    picam2.stop()

    cv2.destroyAllWindows()

    print("Done.")