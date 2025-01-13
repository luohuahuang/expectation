import os
import openai
from flask import Flask, request, jsonify

# 从环境变量中获取 OpenAI API 密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

# 创建 Flask 应用
app = Flask(__name__)

@app.route('/ask', methods=['POST'])
def answer_question():
    # 从请求中获取问题
    data = request.get_json()
    question = data.get('question', '')

    # 检查问题是否为空
    if not question:
        return jsonify({"error": "问题不能为空"}), 400

    model = data.get('model', 'gpt-4')  # 默认使用 gpt-4 模型

    try:
        # 使用 OpenAI API 调用 Chat Completion 接口
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个帮助小学学生解决学习问题的专业助手。"},
                {"role": "user", "content": question},
            ],
            temperature=0.7,  # 控制生成的随机性
            max_tokens=300,  # 限制回答的长度
        )

        # 提取并返回回答内容
        answer = response.choices[0].message.content.strip()

        # 设置正确的字符编码和响应头
        response_data = jsonify({"answer": answer})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data

    except openai.OpenAIError as e:
        response_data = jsonify({"error": f"OpenAI 错误：{str(e)}"})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data, 500
    except Exception as e:
        response_data = jsonify({"error": f"发生错误：{str(e)}"})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data, 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
