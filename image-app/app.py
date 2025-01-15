import gradio as gr
import requests
from openai import OpenAI
import os

# OpenAI 客户端设置
client = OpenAI()
client.api_key = os.getenv("OPENAI_API_KEY")

# 发送图片到 Flask 服务进行分析的函数
def analyze_image_with_flask(image):
    url = "http://localhost:5000/analyze_image"
    files = {"image": open(image, "rb")}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        analysis_result = response.json()["analysis"]
        return analysis_result
    else:
        return "错误：无法处理图片"

# 处理 GPT 聊天的函数
def chat_with_gpt(history, user_message, analysis_result):
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
    messages.append({"role": "user", "content": user_message})

    # 调用 OpenAI 的 API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages
    )
    gpt_reply = response.choices[0].message.content

    # 将用户的消息和 GPT 的回复添加到聊天记录中
    history.append(("assistant", gpt_reply))

    return history, ""  # 清空输入框

# 定义 Gradio 界面
with gr.Blocks() as demo:
    with gr.Row():
        # 左侧：上传图片的 dialog
        with gr.Column():
            image_input = gr.Image(type="filepath", label="上传作业图片")

        # 右侧：包含分析结果和提交按钮的 column
        with gr.Column():
            with gr.Row():
                # 右上角：分析结果 dialog
                analysis_output = gr.Textbox(label="分析结果")
            with gr.Row():
                # 右下角：提交按钮
                submit_button = gr.Button("提交")

    # 第二行布局：作业分析与聊天
    with gr.Row():
        # 左侧：作业分析 dialog
        with gr.Column():
            chatbot = gr.Chatbot(label="作业分析")

        # 右侧：聊天框和发送按钮
        with gr.Column():
            with gr.Row():
                # 右上角：你的消息
                chat_input = gr.Textbox(label="你的消息", placeholder="就分析结果提问...")
            with gr.Row():
                # 右下角：发送按钮
                chat_button = gr.Button("发送")

    # 工作流程：图片分析
    submit_button.click(analyze_image_with_flask, inputs=image_input, outputs=analysis_output)

    # 工作流程：GPT 聊天
    chat_button.click(
        chat_with_gpt,
        inputs=[chatbot, chat_input, analysis_output],
        outputs=[chatbot, chat_input],
        show_progress='full'
    )

# 启动 Gradio 应用
demo.launch()
