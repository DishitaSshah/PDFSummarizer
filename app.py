from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Google Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Ensure 'uploads' directory exists
if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Summarization Function
def summarize_text(text):
    model = genai.GenerativeModel("gemini-1.5-pro")
    response = model.generate_content(f"Summarize this:\n\n{text}")
    return response.text if response else "No summary generated."

# Read PDFs
def read_pdf(file_path):
    text = ""
    with open(file_path, "rb") as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

# Read CSVs
def read_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_string(index=False)

# Homepage Route
@app.route("/")
def index():
    return render_template("index.html", user=session.get("user"), history=session.get("history", []))



# Upload & Summarize File (Requires Login)
@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))
    
    file = request.files["file"]
    
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))
    
    if file and (file.filename.endswith(".pdf") or file.filename.endswith(".csv")):
        file_path = os.path.join("uploads", secure_filename(file.filename))
        file.save(file_path)
        
        try:
            text = read_pdf(file_path) if file.filename.endswith(".pdf") else read_csv(file_path)
            summary = summarize_text(text)

            # Store summary in session (History Feature)
            if "history" not in session:
                session["history"] = []
            session["history"].append({"file": file.filename, "summary": summary})
        
        finally:
            os.remove(file_path)
        
        return render_template("index.html", user=session["user"], summary=summary, history=session["history"])
    
    else:
        flash("Unsupported file type. Please upload a PDF or CSV file.")
        return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
