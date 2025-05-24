import time
import openai
import streamlit as st
from uuid import uuid4

# MODEL CONFIGURATION
# TODO: Please replace the following with your own OpenAI API keys
qwen_OPENAI_API_KEY = "sk-20b4e293dc524e6ca819d9b37e2cadd2"
qwen_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
qwen_kind = "qwen-turbo"
qwen_name = "通义千问"

deepseek_OPENAI_API_KEY ="sk-9aedc4c44eb14c1da848f04cfccacb39"
deepseek_url = "https://api.deepseek.com"
deepseek_kind = "deepseek-chat"
deepseek_name = "deepseek"

# 模型配置信息
models_info = (
    {"kind": qwen_kind, "name": qwen_name, "api_key": qwen_OPENAI_API_KEY, "url": qwen_url},
    {"kind": deepseek_kind, "name": deepseek_name, "api_key": deepseek_OPENAI_API_KEY, "url":deepseek_url}
)

# 初始化所有对话结构
def init_conversations():
    if "conversations" not in st.session_state:
        st.session_state["conversations"] = {}
    if "active_chat" not in st.session_state:
        st.session_state["active_chat"] = {}

    for model in models_info:
        kind = model["kind"]
        if kind not in st.session_state["conversations"]:
            st.session_state["conversations"][kind] = {}
        # 创建默认聊天窗口
        if kind not in st.session_state["active_chat"]:
            new_id = create_new_chat(kind)
            st.session_state["active_chat"][kind] = new_id

# 创建新对话窗口
def create_new_chat(kind):
    chat_id = f"chat_{uuid4().hex[:6]}"
    st.session_state["conversations"][kind][chat_id] = [{'role': 'system', 'content': 'You are a helpful assistant.'}]
    st.session_state["active_chat"][kind] = chat_id
    st.session_state["last_created_chat"] = chat_id
    return chat_id

# 获取模型响应
def get_response(model_index, messages, temperature=1):
    model = models_info[model_index]
    client = openai.OpenAI(
        api_key=model["api_key"], 
        base_url=model["url"]
    )
    completion = client.chat.completions.create(
        model=model["kind"],
        messages=messages,
        temperature=temperature
    )
    return completion.choices[0].message.content

# 提交对话
def ask_model(model_index, user_input, temperature):
    kind = models_info[model_index]['kind']
    chat_id = st.session_state["active_chat"][kind]
    messages = st.session_state["conversations"][kind][chat_id]

    # 判断是否是新提问
    last_user_input = st.session_state.get('last_user_input', '')
    is_new_query = (user_input != last_user_input)
    st.session_state['last_user_input'] = user_input

    messages.append({'role': 'user', 'content': user_input})
    response = get_response(model_index, messages, temperature)
    messages.append({'role': 'assistant', 'content': response})

    return is_new_query
 
# 获取聊天窗口标题
def get_chat_display_titles(kind):
    display_map = {}
    for cid, messages in st.session_state["conversations"][kind].items():
        first_user = next((m["content"] for m in messages if m["role"] == "user"), None)
        display_name = first_user if first_user else "新对话"
        # 若有多个“新对话”标题，添加 chat_id 后缀避免重复
        if display_name in display_map:
            display_name += f" ({cid[-4:]})"
        display_map[display_name] = cid
    return display_map

# 显示该模型所有对话窗口
def display_chat_title(model_index):
    kind = models_info[model_index]["kind"]
    name = models_info[model_index]["name"]

    display_map = get_chat_display_titles(kind)
    display_names = list(display_map.keys())
    current_chat_id = st.session_state["active_chat"][kind]
    current_display_name = next(k for k, v in display_map.items() if v == current_chat_id)
    display_names_reversed = list(reversed(display_names))

    prev_chat_id = st.session_state["active_chat"][kind]
    selected_name = st.radio(
        label=f"**历史对话({name})**",
        options=display_names_reversed,
        index=display_names_reversed.index(current_display_name),
        key=f"radio_{kind}"
    )
    selected_chat_id = display_map[selected_name]

    if prev_chat_id != selected_chat_id:
        st.session_state["active_chat"][kind] = selected_chat_id
        st.rerun()

# 展示历史消息（流式输出最新的AI对话）
def display_messages(current_messages,is_new_query):
    latest_msg = current_messages[-1]  # 获取最新的对话消息
    
    for idx, msg in enumerate(current_messages):
        if msg['role'] == 'system':
            continue

        # 如果是 AI 的回答，且是最新的对话，进行流式输出
        with st.chat_message(name='human' if msg['role'] == 'user' else 'ai'):
            if msg['role'] == 'assistant' and msg == latest_msg and is_new_query:
                with st.empty():
                    partial_response = ""
                    for char in msg['content']: 
                        partial_response += char
                        st.markdown(partial_response)
                        time.sleep(0.03) 
            else:
                st.markdown(msg['content'])

# 新建对话按钮
def create_new_chat_button(kind):
    has_empty = any(
        not any(m["role"] == "user" for m in msgs)
        for msgs in st.session_state["conversations"][kind].values()
    )

    # 仅在没有“新对话”时显示按钮
    if has_empty:
        st.button("新对话", disabled=True, help="当前已有一个空对话，发送消息后才能创建新对话")
    else:
        if st.button("新对话"):
            new_id =create_new_chat(kind)
            st.session_state["active_chat"][kind] = new_id
            st.rerun()

# 主程序
def main():
    st.set_page_config(page_title="多窗口聊天助手", layout="wide")
    
    with st.sidebar:
        st.title("对话助手")

        col1, col2 = st.columns([2, 1])
        # 选择模型
        with col1: 
            choice = st.radio(
                label='选择模型',
                options=[m["name"] for m in models_info],
                index=0)
        
        model_index = [m["name"] for m in models_info].index(choice)
        kind = models_info[model_index]["kind"]

        # 温度选择
        temperature = st.slider(label="模型温度", 
                                min_value= 0.0, 
                                max_value=2.0, 
                                value=1.0, 
                                step=0.1,
                                help="模型温度越高,模型生成文本的多样性越高")
        
        # 显示该模型所有对话窗口
        display_chat_title(model_index)

    # 输入框
    user_input = st.chat_input("请输入你的问题...")
    is_new_query = False
    if user_input:
        is_new_query = ask_model(model_index, user_input, temperature)

    with st.sidebar:
        # 新建对话按钮
        with col2:
            create_new_chat_button(kind)

    # 获取当前激活的聊天
    current_chat_id = st.session_state["active_chat"][kind]
    current_messages = st.session_state["conversations"][kind][current_chat_id]

    # 展示历史消息
    display_messages(current_messages,is_new_query)

if __name__ == "__main__":
    init_conversations()
    main()