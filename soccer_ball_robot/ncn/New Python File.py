import os
from ultralytics import YOLO

# 1. உங்களிடம் இருக்கும் best.pt ஃபைலின் சரியான வழியை (Path) கொடுக்கவும்
# (உங்களது ஃபைல் இருக்கும் ஃபோல்டருக்கு ஏற்ப இதை மாற்றிக் கொள்ளலாம்)
model_path = "best.pt" 

if os.path.exists(model_path):
    print("மாடல் ஃபைல் கண்டுபிடிக்கப்பட்டது. லோடிங் செய்யப்படுகிறது...")
    model = YOLO(model_path)
    
    # 2. .pt ஃபைலை நேரடியாக NCNN வடிவத்திற்கு மாற்றவும்
    # imgsz=320 என்பது ராஸ்பெர்ரி பை 4-ல் ரியல்-டைம் வேகம் (High FPS) கிடைக்க உதவும்!
    print("NCNN வடிவத்திற்கு மாற்றப்படுகிறது (Conversion in progress)...")
    model.export(format="ncnn", imgsz=320)
    
    print("வெற்றி! உங்கள் மாடல் 'best_ncnn_model' என்ற ஃபோல்டராக மாற்றப்பட்டது.")
else:
    print(f"எர்ரர்: '{model_path}' ஃபைல் இந்த ஃபோல்டரில் இல்லை. ஃபைல் பெயரை சரிபார்க்கவும்!")
