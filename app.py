from flask import Flask, request, jsonify, render_template
from openai import OpenAI
import csv

app = Flask(__name__)

# Initialize OpenAI client
client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")

# Initial chat history
history = [
    {"role": "system",
     "content": "You are a dynamic survey system that adapts questions based on previous responses. Ask the user about the survey topic first, then continue asking questions related to the topic. Limit the survey to 4 answers. do not give analysis of users answer just ask the next question without any text before the question after user gives the answer.(ask short and meaningfull questions)"}
]

# File paths
txt_file_path = 'survey_responses.txt'
csv_file_path = 'survey_responses.csv'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/start_chat', methods=['POST'])
def start_chat():
    global history
    # Reset history for new chat
    history = [
        {"role": "system",
         "content": "You are a dynamic survey system that adapts questions based on previous responses. Ask the user about the survey topic first, then continue asking questions related to the topic. Limit the survey to 5 answers. do not give analysis of users answer just ask the next question without any text before the question after user gives the answer.(ask short and meaningfull questions)"}
    ]

    return jsonify({"message": "Welcome to the survey chat. Please provide the topic of the survey to begin."})


@app.route('/get_response', methods=['POST'])
def get_response():
    global history
    user_message = request.json.get('message', '')

    # Ensure only up to 5 questions are asked
    if len([msg for msg in history if msg['role'] == 'user']) >= 5:
        save_responses_to_file(history)
        return jsonify({"response": "Survey completed. Thank you for your responses."})

    # Append the user's message to the history
    history.append({"role": "user", "content": user_message})

    completion = client.chat.completions.create(
        model="bartowski/Meta-Llama-3.1-8B-Instruct-GGUF",
        messages=history,
        temperature=2.0,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}
    for chunk in completion:
        if chunk.choices[0].delta.content:
            new_message["content"] += chunk.choices[0].delta.content

    # Append the assistant's response to history
    history.append(new_message)
    return jsonify({"response": new_message["content"].strip()})


def save_responses_to_file(history):
    qa_pairs = [(history[i]['content'], history[i + 1]['content']) for i in range(1, len(history) - 1, 2)]

    # Save to TXT file
    with open(txt_file_path, 'a') as txt_file:
        for question, answer in qa_pairs:
            txt_file.write(f"A: {question}\nQ: {answer}\n\n")

    # Save to CSV files
    with open(csv_file_path, 'a', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Answer", "Question"])
        for question, answer in qa_pairs:
            writer.writerow([question, answer])

if __name__ == '__main__':
    app.run(debug=True)