import os
import openai
import faiss
import numpy as np
import base64
import io
import logging
from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS

# 从环境变量中获取 OpenAI API 密钥
openai.api_key = os.getenv("OPENAI_API_KEY")

# 创建 Flask 应用
app = Flask(__name__)

# 设置日志记录
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化 FAISS 索引和嵌入模型
index = None
embeddings = OpenAIEmbeddings()
texts = []  # 用于存储文档的文本

def process_uploaded_pdf(file_content):
    """
    将 Base64 编码的文件内容解码，并提取 PDF 文本内容
    """
    logger.info("开始处理上传的 PDF 文件")

    try:
        file_content = base64.b64decode(file_content)  # 解码 Base64 内容
        file_stream = io.BytesIO(file_content)  # 将 bytes 数据转换为 BytesIO 对象
        reader = PdfReader(file_stream)
        full_text = ""

        # 提取 PDF 中的所有文本
        for page in reader.pages:
            full_text += page.extract_text()

        # 将文本分割为段落，并存储文本
        global texts
        texts = full_text.split("\n")

        logger.debug(f"提取的文本内容：{full_text[:500]}...")  # 打印前500个字符，避免过长

        # 使用 LangChain 的嵌入模型，将文本分割为片段并生成向量
        embeddings_list = embeddings.embed_documents(texts)

        # 创建 FAISS 索引
        global index
        dimension = len(embeddings_list[0])
        index = faiss.IndexFlatL2(dimension)
        index.add(np.array(embeddings_list, dtype=np.float32))

        logger.info("PDF 文档处理完成并生成 FAISS 索引")

    except Exception as e:
        logger.error(f"处理 PDF 文件时出错: {str(e)}")
        raise

def retrieve_relevant_documents(question):
    """
    使用 FAISS 检索与问题相关的文档片段
    """
    logger.info(f"开始检索与问题相关的文档: {question}")

    try:
        # 将问题转换为嵌入向量
        question_embedding = embeddings.embed_query(question)

        # 在 FAISS 中进行检索
        _, indices = index.search(np.array([question_embedding], dtype=np.float32), k=10)  # k=3表示返回最相关的3个片段

        # 获取检索到的文本
        relevant_texts = [texts[idx] for idx in indices[0]]  # 从 texts 中获取相应的文档片段

        logger.debug(f"检索到的相关文档片段：{relevant_texts}")
        return "\n".join(relevant_texts)

    except Exception as e:
        logger.error(f"检索相关文档时出错: {str(e)}")
        raise

@app.route('/ask', methods=['POST'])
def answer_question():
    # 从请求中获取问题和文件内容
    data = request.get_json()
    question = data.get('question', '')
    file_content = data.get('file_content', None)

    logger.info(f"收到的问题：{question}")

    # 检查问题是否为空
    if not question:
        logger.error("问题不能为空")
        return jsonify({"error": "问题不能为空"}), 400

    # 如果有上传的文件内容，处理文件
    if file_content:
        logger.info("文件内容已上传，开始处理文件...")
        try:
            process_uploaded_pdf(file_content)  # 处理文件并生成 FAISS 索引
        except Exception as e:
            logger.error(f"处理文件时出错: {str(e)}")
            return jsonify({"error": f"处理文件时出错: {str(e)}"}), 500

    # 使用 FAISS 检索相关文档
    try:
        retrieved_documents = retrieve_relevant_documents(question)
    except Exception as e:
        logger.error(f"检索相关文档时出错: {str(e)}")
        return jsonify({"error": f"检索相关文档时出错: {str(e)}"}), 500

    # 结合检索到的文档和问题生成模型的提示
    prompt = f"问题：{question}\n相关文档：{retrieved_documents}"

    try:
        logger.info("调用 OpenAI API 获取回答...")
        # 使用 OpenAI API 调用 Chat Completion 接口
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是一个帮助小学学生解决学习问题的专业助手。"},
                {"role": "user", "content": prompt},  # 将问题和检索到的文档作为上下文
            ],
            temperature=0.7,  # 控制生成的随机性
            max_tokens=300,  # 限制回答的长度
        )

        # 提取并返回回答内容
        answer = response.choices[0].message.content.strip()

        logger.info("OpenAI API 调用成功，返回回答。")

        # 设置正确的字符编码和响应头
        response_data = jsonify({"answer": answer})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data

    except openai.OpenAIError as e:
        logger.error(f"OpenAI 错误：{str(e)}")
        response_data = jsonify({"error": f"OpenAI 错误：{str(e)}"})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data, 500
    except Exception as e:
        logger.error(f"发生错误：{str(e)}")
        response_data = jsonify({"error": f"发生错误：{str(e)}"})
        response_data.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response_data, 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
