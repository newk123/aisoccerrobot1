from ultralytics import YOLO
from picamera2 import Picamera2
import cv2
import time


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "best_ncnn_model"

CONF_THRESHOLD = 0.40

# Smaller = faster inference
IMG_SIZE = 416

# Camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480


# ============================================================
# START
# ============================================================

print("==============================================")
print("   SOCCER BALL DETECTION - NCNN")
print("==============================================")


# ============================================================
# LOAD MODEL
# ============================================================

print("Loading NCNN model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully!")
print("Classes:", model.names)


# ============================================================
# CAMERA SETUP
# ============================================================

print("Starting Camera...")

picam2 = Picamera2()

camera_config = picam2.create_preview_configuration(
    main={
        "size": (CAMERA_WIDTH, CAMERA_HEIGHT),
        "format": "XRGB8888"
    },
    buffer_count=4
)

picam2.configure(camera_config)

picam2.start()

time.sleep(2)

print("Camera started successfully!")
print("Press Q to quit.")


# ============================================================
# FPS VARIABLES
# ============================================================

previous_time = time.perf_counter()

fps = 0.0


# ============================================================
# MAIN LOOP
# ============================================================

try:

    while True:

        # ====================================================
        # CAMERA FRAME
        # ====================================================

        frame = picam2.capture_array()

        # XRGB8888 = 4 channels
        #
        # Take first 3 channels.
        #
        # .copy() is IMPORTANT because OpenCV requires
        # a contiguous writable array.
        #

        frame = frame[:, :, :3].copy()


        # ====================================================
        # YOLO NCNN INFERENCE
        # ====================================================

        results = model.predict(
            source=frame,
            imgsz=IMG_SIZE,
            conf=CONF_THRESHOLD,
            verbose=False
        )

        result = results[0]


        # ====================================================
        # DETECTION VARIABLES
        # ====================================================

        ball_detected = False

        ball_count = 0


        # ====================================================
        # PROCESS YOLO BOXES
        # ====================================================

        if result.boxes is not None:

            for box in result.boxes:

                class_id = int(box.cls[0])

                confidence = float(box.conf[0])


                # --------------------------------------------
                # CLASS 0 = BALL
                # --------------------------------------------

                if class_id == 0:

                    ball_detected = True

                    ball_count += 1


                    # ----------------------------------------
                    # GET BOX COORDINATES
                    # ----------------------------------------

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )


                    # ----------------------------------------
                    # DRAW BOX
                    # ----------------------------------------

                    cv2.rectangle(
                        frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2
                    )


                    # ----------------------------------------
                    # BALL LABEL
                    # ----------------------------------------

                    label = f"Ball {confidence * 100:.1f}%"


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
        # FPS
        # ====================================================

        current_time = time.perf_counter()

        elapsed = current_time - previous_time

        if elapsed > 0:

            fps = 1.0 / elapsed

        previous_time = current_time


        # ====================================================
        # STATUS
        # ====================================================

        if ball_detected:

            status_text = "BALL DETECTED"

            status_color = (0, 255, 0)

        else:

            status_text = "NO BALL"

            status_color = (0, 0, 255)


        # ====================================================
        # STATUS TEXT
        # ====================================================

        cv2.putText(
            frame,
            status_text,
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            status_color,
            2,
            cv2.LINE_AA
        )


        # ====================================================
        # BALL COUNT
        # ====================================================

        cv2.putText(
            frame,
            f"Ball Count: {ball_count}",
            (15, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )


        # ====================================================
        # FPS
        # ====================================================

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
            "Soccer Ball Detection - NCNN",
            frame
        )


        # ====================================================
        # QUIT
        # ====================================================

        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):

            print("Q pressed. Stopping...")

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

    print("Stopping camera...")

    picam2.stop()

    cv2.destroyAllWindows()

    print("Camera stopped.")
    print("Program finished.")