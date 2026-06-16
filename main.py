import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
import json
import re
from datetime import datetime

# 重新加载日志 (用于在终端观察页面重载情况)
print("\nReload this file\n")

# ==========================================
# 0. 页面全局配置
# ==========================================
st.set_page_config(
    page_title="AI Chat",
    page_icon="👽",
    layout="wide",  # 使用宽屏模式，充分利用屏幕空间
    initial_sidebar_state="expanded",  # 默认展开侧边栏
    menu_items={}
)

# 标题与 Logo
st.title("AI Chat")
st.logo("🧀")

# ==========================================
# 1. 常量定义 (Constants)
# ==========================================
# 提取魔法字符串，方便后期统一修改和维护 (DRY 原则)
DEFAULT_SESSION_NAME = "Default session"
DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."


# ==========================================
# 2. 核心逻辑函数定义 (Functions)
# ==========================================
def sanitize_filename(name):
    return re.sub(r'[^\w\-]', '_', name)


def save_session(current_sys_prompt):
    """
    保存当前对话到本地 JSON 文件。
    只有在发生了“实质性改变”时才执行保存，避免生成大量垃圾空文件。
    """
    # 检查是否满足保存的三个条件之一
    has_messages = len(st.session_state.messages) > 0  # 有聊天记录
    name_changed = st.session_state.base_session_name != DEFAULT_SESSION_NAME  # 改了会话名
    prompt_changed = current_sys_prompt != DEFAULT_SYSTEM_PROMPT  # 改了提示词

    if st.session_state.current_session and (has_messages or name_changed or prompt_changed):
        # 将当前状态打包成字典
        session_data = {
            "session_name": st.session_state.current_session,
            "base_session_name": st.session_state.base_session_name,  # 独立保存基础名，方便日后加载
            "session_timestamp": st.session_state.session_timestamp,  # 独立保存时间戳
            "session_messages": st.session_state.messages,
            "system_prompt": current_sys_prompt
        }

        # 确保 sessions 文件夹存在
        if not os.path.exists("sessions"):
            os.mkdir("sessions")

        # 写入 JSON 文件
        file_path = f"sessions/{st.session_state.current_session}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)

        print(f"Session saved to: {file_path}")


def generate_session_name():
    """生成安全的时间戳字符串，用于拼接文件名"""
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def handle_new_chat():
    """
    【回调函数】处理点击“New Chat”按钮的逻辑。
    在 Streamlit 重新渲染页面之前执行，确保状态重置不会报错。
    """
    # 1. 尝试保存当前正在进行的对话
    save_session(st.session_state.sys_prompt_key)
    # 2. 清空各种状态，恢复到出厂默认值
    st.session_state.messages = []
    st.session_state.session_timestamp = generate_session_name()
    st.session_state.base_session_name = DEFAULT_SESSION_NAME
    st.session_state.sys_prompt_key = DEFAULT_SYSTEM_PROMPT


def load_sessions():
    """读取 sessions 文件夹，返回按时间排序的历史会话列表"""
    session_list = []
    if os.path.exists("sessions"):
        file_list = os.listdir("sessions")
        # 按照文件的最后修改时间降序排序，让最新的对话排在最前面
        file_list.sort(key=lambda x: os.path.getmtime(os.path.join("sessions", x)), reverse=True)
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])  # 去掉 .json 后缀
    return session_list


def load_session_callback(session_name):
    """
    【回调函数】加载指定的历史会话。
    """
    try:
        # 核心防丢机制：加载历史记录前，先把当前屏幕上的对话存起来
        save_session(st.session_state.sys_prompt_key)

        file_path = f"sessions/{session_name}.json"
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                session_data = json.load(f)

                # 使用 .get() 方法安全读取数据，防止旧版本 JSON 缺少某些键导致 KeyError
                st.session_state.messages = session_data.get("session_messages", [])
                st.session_state.sys_prompt_key = session_data.get("system_prompt", DEFAULT_SYSTEM_PROMPT)

                # 恢复基础名称和时间戳（兼容新老版本的数据格式）
                if "base_session_name" in session_data and "session_timestamp" in session_data:
                    st.session_state.base_session_name = session_data["base_session_name"]
                    st.session_state.session_timestamp = session_data["session_timestamp"]
                else:
                    # 针对旧版没有拆分名字的数据做的兼容处理
                    parts = session_data.get("session_name", "").rsplit(" - ", 1)
                    if len(parts) == 2:
                        st.session_state.base_session_name = parts[0]
                        st.session_state.session_timestamp = parts[1]

    except Exception as e:
        st.error(f"Load session failed! Error: {e}")


def delete_session_callback(session_name):
    """
    【回调函数】删除指定的历史会话。
    """
    file_path = f"sessions/{session_name}.json"
    if os.path.exists(file_path):
        os.remove(file_path)  # 物理删除文件

        # 如果用户刚刚删掉的，正好是他当前屏幕上正在看的对话
        # 就必须把屏幕清空，重置为新建状态，防止出现"幽灵对话"
        if st.session_state.current_session == session_name:
            st.session_state.messages = []
            st.session_state.base_session_name = DEFAULT_SESSION_NAME
            st.session_state.session_timestamp = generate_session_name()
            st.session_state.sys_prompt_key = DEFAULT_SYSTEM_PROMPT


# ==========================================
# 3. 状态初始化 (Session State Init)
# ==========================================
# 如果某个状态不存在于 session_state 中，则为其赋初始值。
# 这是 Streamlit 保持状态不被刷新的核心机制。

if "messages" not in st.session_state:
    st.session_state.messages = []  # 存放聊天记录的列表

if "base_session_name" not in st.session_state:
    st.session_state.base_session_name = DEFAULT_SESSION_NAME  # 基础会话名

if "session_timestamp" not in st.session_state:
    st.session_state.session_timestamp = generate_session_name()  # 当前会话的专属时间戳

if "sys_prompt_key" not in st.session_state:
    st.session_state.sys_prompt_key = DEFAULT_SYSTEM_PROMPT  # 系统提示词

# 动态拼接完整的会话名 (因为上面的 base_session_name 可能会随时被 UI 修改)
st.session_state.current_session = f"{st.session_state.base_session_name} - {st.session_state.session_timestamp}"

# 初始化大模型 API 客户端
api_key = os.environ.get("DEEPSEEK_API_KEY")
if not api_key:
    st.error("DEEPSEEK_API_KEY is not configured.")
    st.stop()  # 如果没有配置 Key，立刻停止运行程序

# 注意：这里配置了 base_url 从而兼容 OpenAI 的 SDK 来调用 DeepSeek
client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com")

# ==========================================
# 4. 侧边栏渲染 (Sidebar UI)
# ==========================================
with st.sidebar:
    st.subheader("Model Setting")

    # 绑定了 key，用户输入的内容会瞬间同步到 st.session_state.base_session_name
    st.text_input("Session Name", key="base_session_name", placeholder="Please input session name")

    # 输入框可能会修改基础名，这里再次拼接确保当前名称是最新的
    st.session_state.current_session = f"{st.session_state.base_session_name} - {st.session_state.session_timestamp}"

    # 系统提示词输入框
    st.text_area("System Prompt", key="sys_prompt_key", placeholder="Please input system prompt")

    st.subheader("Control Panel")

    # 新建对话按钮：通过 on_click 绑定回调函数
    st.button("New Chat", width="stretch", icon="🆕", on_click=handle_new_chat)

    st.text("Chat History")
    session_list = load_sessions()

    # 动态渲染历史记录列表
    for session in session_list:
        # 将侧边栏横向切分为比例为 6:1 的两列，前面放加载按钮，后面放删除按钮
        col1, col2 = st.columns([6, 1])
        with col1:
            # args 参数用于向回调函数传递参数（注意必须是元组，所以有个逗号）
            # type="primary" 可以高亮显示当前正在查看的会话按钮，增强用户体验
            st.button(session, width="stretch", icon="🫧", key=f"load_{session}",
                      on_click=load_session_callback, args=(session,),
                      type="primary" if session == st.session_state.current_session else "secondary")
        with col2:
            st.button("", width="stretch", icon="❌", key=f"del_{session}",
                      on_click=delete_session_callback, args=(session,))

# ==========================================
# 5. 主聊天界面渲染与交互 (Main UI & Chat)
# ==========================================
# 在界面顶部显示当前的会话全名
st.caption(f"Current Session: {st.session_state.current_session}")

# 遍历并显示已有的历史聊天记录
for message in st.session_state.messages:
    st.chat_message(message["role"]).write(message["content"])

# 渲染底部的聊天输入框，并等待用户输入
prompt = st.chat_input("What do you want to know?")

if prompt:  # 当用户输入内容并回车后
    # 1. 立即在屏幕上显示用户的提问
    st.chat_message("user").write(prompt)
    # 2. 将提问存入全局记忆中
    st.session_state.messages.append({"role": "user", "content": prompt})
    print("---> prompt: ", prompt)

    # 3. 组装上下文并向大模型发送请求
    try:
        response = client.chat.completions.create(
            model="deepseek-v4-pro",
            messages=[
                {"role": "system", "content": st.session_state.sys_prompt_key},  # 注入系统提示词
                *st.session_state.messages  # 解包所有历史消息
            ],
            stream=True,  # 开启流式输出 (打字机效果)
            # reasoning_effort="high",
            # extra_body={"thinking": {"type": "enabled"}}
        )
    except Exception as e:
        st.error(f"API request failed: {e}")
        st.stop()

    # 4. 创建一个空的占位符，用于实时渲染流式返回的文字
    response_message = st.empty()
    full_response = ""

    # 5. 循环读取流式数据包
    for chunk in response:
        # 防错机制：确保解析的数据包里真的有文本内容
        if not chunk.choices or len(chunk.choices) == 0:
            continue
        delta = chunk.choices[0].delta
        if delta is None:
            continue
        if hasattr(delta, 'content') and delta.content is not None:
            content = delta.content
            full_response += content
            # 不断覆盖占位符，形成打字机效果
            response_message.chat_message("assistant").write(full_response)

    # 6. 回答完毕后，将完整的 AI 回复存入全局记忆中
    st.session_state.messages.append({"role": "assistant", "content": full_response})