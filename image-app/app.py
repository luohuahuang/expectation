import gradio as gr
import requests

# Function to send image to Flask service
def analyze_image_with_flask(image):
    url = "http://localhost:5000/analyze_image"
    files = {"image": open(image, "rb")}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        return response.json()["analysis"]
    else:
        return "Error: Unable to process image"

# Create Gradio interface
iface = gr.Interface(
    fn=analyze_image_with_flask,
    inputs=gr.Image(type="filepath"),  # Change to "filepath"
    outputs="text",
    live=False,  # Set live=False so that analysis only happens on submit
    allow_flagging="never",  # Optionally disable flagging if not needed
)

# Launch the Gradio interface
iface.launch()
