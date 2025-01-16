import io

import gradio as gr
import requests
from PIL import Image


# 压缩图片质量函数
def compress_image_quality(image_file, quality=80):
    img = Image.open(image_file)
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG', quality=quality)
    img_byte_arr.seek(0)
    return img_byte_arr


# 发送图片到 Flask 服务进行分析的函数
def analyze_image_with_flask(image):
    # 压缩图片
    compressed_image = compress_image_quality(image, quality=75)

    # 将压缩后的图片传给 Flask 服务
    url = "http://localhost:5000/analyze_image"
    files = {"image": compressed_image}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        analysis_result = response.json()["analysis"]
        return analysis_result
    else:
        return "错误：无法处理图片"


# 发送请求到 Flask 后端保存分析结果
def save_analysis_with_flask(analysis_result):
    url = "http://localhost:5000/save_analysis"
    data = {"analysis_result": analysis_result}
    response = requests.post(url, json=data)

    if response.status_code == 200:
        return response.json().get("message", "分析结果保存成功！")
    else:
        return response.json().get("message", "分析结果保存失败！")


# 发送请求到 Flask 后端处理 GPT 聊天
def chat_with_gpt_api(history, user_message, analysis_result):
    url = "http://localhost:5000/chat"
    data = {
        "history": history,
        "user_message": user_message,
        "analysis_result": analysis_result
    }
    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        return result["history"], ""  # 返回聊天记录和清空输入框
    else:
        return "Error: Unable to process the request", ""


# 定义 Gradio 界面
with gr.Blocks(css="""
#image-input .image-container {
    width: 300px; /* 固定宽度 */
    height: 300px; /* 固定高度 */
    overflow: hidden; /* 隐藏溢出内容 */
    display: flex;
    align-items: center;
    justify-content: center;
}

#image-input img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain; /* 自适应图片显示 */
}
""") as demo:
    # 第一行：图片上传和分析
    with gr.Group():
        with gr.Row():
            # 左侧：上传图片的 dialog
            with gr.Column():
                image_input = gr.Image(type="filepath", label="上传作业图片", elem_id="image-input")

            # 右侧：包含分析结果和提交按钮的 column
            with gr.Column():
                with gr.Row():
                    # 右上角：分析结果 dialog
                    analysis_output = gr.Textbox(label="分析结果")
                with gr.Row():
                    # 右下角：提交和保存按钮
                    submit_button = gr.Button("提交")
                    save_button = gr.Button("保存")

    # 第二行：作业分析与聊天
    with gr.Group():
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

    # Save button logic
    save_button.click(save_analysis_with_flask, inputs=analysis_output, outputs=analysis_output)

    # 工作流程：GPT 聊天
    chat_button.click(
        chat_with_gpt_api,
        inputs=[chatbot, chat_input, analysis_output],
        outputs=[chatbot, chat_input],
        show_progress='full'
    )

# 启动 Gradio 应用
demo.launch(share=True)
