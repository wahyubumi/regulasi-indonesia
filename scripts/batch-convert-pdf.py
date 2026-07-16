import os
import glob
import time
import google.generativeai as genai
from pathlib import Path

# Konfigurasi Path
ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "pdf-local" / "downloads"
STAGING_DIR = ROOT / "staging" / "incoming"
PROMPT_FILE = ROOT / "prompts" / "PROMPT-REGULATION-TO-MARKDOWN-PAGE-EN.md"

def process_pdf(pdf_path: Path, model):
    print(f"Mulai memproses: {pdf_path.name}...")
    
    # Upload file ke Gemini
    uploaded_file = genai.upload_file(path=str(pdf_path))
    
    try:
        time.sleep(2) 
        response = model.generate_content([
            "Please convert this regulation PDF to markdown based on the system instructions.", 
            uploaded_file
        ])
        
        markdown_text = response.text
        
        output_filename = pdf_path.stem + ".md"
        output_path = STAGING_DIR / output_filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown_text)
            
        print(f"✅ Selesai: Disimpan ke {output_path}")
        
    except Exception as e:
        print(f"❌ Error memproses {pdf_path.name}: {e}")
    finally:
        genai.delete_file(uploaded_file.name)

def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Environment variable GEMINI_API_KEY tidak ditemukan.")
        print("Jalankan dengan: GEMINI_API_KEY='kunci_api_anda' python3 scripts/batch-convert-pdf.py")
        return

    genai.configure(api_key=api_key)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro-latest",
        system_instruction=system_prompt
    )

    pdf_files = list(PDF_DIR.glob("*.pdf"))
    
    if not pdf_files:
        print("Tidak ada file PDF ditemukan di pdf-local/downloads/")
    else:
        print(f"Ditemukan {len(pdf_files)} file PDF. Memulai konversi batch...")
        for pdf in pdf_files:
            # Lewati jika file markdown sudah ada
            output_filename = pdf.stem + ".md"
            output_path = STAGING_DIR / output_filename
            if output_path.exists():
                print(f"Lewati {pdf.name}, sudah dikonversi.")
                continue
            
            process_pdf(pdf, model)
            time.sleep(5) # Delay 5 detik untuk menghindari rate limit

if __name__ == "__main__":
    main()
