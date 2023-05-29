from flask import Flask, render_template, request
import nltk
from nltk.tokenize import word_tokenize
from bardapi import Bard
from PyPDF2 import PdfReader
from io import BytesIO



nltk.download('punkt')

# Set up your Bard API credentials
token = "..."

app = Flask(__name__)

bard = Bard(token=token)


class Document:
    def __init__(self, text):
        self.page_content = text
        self.metadata = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/query", methods=["POST"])
def query():
    files = request.files.getlist("files")  # Get list of files
    query = request.form.get("query")
    responses = []

    # Check if any files were uploaded
    if not files:
        try:
            response = bard.get_answer(f"Query: {query}")
            responses.append(response['content'])
        except Exception as e:
            print(f"Query failed: {query}. Skipping...")
    else:
        for file in files:
            if file.filename.endswith('.pdf'):
                # For PDF files, use PdfReader to extract text
                pdf = PdfReader(BytesIO(file.read()))
                content = ""
                for page in pdf.pages:
                    content += page.extract_text()
            else:
                # For TXT files, just read the content
                content = file.read().decode("utf-8")

            tokens = word_tokenize(content)
            chunks = [' '.join(tokens[i:i + 2048]) for i in range(0, len(tokens), 2048)]
            documents_tokenized = [Document(chunk) for chunk in chunks]

            for document in documents_tokenized:
                try:
                    response = bard.get_answer(f"{document.page_content}\n\nQuery: {query}")
                    responses.append(response['content'])
                except Exception as e:
                    print(f"Query was too large for document: {document}. Skipping...")

    query_result = '\n'.join(responses)

    return render_template("query_result.html", result=query_result)

if __name__ == "__main__":
    app.run(debug=True)
