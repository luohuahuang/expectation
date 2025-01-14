from flask import Flask, request, jsonify
import base64
import os
from openai import OpenAI

app = Flask(__name__)

# OpenAI client setup
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

# Route for image upload and processing
@app.route("/analyze_image", methods=["POST"])
def analyze_image():
    image_file = request.files["image"]
    image_path = "uploaded_image.png"  # Temporary file path
    image_file.save(image_path)  # Save the uploaded file

    # Getting the base64 string
    base64_image = encode_image(image_path)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "你是一位优秀的小学老师，你在辅导小学生写作业方面有丰富的经验。"},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "这种图片的内容是一个小学生的家庭作业。\n图片里面包含了什么内容？请问可以总结一下图片里面的内容。\n具体分析一下里面有哪些题目是做错的？对于做错的题目，最好可以提出学习的建议\n。回答的最后，请用可读性比较强的方式（比如表格）展示所包含的原始内容",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ],
            }
        ],
    )

    print(response.choices[0])
    # Extract relevant content from the response
    analysis_content = response.choices[0].message.content  # Use dot notation

    # Return the result as a JSON serializable string
    return jsonify({"analysis": analysis_content})


if __name__ == "__main__":
    app.run(debug=True)
