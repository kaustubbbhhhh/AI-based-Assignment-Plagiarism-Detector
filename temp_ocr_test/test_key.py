import os
import sys

def test_huggingface(token):
    print("--- Testing Hugging Face Token ---")
    try:
        from huggingface_hub import HfApi
        api = HfApi(token=token)
        user = api.whoami()
        print(f"[SUCCESS] Token is a VALID Hugging Face token!")
        print(f"Username: {user.get('name')}")
        print(f"Full Name: {user.get('fullname')}")
        print(f"Email: {user.get('email')}")
        return True
    except Exception as e:
        print(f"[FAILED] Not a valid Hugging Face token: {e}")
        return False

def test_google_vision(api_key):
    print("\n--- Testing Google Cloud Vision API Key ---")
    try:
        from google.cloud import vision
        # Set up client with API key option
        client = vision.ImageAnnotatorClient(client_options={"api_key": api_key})
        print("Initialized Vision client with API key.")
        
        # Test with a dummy request (empty image)
        # If the API key is completely invalid, it will throw an authentication error
        image = vision.Image()
        print("Sending test request to Google Cloud Vision...")
        try:
            # We call with an empty image; it should return a 400 or bad request,
            # but if it's an authentication error (403/401), we know the key is invalid.
            response = client.label_detection(image=image)
            print("[SUCCESS] API Key auth accepted (Request processed).")
            return True
        except Exception as api_err:
            err_str = str(api_err)
            if "API key not valid" in err_str or "API_KEY_INVALID" in err_str or "403" in err_str or "401" in err_str:
                print(f"[FAILED] Invalid Google API Key: {api_err}")
                return False
            else:
                # If it's a 400 Bad Request (due to empty image), auth was actually accepted!
                print(f"[SUCCESS] Auth accepted, but request returned expected error: {api_err}")
                return True
    except Exception as e:
        print(f"[FAILED] Error during Google Vision test: {e}")
        return False

if __name__ == "__main__":
    key = "3559d0d7679481a9153f140a00cb8df0384652d9"
    print(f"Analyzing key: {key[:5]}...{key[-5:]}\n")
    
    is_hf = test_huggingface(key)
    is_gcp = test_google_vision(key)
    
    print("\n--- Summary ---")
    if is_hf:
        print("Result: Key is a Hugging Face Token.")
    elif is_gcp:
        print("Result: Key is a Google Cloud Vision API Key.")
    else:
        print("Result: Key is invalid for both Hugging Face and Google Cloud Vision.")
