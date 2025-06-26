import streamlit as st
import requests
import json
import base64
import urllib.parse
import html
import ast
import plotly.graph_objects as go
import re
import os

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
        file_response = requests.get(download_url, headers=headers)
        if file_response.status_code != 200:
            st.error(f"File download failed: {file_response.status_code}")
            return None
        content = file_response.text
        dialogs = extract_dicts_from_file(content)
        if not dialogs:
            st.error("No valid dialogs with 'full_state' found in file.")
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
    if not isinstance(dialog_data, dict) or "full_state" not in dialog_data:
        st.error("This dialog does not contain 'full_state' key. Please check your data format.")
        st.write(dialog_data)
        return

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

    else:
        st.warning("No dialogs found or failed to parse any dialog.")

def display_eval_metrics(file_content):
    """Display evaluation metrics in a formatted way"""
    st.markdown("""
        <style>
        /* 整体页面样式 */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa, #e4e8eb);
        }
        
        /* 调整页面顶部和容器布局 */
        .block-container {
            padding: 5rem 1rem 0rem 1rem !important;  /* 显著增加顶部间距 */
            max-width: 95% !important;
        }
        
        /* 移除默认的空白区域 */
        .css-18e3th9 {
            padding: 0 !important;
        }
        
        .css-1d391kg {
            padding: 0 !important;
        }
        
        /* 选择框样式优化 */
        .stSelectbox > div {
            padding-bottom: 1.5rem;  /* 增加选择框底部间距 */
        }
        
        .stSelectbox > div > div {
            background-color: white;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            min-height: 60px !important;
            padding: 0.5rem !important;
            margin-top: 0.5rem !important;  /* 增加选择框顶部间距 */
        }
        
        /* 标题样式调整 */
        h1 {
            padding-top: 3rem !important;  /* 增加标题顶部间距 */
            margin-bottom: 2rem !important;
            position: relative;  /* 确保标题正确定位 */
            z-index: 1;  /* 提高标题层级 */
        }
        
        /* 度量指标容器样式 */
        .metric-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 3rem 0 2rem 0;  /* 调整容器边距 */
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            transition: transform 0.2s ease;
            position: relative;  /* 确保容器正确定位 */
            z-index: 0;  /* 降低容器层级 */
        }
        
        /* 其他样式保持不变 */
        .metric-container:hover {
            transform: translateY(-2px);
        }
        
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
        
        .metric-label {
            color: #37474f;
            min-width: 160px;
            font-weight: 500;
            font-size: 0.95em;
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
        }
        
        .metric-number {
            color: #1565c0;
            font-weight: 600;
            font-size: 1.1em;
            font-family: 'Roboto Mono', monospace;
        }
        
        .turn-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .metric-icon {
            margin-right: 12px;
            color: #5c6bc0;
            font-size: 1.2em;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .metric-container {
            animation: fadeIn 0.5s ease-out;
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

def display_metrics_analysis(data_path, github_token):
    """Display metrics analysis with line charts"""
    # 定义 GitHub 仓库信息
    REPO_OWNER = "ym689"
    REPO_NAME = "dialog-visualizer"
    
    # 添加刷新按钮
    if st.button("🔄 Refresh Analysis"):
        st.rerun()
        
    st.markdown("""
        <style>
        /* 图表容器样式 */
        .metrics-container {
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            margin: 2rem 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* 分割线样式 */
        .metrics-divider {
            margin: 2rem 0;
            height: 2px;
            background: linear-gradient(to right, transparent, #6c5ce7, transparent);
        }
        
        /* 图表标题样式 */
        .chart-title {
            color: #1a237e;
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e3f2fd;
        }
        </style>
    """, unsafe_allow_html=True)

    # 获取所有文件
    files = get_github_files(REPO_OWNER, REPO_NAME, data_path, github_token)
    if not files:
        st.error("No files found for analysis.")
        return
        
    # 添加加载提示
    with st.spinner('Loading metrics data...'):
        metrics_data = {
            'overall': {
                'Success Rate': [],
                'Average Turns': [],
                'Rewards': []
            },
            'turn_based': {}
        }
        
        # 读取所有文件数据
        for file in files:
            try:
                file_path = f"{data_path}/{file}"
                encoded_path = urllib.parse.quote(file_path)
                url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{encoded_path}"
                
                headers = {
                    "Authorization": f"token {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                response = requests.get(url, headers=headers)
                
                if response.status_code == 200:
                    content = base64.b64decode(response.json()['content']).decode('utf-8')
                    lines = content.split('\n')
                    
                    # 提取epoch数字 - 更新提取逻辑
                    try:
                        # 从文件名中提取epoch数字
                        parts = file.split('-')
                        for i, part in enumerate(parts):
                            if part == 'epoch' and i + 1 < len(parts):
                                file_id = int(parts[i + 1])
                                break
                        else:
                            continue  # 如果没有找到epoch数字，跳过此文件
                    except (ValueError, IndexError):
                        continue  # 如果解析失败，跳过此文件
                    
                    # 解析数据
                    for line in lines:
                        if "Testing SR:" in line:
                            try:
                                sr = float(line.split("Testing SR:")[1].strip().split()[0])
                                metrics_data['overall']['Success Rate'].append((file_id, sr))
                            except (ValueError, IndexError):
                                continue
                        elif "Testing Avg@T:" in line:
                            try:
                                avg_t = float(line.split("Testing Avg@T:")[1].strip().split()[0])
                                metrics_data['overall']['Average Turns'].append((file_id, avg_t))
                            except (ValueError, IndexError):
                                continue
                        elif "Testing Rewards:" in line:
                            try:
                                rewards = float(line.split("Testing Rewards:")[1].strip().split()[0])
                                metrics_data['overall']['Rewards'].append((file_id, rewards))
                            except (ValueError, IndexError):
                                continue
                        elif "Testing SR-turn@" in line:
                            try:
                                turn_num = line.split("@")[1].split(":")[0]
                                value = float(line.split(":")[1].strip())
                                if turn_num not in metrics_data['turn_based']:
                                    metrics_data['turn_based'][turn_num] = []
                                metrics_data['turn_based'][turn_num].append((file_id, value))
                            except (ValueError, IndexError):
                                continue
            except Exception as e:
                st.error(f"Error processing file {file}: {str(e)}")
                continue

        # 对数据点进行排序
        for metric in metrics_data['overall'].values():
            metric.sort(key=lambda x: x[0])
        for turn_data in metrics_data['turn_based'].values():
            turn_data.sort(key=lambda x: x[0])

        # 创建整体指标图表
        st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Overall Metrics</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # 绘制整体指标图表
        for i, (metric_name, metric_data) in enumerate(metrics_data['overall'].items()):
            with col1 if i % 2 == 0 else col2:
                if metric_data:
                    x_values = [x[0] for x in metric_data]
                    y_values = [x[1] for x in metric_data]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=metric_name,
                        line=dict(color='#6c5ce7', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig.update_layout(
                        title=metric_name,
                        xaxis_title="Epoch",
                        yaxis_title="Value",
                        showlegend=False,
                        height=300,
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)
        
        # 添加分割线
        st.markdown('<div class="metrics-divider"></div>', unsafe_allow_html=True)
        
        # 创建回合指标图表
        st.markdown('<div class="metrics-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Turn-based Success Rate</div>', unsafe_allow_html=True)
        
        # 对回合指标进行排序
        sorted_turns = sorted(metrics_data['turn_based'].keys(), key=lambda x: int(x))
        
        # 创建两列布局
        col1, col2 = st.columns(2)
        
        # 绘制回合指标图表
        for i, turn_num in enumerate(sorted_turns):
            with col1 if i % 2 == 0 else col2:
                turn_data = metrics_data['turn_based'][turn_num]
                if turn_data:
                    x_values = [x[0] for x in turn_data]
                    y_values = [x[1] for x in turn_data]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=x_values,
                        y=y_values,
                        mode='lines+markers',
                        name=f'Turn {turn_num}',
                        line=dict(color='#6c5ce7', width=2),
                        marker=dict(size=8)
                    ))
                    
                    fig.update_layout(
                        title=f'Success Rate at Turn {turn_num}',
                        xaxis_title="Epoch",
                        yaxis_title="Success Rate",
                        showlegend=False,
                        height=300,
                        margin=dict(l=40, r=40, t=40, b=40)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

def view_dialog(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 找到第一个有效的 JSON 对象
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                dialog_data = json.loads(content[start:end])
                if not isinstance(dialog_data, dict) or "full_state" not in dialog_data:
                    st.error("This dialog does not contain 'full_state' key. Please check your data format.")
                    st.write(dialog_data)
                    return
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

def get_all_settings(data_dir="data"):
    # 返回所有可用setting名
    dirs = os.listdir(data_dir)
    conv_settings = [d.replace("conversation_history", "").strip("_") for d in dirs if d.startswith("conversation_history")]
    eval_settings = [d.replace("eval_metrics", "").strip("_") for d in dirs if d.startswith("eval_metrics")]
    # 取交集或并集都可，这里用并集
    all_settings = sorted(set(conv_settings + eval_settings))
    return all_settings

def main():
    st.set_page_config(page_title="Dialog Visualization", layout="wide")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        show_login_page()
        return

    try:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    except Exception as e:
        st.error(f"Error reading GitHub token: {str(e)}")
        return

    REPO_OWNER = "ym689"
    REPO_NAME = "dialog-visualizer"

    # 获取所有setting
    all_settings = get_all_settings("data")
    if not all_settings:
        st.error("No settings found in data directory.")
        return

    st.title("Dialog Visualization (Ablation Comparison)")

    col_left, col_right = st.columns(2)
    for col, side in zip([col_left, col_right], ["Left", "Right"]):
        with col:
            st.header(f"{side} Setting")
            setting = st.selectbox(f"Select Setting ({side})", all_settings, key=f"setting_{side}")
            view = st.selectbox(f"Select View ({side})", ["Conversation History", "Eval Metrics"], key=f"view_{side}")

            # 目录名拼接
            conv_dir = f"data/conversation_history{('_' + setting) if setting else ''}"
            eval_dir = f"data/eval_metrics{('_' + setting) if setting else ''}"

            if view == "Conversation History":
                DATA_PATH = conv_dir
                display_conversation = True
            else:
                DATA_PATH = eval_dir
                display_conversation = False

            available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
            if not available_files:
                st.error(f"No files found in {DATA_PATH}.")
                continue

            selected_file = st.selectbox(f"Select File ({side})", available_files, format_func=format_file_name, key=f"file_{side}")

            if selected_file:
                if display_conversation:
                    dialogs = read_github_file(REPO_OWNER, REPO_NAME, f"{DATA_PATH}/{selected_file}", GITHUB_TOKEN)
                    if dialogs:
                        dialog_index = st.selectbox(
                            f"Select Dialog ({side})",
                            range(len(dialogs)),
                            format_func=lambda x: f"Dialog {x+1}",
                            key=f"dialog_{side}"
                        )
                        if st.button(f"🔄 Refresh Dialog ({side})"):
                            st.rerun()
                        format_dialog(dialogs[dialog_index])
                else:
                    # Display eval metrics
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

def extract_dicts_from_file(content):
    """
    提取文件中所有完整的 dict（支持多行），返回 dict 列表
    """
    dicts = []
    # 用正则提取所有 {...} 块，支持嵌套
    pattern = re.compile(r'({(?:[^{}]|(?R))*})', re.DOTALL)
    matches = pattern.findall(content)
    for dict_str in matches:
        dict_str = dict_str.strip()
        # 先尝试 json.loads
        try:
            d = json.loads(dict_str)
            if isinstance(d, dict) and "full_state" in d:
                dicts.append(d)
                continue
        except Exception:
            pass
        # 再尝试 ast.literal_eval
        try:
            d = ast.literal_eval(dict_str)
            if isinstance(d, dict) and "full_state" in d:
                dicts.append(d)
        except Exception:
            pass
    return dicts

if __name__ == "__main__":
    main()