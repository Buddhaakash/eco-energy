"""
Checks, step by step, why bill reading might be failing, and prints the
real error instead of hiding it.

Run from the project folder (with the venv active):
    python diagnose_bill.py "current bill\\Electricity-Bill.png"
"""
import sys
import traceback
from pathlib import Path

MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".webp": "image/webp", ".pdf": "application/pdf"}


def main():
    if len(sys.argv) < 2:
        print('Usage: python diagnose_bill.py "path\\to\\your\\bill.png"')
        return
    path = Path(sys.argv[1].strip('"'))
    print(f"1. Bill file found: {path.exists()}  ({path})")
    if not path.exists():
        return

    from backend.config import settings
    print(f"2. API key loaded from .env: {bool(settings.AI_API_KEY)}   model name: {settings.AI_MODEL}")
    if not settings.AI_API_KEY:
        print("   -> PROBLEM: AI_API_KEY is empty. Open the .env file and paste your key after AI_API_KEY=")
        return

    try:
        import google.generativeai as genai
        print("3. google-generativeai package installed: yes")
    except Exception:
        print("3. google-generativeai package installed: NO")
        print("   -> run:  pip install google-generativeai")
        traceback.print_exc()
        return

    genai.configure(api_key=settings.AI_API_KEY)

    print("4. Models your key can use:")
    try:
        names = [m.name for m in genai.list_models()
                 if "generateContent" in m.supported_generation_methods]
        for n in names[:15]:
            print("   -", n)
        for wanted in [m.strip() for m in settings.AI_MODEL.split(",") if m.strip()]:
            if "models/" + wanted not in names:
                print(f"   -> NOTE: '{wanted}' is not in this list (it may still work, step 5 will tell).")
    except Exception:
        print("   -> Could not list models (key invalid or no internet?):")
        traceback.print_exc()
        return

    print("5. Sending the bill to each model in AI_MODEL...")
    working = []
    for name in [m.strip() for m in settings.AI_MODEL.split(",") if m.strip()]:
        try:
            model = genai.GenerativeModel(name)
            resp = model.generate_content([
                "Reply with just the total amount payable on this bill.",
                {"mime_type": MIME.get(path.suffix.lower(), "image/png"), "data": path.read_bytes()},
            ])
            print(f"   OK    {name} -> AI replied: {resp.text.strip()[:80]}")
            working.append(name)
        except Exception as e:
            first_line = str(e).strip().splitlines()[0][:200]
            print(f"   FAIL  {name} -> {first_line}")
    if not working:
        print("   -> PROBLEM: none of your models worked. Pick other names from the list in step 4.")
        return

    print("6. Running the app's own bill reader...")
    try:
        from backend.services.bill_extraction_service import extract_bill_fields
        result = extract_bill_fields(path.read_bytes(), path.name)
        print("   ", result)
    except Exception:
        print("   -> PROBLEM inside the app's bill reader. Full error:")
        traceback.print_exc()


if __name__ == "__main__":
    main()
