import gradio as gr
import requests
from openai import OpenAI
import os

# OpenAI client setup
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

# Function to send image to Flask service for analysis
def analyze_image_with_flask(image):
    url = "http://localhost:5000/analyze_image"
    files = {"image": open(image, "rb")}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        analysis_result = response.json()["analysis"]
        return analysis_result
    else:
        return "Error: Unable to process image"


# Function to handle GPT chat
def chat_with_gpt(history, user_message):
    # Convert chat history into a format GPT can understand
    messages = [{"role": "system", "content": "You are a helpful assistant who helps students with their homework."}]
    for message in history:
        role = "user" if message[0] else "assistant"
        messages.append({"role": role, "content": message[1]})

    # Add the latest user message
    messages.append({"role": "user", "content": user_message})

    # Call OpenAI GPT API
    response = client.chat.completions.create(
        model="gpt-4",  # Use your desired GPT model
        messages=messages
    )
    gpt_reply = response.choices[0].message.content

    # Update chat history
    history.append((True, user_message))  # User message
    history.append((False, gpt_reply))  # GPT response

    return history, gpt_reply


# Define the Gradio interface
with gr.Blocks() as demo:
    # File upload and analysis
    with gr.Row():
        image_input = gr.Image(type="filepath", label="Upload Homework Image")
        analysis_output = gr.Textbox(label="Analysis Result")

    submit_button = gr.Button("Submit")

    # Chat functionality
    with gr.Row():
        chatbot = gr.Chatbot(label="Homework Discussion")
        chat_input = gr.Textbox(label="Your Message", placeholder="Ask a question about the analysis...")
        chat_button = gr.Button("Send")

    # Workflow: Image analysis
    submit_button.click(analyze_image_with_flask, inputs=image_input, outputs=analysis_output)

    # Workflow: GPT chat
    chat_button.click(
        chat_with_gpt,
        inputs=[chatbot, chat_input],
        outputs=[chatbot, chat_input],
        show_progress='full'
    )

# Launch the Gradio app
demo.launch()
