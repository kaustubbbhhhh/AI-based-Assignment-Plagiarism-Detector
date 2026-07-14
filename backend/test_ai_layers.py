import sys
import json
from services.ai_detection import analyze_ai_content

ai_text = """
The concept of artificial intelligence plays a crucial role in modern technology. 
Furthermore, it has garnered significant attention from researchers and practitioners alike. 
In essence, machine learning is a multifaceted domain that can be defined as the ability of computers to learn without being explicitly programmed. 
Moreover, its applications span across numerous industries. 
In conclusion, it is important to note that the landscape of technology will continue to evolve.
""" * 3

human_text = """
I don't really know how to start this, but my experience with learning coding has been completely crazy so far! 
At first I thought it would be easy. You know, just typing some commands on a keyboard and watching things happen.
But man, I was so wrong lol. I felt like giving up multiple times, especially when I couldn't figure out why my React components weren't mounting. 
I think the hardest part is just staying motivated when everything breaks. Anyway, we will see how it goes next semester.
""" * 3

print("--- Testing AI Generated Text ---")
ai_res = analyze_ai_content(ai_text)
print(json.dumps(ai_res, indent=2))

print("\n--- Testing Human Generated Text ---")
human_res = analyze_ai_content(human_text)
print(json.dumps(human_res, indent=2))
