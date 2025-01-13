import gradio as gr
import requests
import base64

# 后端 Flask API 地址
API_URL = "http://localhost:5000/ask"

def get_answer(question, uploaded_file):
    """
    调用后端 API 获取答案
    """
    if not question:
        return "请输入问题！"

    try:
        # 将上传的文件作为二进制数据并进行 Base64 编码
        if uploaded_file:
            file_content = base64.b64encode(uploaded_file).decode('utf-8')
        else:
            file_content = None

        # 调用后端 Flask API
        response = requests.post(API_URL, json={"question": question, "file_content": file_content})

        # 解析 JSON 响应
        data = response.json()

        if "answer" in data:
            return data['answer']
        elif "error" in data:
            return f"发生错误：{data['error']}"
    except Exception as e:
        return f"请求失败：{str(e)}"

# 创建 Gradio 界面
iface = gr.Interface(
    fn=get_answer,  # 调用后端 API 的函数
    inputs=[
        gr.Textbox(label="请输入问题", placeholder="在这里输入问题..."),  # 用户输入框
        gr.File(label="上传文档", type="binary")  # 上传文档，type="binary" 接受二进制数据
    ],
    outputs=gr.Textbox(label="AI 的回答"),  # 显示答案的文本框
    title="AI 学习助手",  # 界面标题
    description="输入问题并从 AI 获取答案。"  # 描述
)

# 启动界面
if __name__ == "__main__":
    iface.launch()
