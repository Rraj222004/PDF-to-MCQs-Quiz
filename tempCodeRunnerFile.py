from flask import Flask, render_template, request
import pdfplumber
import re
import json

app = Flask(__name__)

# ------------ PDF → TEXT ------------

def extract_text_from_pdf_file(file_obj):
    text = ""
    with pdfplumber.open(file_obj) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# ------------ TEXT → MCQS ------------

def parse_mcqs(raw_text: str):
    pattern = re.compile(
        r"(?P<number>\d+)\.\s*(?P<question>.*?)\n"
        r"a\)\s*(?P<a>.*?)\n"
        r"b\)\s*(?P<b>.*?)\n"
        r"c\)\s*(?P<c>.*?)\n"
        r"d\)\s*(?P<d>.*?)\n"
        r"(?:Answer|Ans|nswer)\s*[:\-]\s*(?P<ans>[a-dA-D])",
        re.DOTALL,
    )

    questions = []
    for match in pattern.finditer(raw_text):
        gd = match.groupdict()
        questions.append(
            {
                "number": int(gd["number"]),
                "question": gd["question"].strip(),
                "options": [
                    gd["a"].strip(),
                    gd["b"].strip(),
                    gd["c"].strip(),
                    gd["d"].strip(),
                ],
                "answer": gd["ans"].upper().strip(),  # A/B/C/D
            }
        )
    return questions

# ------------ ROUTES ------------

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        uploaded_file = request.files.get("pdf")
        if not uploaded_file:
            return render_template("index.html", error="Please upload a PDF file.")

        try:
            raw_text = extract_text_from_pdf_file(uploaded_file)
            questions = parse_mcqs(raw_text)
        except Exception as e:
            return render_template("index.html", error=f"Error reading PDF: {e}")

        if not questions:
            return render_template(
                "index.html",
                error="No questions found. Check the format of the PDF.",
            )

        # Convert to JSON string for JavaScript
        questions_json = json.dumps(questions)
        return render_template("quiz.html", questions_json=questions_json)

    return render_template("index.html")


if __name__ == "__main__":
    # host='0.0.0.0' so other devices on same Wi-Fi can open it
    app.run(host="0.0.0.0", port=5000, debug=True)
