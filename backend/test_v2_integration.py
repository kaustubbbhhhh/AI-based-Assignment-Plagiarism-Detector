"""Quick integration test for the v2 AI detection system."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from services.ai_detection import analyze_ai_content

# --- Test 1: Known AI-style text ---
ai_text = """
The rapid advancement of technology has significantly transformed the landscape of modern education. 
Furthermore, the integration of digital tools into educational frameworks has facilitated a paradigm 
shift in how knowledge is disseminated and acquired. It is worth noting that these technological 
advancements have not merely enhanced traditional teaching methods but have also introduced entirely 
new modalities of learning. Consequently, educators and institutions must adapt to these evolving 
dynamics to remain relevant and effective in their pedagogical approaches. In conclusion, the 
intersection of technology and education presents both opportunities and challenges that necessitate 
careful consideration and strategic planning.
"""

# --- Test 2: Known human-style text ---
human_text = """
I remember when I first started college, everything felt overwhelming. The lectures were long, 
the assignments piled up, and honestly I didn't know what I was doing half the time. My roommate 
was way better at managing things - she'd have her notes organized by color and everything. 
Meanwhile I'm over here trying to figure out where I even put my syllabus. Looking back though, 
I think that chaos taught me a lot about myself. I learned to ask for help, which isn't something 
that comes naturally to me. And yeah, my grades weren't perfect, but I survived. That's gotta 
count for something right?
"""

print("=" * 60)
print("INTEGRATION TEST: V2 AI Detection System")
print("=" * 60)

print("\n--- Test 1: AI-Generated Text ---")
result1 = analyze_ai_content(ai_text)
print(f"  Score:    {result1['ai_score']}%")
print(f"  Label:    {result1['label']}")
print(f"  Model:    {result1.get('model_version', 'unknown')}")
print(f"  Basis:    {result1.get('decision_basis', 'unknown')}")
print(f"  Reasoning: {result1['reasoning']}")

print("\n--- Test 2: Human-Written Text ---")
result2 = analyze_ai_content(human_text)
print(f"  Score:    {result2['ai_score']}%")
print(f"  Label:    {result2['label']}")
print(f"  Model:    {result2.get('model_version', 'unknown')}")
print(f"  Basis:    {result2.get('decision_basis', 'unknown')}")
print(f"  Reasoning: {result2['reasoning']}")

print("\n--- Results ---")
ai_pass = result1['ai_score'] > 70
human_pass = result2['ai_score'] < 30
print(f"  AI text scored > 70%:    {'PASS' if ai_pass else 'FAIL'} ({result1['ai_score']}%)")
print(f"  Human text scored < 30%: {'PASS' if human_pass else 'FAIL'} ({result2['ai_score']}%)")
print(f"  Using v2 classifier:     {'YES' if result1.get('decision_basis') == 'v2_classifier' else 'NO'}")

if ai_pass and human_pass:
    print("\n  ALL INTEGRATION TESTS PASSED!")
else:
    print("\n  SOME TESTS FAILED - review results above.")
