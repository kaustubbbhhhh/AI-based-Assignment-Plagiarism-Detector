import urllib.request
import os
import sys

# A sample of handwritten text from a public OCR dataset
image_url = "https://raw.githubusercontent.com/ThomasDelteil/HandwrittenTextRecognition_MXNet/master/data/lineImages/a01/a01-000u/a01-000u-00.png"
image_path = "sample_handwritten.png"


print(f"Downloading handwritten sample...")
try:
    req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as response, open(image_path, 'wb') as out_file:
        out_file.write(response.read())
    print(f"[SUCCESS] Saved as {image_path}")
    
    print(f"\nRunning Reading Doc Layer on {image_path}...")
    # Call the test script we created earlier
    os.system(f"{sys.executable} test_extraction.py {image_path}")
except Exception as e:
    print(f"Failed to download or run test: {e}")


