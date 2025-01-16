from flask import Flask, request, jsonify, render_template_string, redirect
import base64
import os
import sqlite3
from openai import OpenAI

app = Flask(__name__)

# OpenAI client setup
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")


# Initialize SQLite database
def initialize_database():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            uid INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_result TEXT NOT NULL,
            utime TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


initialize_database()


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


# Route for saving analysis results
@app.route("/save_analysis", methods=["POST"])
def save_analysis():
    data = request.json
    analysis_result = data.get("analysis_result")
    if not analysis_result:
        return jsonify({"message": "分析结果为空，无法保存！"}), 400

    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO analysis_results (analysis_result) VALUES (?)", (analysis_result,))
    conn.commit()
    conn.close()
    return jsonify({"message": "分析结果保存成功！"})


# CRUD 操作页面
@app.route("/history", methods=["GET", "POST"])
def history():
    conn = sqlite3.connect("results.db")
    cursor = conn.cursor()

    if request.method == "POST":
        # Handle delete operation
        uid = request.form.get("delete_uid")
        if uid:
            cursor.execute("DELETE FROM analysis_results WHERE uid = ?", (uid,))
            conn.commit()

    cursor.execute("SELECT uid, analysis_result, utime FROM analysis_results ORDER BY utime DESC")
    rows = cursor.fetchall()
    conn.close()

    # Render HTML template
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>分析结果历史记录</title>
    </head>
    <body>
        <h1>分析结果历史记录</h1>
        <table border="1">
            <tr>
                <th>ID</th>
                <th>分析结果</th>
                <th>更新时间</th>
                <th>操作</th>
            </tr>
            {% for row in rows %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
                <td>
                    <form method="post">
                        <input type="hidden" name="delete_uid" value="{{ row[0] }}">
                        <button type="submit">删除</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
        <a href="/">返回 Gradio 界面</a>
    </body>
    </html>
    """
    return render_template_string(html, rows=rows)


# 处理 GPT 聊天的函数
@app.route('/chat', methods=['POST'])
def chat_with_gpt():
    data = request.json
    history = data.get("history", [])
    user_message = data.get("user_message")
    analysis_result = data.get("analysis_result")

    if history is None:
        history = []

    # 将分析结果作为系统的初始消息
    messages = [
        {"role": "system", "content": f"你是一个帮助学生做作业的助手。分析结果是：{analysis_result}"}
    ]

    # 添加之前的聊天记录
    for sender, message in history:
        role = "user" if sender == "user" else "assistant"
        messages.append({"role": role, "content": message})

    # 添加用户的消息到对话中
    if user_message:
        messages.append({"role": "user", "content": user_message})

    # 调用 OpenAI 的 API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    gpt_reply = response.choices[0].message.content

    # 将用户的消息和 GPT 的回复添加到聊天记录中
    history.append(("assistant", gpt_reply))

    return jsonify({"history": history, "gpt_reply": gpt_reply})


if __name__ == "__main__":
    app.run(debug=True)
