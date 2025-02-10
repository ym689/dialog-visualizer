import streamlit as st
import requests
import json
import base64
import urllib.parse
import html
import ast

def parse_dialog_data(text):
    """解析多行JSON数据，每行是一个独立的对话"""
    dialogs = []
    for line in text.strip().split('\n'):
        if line.strip():  # 忽略空行
            try:
                dialog = json.loads(line.strip())
                dialogs.append(dialog)
            except json.JSONDecodeError as e:
                st.error(f"Error parsing line: {e}")
                continue
    return dialogs

def display_dialog(dialog):
    # 添加一个容器来展示对话
    with st.container():
        # 显示reward，使用更醒目的格式
        st.info(f"💎 Reward: {dialog['reward']}")
        
        # 使用列表来展示对话
        for message in dialog['dialog']:
            role = message['role']
            content = message['content']
            
            # 使用不同的样式显示不同角色的消息
            if role == 'Seeker':
                st.write(f'👤 **Seeker**')
                st.write(content)
            else:
                st.write(f'🤖 **Recommender**')
                st.write(content)
            
            # 添加一个小间隔
            st.write("")
        
        # 添加分隔线
        st.divider()

def get_github_files(repo_owner, repo_name, path, token):
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        return []
    
    files = [file['name'] for file in response.json() if file['type'] == 'file' and file['name'].endswith('.txt')]
    return files

def read_github_file(repo_owner, repo_name, file_path, token):
    # URL encode each path component separately
    encoded_path = '/'.join(urllib.parse.quote(part, safe='') for part in file_path.split('/'))
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{encoded_path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        st.error(f"Error fetching file: {response.status_code}")
        return None
        
    try:
        file_info = response.json()
        download_url = file_info.get('download_url')
        
        if not download_url:
            st.error("No download URL found")
            return None
            
        # 直接下载文件内容
        file_response = requests.get(download_url, headers=headers)
        if file_response.status_code != 200:
            st.error(f"File download failed: {file_response.status_code}")
            return None
            
        content = file_response.text
        
        # 显示行数统计
        lines = [line for line in content.split('\n') if line.strip()]
        
        # 使用 ast.literal_eval 来解析 Python 字典格式
        dialogs = []
        for line in lines:
            try:
                dialog = ast.literal_eval(line)
                dialogs.append(dialog)
            except Exception as e:
                continue
        
        return dialogs
        
    except Exception as e:
        st.error(f"Error processing content: {str(e)}")
        return None

def format_file_name(file_name):
    """简化文件名显示"""
    # 移除 .txt 后缀
    name = file_name.replace('.txt', '')
    
    if name.startswith('Evaluate'):
        # 处理评估文件名
        parts = name.split('-')
        if len(parts) >= 4:
            epoch = f"{parts[1]}{parts[2]}"  # epoch-1
            model = parts[-1]    # llama2
            return f"Eval Metrics ({epoch}, {model})"
    else:
        # 处理对话文件名
        parts = name.split('-')
        if len(parts) >= 4:
            epoch = parts[1] + parts[2]  # epoch-1
            model = parts[-1]  # llama2
            return f"Dialog Record ({epoch}, {model})"
    
    # 如果格式不匹配，返回简化的原始名称
    return name

def format_dialog(dialog_data):
    st.markdown("""
    <style>
        /* 整体页面背景 */
        .stApp {
            background: linear-gradient(to bottom right, #f8f9fa, #e9ecef);
        }
        
        /* 标题样式 */
        .main .block-container h1 {
            color: #2c3e50;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
            margin-bottom: 30px;
        }
        
        /* 消息基础样式 */
        .message {
            margin: 15px 0;
            padding: 20px;
            border-radius: 15px;
            position: relative;
            font-size: 18px;
            line-height: 1.6;
            display: flex;
            align-items: flex-start;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
            transition: transform 0.2s ease;
        }
        
        .message:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        .message-icon {
            font-size: 24px;
            margin-right: 15px;
            min-width: 35px;
            text-align: center;
            padding-top: 3px;
        }
        
        .message-content {
            flex-grow: 1;
            color: #2c3e50;
        }
        
        /* Seeker 消息样式 */
        .seeker {
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            margin-left: 40px;
            border-top-left-radius: 5px;
        }
        
        /* Recommender 消息样式 */
        .recommender {
            background: linear-gradient(135deg, #f5f5f5, #e0e0e0);
            margin-right: 40px;
            border-top-right-radius: 5px;
        }
        
        /* Reward 样式 */
        .reward {
            margin: 15px 40px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #fff3e0, #ffe0b2);
            border-radius: 10px;
            font-size: 16px;
            display: flex;
            align-items: center;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            font-family: 'Helvetica Neue', Arial, sans-serif;
        }
        
        .reward-icon {
            font-size: 20px;
            margin-right: 12px;
            color: #ffa000;
        }
        
        /* 展开器样式 */
        .stExpander {
            font-size: 14px;
            margin: 5px 40px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            background-color: white;
        }
        
        .stExpander button {
            font-size: 14px !important;
            color: #546e7a !important;
            background-color: transparent !important;
            border-radius: 6px !important;
        }
        
        .stExpander button:hover {
            background-color: #f5f5f5 !important;
        }
        
        /* 选择框样式 */
        .stSelectbox {
            font-size: 16px;
            margin-bottom: 25px;
        }
        
        .stSelectbox > div > div {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
        }
        
        /* 分割线样式 */
        hr {
            margin: 30px 0;
            border: none;
            height: 1px;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent);
        }
        
        /* 按钮容器样式 */
        .stButton > button {
            background: linear-gradient(135deg, #6c5ce7, #a367dc);
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            font-family: 'Helvetica Neue', Arial, sans-serif;
            transition: all 0.3s ease;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            background: linear-gradient(135deg, #5b4cc4, #8b4dc9);
        }
        
        .stButton > button:active {
            transform: translateY(0px);
        }
        
        /* 按钮行样式 */
        .button-row {
            display: flex;
            gap: 10px;
            margin: 10px 0;
        }
    </style>
    """, unsafe_allow_html=True)

    messages = dialog_data["full_state"]
    
    # 显示第一个 Seeker 消息
    if messages:
        first_msg = messages[0]
        st.markdown(f"""
            <div class="message seeker">
                <div class="message-icon">👤</div>
                <div class="message-content">
                    {html.escape(first_msg["content"])}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        i = 1
        while i < len(messages):
            # Recommender
            if i < len(messages) and messages[i]["role"] == "Recommender":
                msg = messages[i]
                st.markdown(f"""
                    <div class="message recommender">
                        <div class="message-icon">🤖</div>
                        <div class="message-content">
                            {html.escape(str(msg["content"]))}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("📋 User Preference"):
                        st.write(msg.get("user_preference", ""))
                with col2:
                    with st.expander("💭 Recommender Prompt"):
                        st.write(msg.get("Recommender_prompt", ""))
                i += 1
            
            # Seeker
            if i < len(messages) and messages[i]["role"] == "Seeker":
                msg = messages[i]
                st.markdown(f"""
                    <div class="message seeker">
                        <div class="message-icon">👤</div>
                        <div class="message-content">
                            {html.escape(str(msg["content"]))}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("💬 Seeker Prompt"):
                    st.write(msg.get("Seeker_prompt", ""))
                i += 1
            
            # Critic
            if i < len(messages) and messages[i]["role"] == "critic":
                msg = messages[i]
                reward = msg.get("reward", 0)
                st.markdown(f"""
                    <div class="reward">
                        <div class="reward-icon">⭐</div>
                        <div>Reward: {reward}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("📊 Content"):
                        content_list = msg.get("content", [])
                        for idx, content in enumerate(content_list, 1):
                            st.markdown(f"**Output {idx}:**")
                            st.write(content)
                with col2:
                    with st.expander("📝 Critique Prompt"):
                        st.write(msg.get("critic_prompt", ""))
                i += 1
                st.markdown("<hr/>", unsafe_allow_html=True)

def display_eval_metrics(file_content):
    """Display evaluation metrics in a formatted way"""
    st.markdown("""
        <style>
        /* 整体页面样式 */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
        }
        
        /* 移除空白容器 */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            max-width: 95%;
        }
        
        /* 选择框样式 */
        .stSelectbox {
            margin-bottom: 25px;
        }
        
        .stSelectbox > div > div {
            background-color: white;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            padding: 8px;  /* 增加内边距 */
            min-height: 48px;  /* 设置最小高度 */
        }
        
        /* 选择框文本样式 */
        .stSelectbox > div > div > div {
            line-height: 1.5;  /* 增加行高 */
            white-space: normal !important;  /* 允许文本换行 */
            overflow: visible !important;  /* 允许内容溢出 */
        }
        
        /* 容器样式 */
        .metric-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s ease;
        }
        
        .metric-container:hover {
            transform: translateY(-2px);
        }
        
        /* 标题样式 */
        .metric-header {
            color: #1a237e;
            font-size: 1.4em;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 12px;
            border-bottom: 2px solid #e3f2fd;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            letter-spacing: 0.5px;
        }
        
        /* 指标值样式 */
        .metric-value {
            display: flex;
            align-items: center;
            margin: 12px 0;
            padding: 12px 16px;
            background: linear-gradient(135deg, #f8f9fa, #ffffff);
            border-radius: 10px;
            border: 1px solid #e3f2fd;
            transition: all 0.2s ease;
        }
        
        .metric-value:hover {
            background: linear-gradient(135deg, #e3f2fd, #f5f7fa);
            border-color: #bbdefb;
        }
        
        /* 标签样式 */
        .metric-label {
            color: #37474f;
            min-width: 160px;
            font-weight: 500;
            font-size: 0.95em;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }
        
        /* 数值样式 */
        .metric-number {
            color: #1565c0;
            font-weight: 600;
            font-size: 1.1em;
            font-family: 'Roboto Mono', monospace;
        }
        
        /* 网格布局样式 */
        .turn-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        /* 图标样式 */
        .metric-icon {
            margin-right: 12px;
            color: #5c6bc0;
            font-size: 1.2em;
        }
        
        /* 动画效果 */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .metric-container {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* 移除不必要的空白 */
        .css-1544g2n {
            padding-top: 0rem;
        }
        
        .css-1q1n0ol {
            padding-top: 0rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # 创建主要指标容器
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">📊 Overall Metrics</div>', unsafe_allow_html=True)
    
    # 提取主要指标
    lines = file_content.split('\n')
    for line in lines:
        if "Testing SR:" in line:
            sr = line.split("Testing SR:")[1].strip().split()[0]
            st.markdown(f"""
                <div class="metric-value">
                    <span class="metric-icon">🎯</span>
                    <span class="metric-label">Success Rate</span>
                    <span class="metric-number">{sr}</span>
                </div>
            """, unsafe_allow_html=True)
        elif "Testing Avg@T:" in line:
            avg_t = line.split("Testing Avg@T:")[1].strip().split()[0]
            st.markdown(f"""
                <div class="metric-value">
                    <span class="metric-icon">⏱️</span>
                    <span class="metric-label">Average Turns</span>
                    <span class="metric-number">{avg_t}</span>
                </div>
            """, unsafe_allow_html=True)
        elif "Testing Rewards:" in line:
            rewards = line.split("Testing Rewards:")[1].strip().split()[0]
            st.markdown(f"""
                <div class="metric-value">
                    <span class="metric-icon">🌟</span>
                    <span class="metric-label">Rewards</span>
                    <span class="metric-number">{rewards}</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 创建回合指标容器
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.markdown('<div class="metric-header">📈 Turn-based Success Rate</div>', unsafe_allow_html=True)
    
    # 创建网格布局来展示回合指标
    st.markdown('<div class="turn-metrics">', unsafe_allow_html=True)
    for line in lines:
        if "Testing SR-turn@" in line:
            turn_num = line.split("@")[1].split(":")[0]
            value = line.split(":")[1].strip()
            st.markdown(f"""
                <div class="metric-value">
                    <span class="metric-icon">🔄</span>
                    <span class="metric-label">Turn {turn_num}</span>
                    <span class="metric-number">{value}</span>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

def view_dialog(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 找到第一个有效的 JSON 对象
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                dialog_data = json.loads(content[start:end])
                format_dialog(dialog_data)
            else:
                st.error("No valid JSON data found in file")
    except Exception as e:
        st.error(f"Error loading dialog: {str(e)}")

def show_login_page():
    st.markdown("""
        <style>
            /* 登录页面容器 */
            .login-container {
                max-width: 400px;
                margin: 80px auto 20px auto;  /* 调整上边距 */
                padding: 40px;  /* 增加内边距 */
                background: white;
                border-radius: 15px;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            /* 登录标题 */
            .login-title {
                color: #2c3e50;
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 30px;
                font-family: 'Helvetica Neue', Arial, sans-serif;
            }
            
            /* 登录图标 */
            .login-icon {
                font-size: 60px;  /* 增大图标 */
                margin-bottom: 25px;
            }
            
            /* 输入框容器 */
            .stTextInput {
                max-width: 300px;  /* 限制输入框宽度 */
                margin: 0 auto;    /* 水平居中 */
            }
            
            .stTextInput > div > div {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 8px 12px;  /* 增加输入框高度 */
                transition: all 0.3s ease;
            }
            
            .stTextInput > div > div:hover {
                border-color: #6c5ce7;
            }
            
            .stTextInput > div > div:focus-within {
                border-color: #6c5ce7;
                box-shadow: 0 0 0 3px rgba(108, 92, 231, 0.1);
            }
            
            /* 背景样式 */
            .stApp {
                background: linear-gradient(135deg, #a8c0ff, #3f2b96);
            }
            
            /* 错误消息样式 */
            .stAlert {
                max-width: 300px;  /* 限制错误消息宽度 */
                margin: 10px auto;  /* 水平居中 */
                background-color: rgba(255, 92, 92, 0.1);
                border: 1px solid #ff5c5c;
                border-radius: 8px;
                color: #ff5c5c;
                padding: 10px;
            }
            
            /* 帮助文本样式 */
            .stTextInput > div > div > div > small {
                color: #666;
                font-size: 0.85em;
                margin-top: 5px;
            }
        </style>
        
        <div class="login-container">
            <div class="login-icon">🔐</div>
            <div class="login-title">Welcome to Dialog Visualization</div>
        </div>
    """, unsafe_allow_html=True)
    
    # 使用列来控制输入框的宽度和位置
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("Enter password", 
                               type="password", 
                               placeholder="Please enter your password",
                               help="Contact administrator if you need access",
                               key="password_input")
        
        if password:
            if password == "next2025":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")

def main():
    st.set_page_config(page_title="Dialog Visualization", layout="wide")
    
    # 添加全局样式
    st.markdown("""
        <style>
        /* 页面基础样式 */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
        }
        
        /* 主容器样式 */
        .main .block-container {
            padding: 2rem 1rem 1rem 1rem !important;
            max-width: 95% !important;
        }
        
        /* 页面头部样式 */
        .header-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        
        .header-title {
            font-size: 2rem;
            font-weight: 600;
            color: #1a237e;
            margin: 0;
            padding: 0;
        }
        
        /* 选择框通用样式 */
        .stSelectbox {
            margin-bottom: 1.5rem;
        }
        
        .stSelectbox > div > div {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            min-height: 48px;
            padding: 0.5rem;
        }
        
        .stSelectbox > div > div > div {
            line-height: 1.5;
            white-space: normal !important;
            overflow: visible !important;
        }
        
        /* 文件选择框特殊样式 */
        .file-select {
            margin: 1rem 0 2rem 0;
        }
        
        .file-select > div > div {
            background-color: white;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            min-height: 48px;
        }
        
        /* 按钮样式 */
        .stButton > button {
            background-color: #1a237e;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        
        .stButton > button:hover {
            background-color: #283593;
        }
        
        /* 移除不必要的空白 */
        [data-testid="stVerticalBlock"] > div:empty {
            display: none !important;
        }
        
        /* 内容区域样式 */
        .content-container {
            margin-top: 1rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # 页面头部布局
    st.markdown("""
        <div class="header-container">
            <h1 class="header-title">Dialog Visualization</h1>
        </div>
    """, unsafe_allow_html=True)

    # 使用列布局组织顶部控件
    col1, col2, col3 = st.columns([6, 2, 1])
    with col2:
        selected_view = st.selectbox(
            "",
            ["Conversation History", "Eval Metrics"],
            key="view_selector",
            label_visibility="collapsed"
        )
    with col3:
        if st.button("🚪 Logout", key="logout"):
            st.session_state.authenticated = False
            st.rerun()

    # 设置数据路径
    if selected_view == "Conversation History":
        DATA_PATH = "data/conversation_history"
        display_conversation = True
    else:
        DATA_PATH = "data/eval_metrics"
        display_conversation = False

    # 文件选择区域
    available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
    if not available_files:
        st.error(f"No files found in {DATA_PATH}.")
        return

    st.markdown('<div class="file-select">', unsafe_allow_html=True)
    selected_file = st.selectbox(
        "Select File",
        available_files,
        format_func=format_file_name
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # 内容区域
    if selected_file:
        st.markdown('<div class="content-container">', unsafe_allow_html=True)
        if display_conversation:
            # 对话历史显示逻辑
            dialogs = read_github_file(REPO_OWNER, REPO_NAME, f"{DATA_PATH}/{selected_file}", GITHUB_TOKEN)
            if dialogs:
                dialog_index = st.selectbox(
                    "Select Dialog",
                    range(len(dialogs)),
                    format_func=lambda x: f"Dialog {x+1}"
                )
                
                if st.button("🔄 Refresh Dialog"):
                    st.rerun()
                    
                format_dialog(dialogs[dialog_index])
        else:
            # 评估指标显示逻辑
            file_path = f"{DATA_PATH}/{selected_file}"
            encoded_path = urllib.parse.quote(file_path)
            url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_path}"
            
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                content = base64.b64decode(response.json()['content']).decode('utf-8')
                display_eval_metrics(content)
            else:
                st.error(f"Error fetching file: {response.status_code}")
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()