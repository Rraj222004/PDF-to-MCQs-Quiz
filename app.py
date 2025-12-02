from flask import Flask, render_template, request
import pdfplumber
import re
import json
import random
import os

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
    """
    Expected format:

    1. Question text...
    a) option1
    b) option2
    c) option3
    d) option4
    Answer: b
    """
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

        # options from form
        num_q_str = request.form.get("num_questions", "all")
        shuffle_flag = request.form.get("shuffle") == "on"

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

        # shuffle if requested
        if shuffle_flag:
            random.shuffle(questions)

        # limit number of questions
        if num_q_str.lower() != "all":
            try:
                n = int(num_q_str)
                questions = questions[:n]
            except ValueError:
                pass  # ignore and keep all

        questions_json = json.dumps(questions)
        return render_template(
            "quiz.html",
            questions_json=questions_json,
        )

    return render_template("index.html")


if __name__ == "__main__":
    # ready for local & deployment
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
