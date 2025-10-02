import streamlit as st
import json
import os
import html
import re
from typing import List, Dict, Any
import random

# 页面配置
st.set_page_config(
    page_title="AI Dialog Showcase",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 全局样式
def load_custom_css():
    st.markdown("""
    <style>
    /* 导入Google字体 */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* 全局重置和基础样式 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* 强制移除所有顶部空白 */
    .stApp, .stApp > div, .stApp > div > div, .stApp > div > div > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        font-family: 'Times New Roman', Times, serif;
    }
    
    /* 隐藏Streamlit默认元素 */
    .stApp > header {
        display: none;
    }
    
    .stApp > div[data-testid="stToolbar"] {
        display: none;
    }
    
    .stApp > div[data-testid="stDecoration"] {
        display: none;
    }
    
    /* 隐藏Streamlit默认的空白区域 */
    .stApp > div[data-testid="stAppViewContainer"] {
        padding-top: 0 !important;
    }
    
    .stApp > div[data-testid="stAppViewContainer"] > div {
        padding-top: 0 !important;
    }
    
    /* 移除所有Streamlit默认边距 */
    .stApp > div[data-testid="stAppViewContainer"] > div > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 移除Streamlit默认的block-container样式 */
    .stApp > div[data-testid="stAppViewContainer"] > div > div > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 强制移除所有默认边距 */
    .stApp > div[data-testid="stAppViewContainer"] > div > div > div > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 移除Streamlit默认的空白区域 */
    .stApp > div[data-testid="stAppViewContainer"] > div > div > div > div > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* 主容器 */
    .main-container {
        max-width: 1200px;
        margin: 0 !important;
        padding: 0.5rem !important;
        min-height: 100vh;
    }
    
    /* 强制移除所有markdown元素的边距 */
    .stMarkdown {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    .stMarkdown > div {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 特别针对主容器的markdown */
    .stMarkdown:has(.main-container) {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* 头部区域 */
    .header {
        text-align: center;
        margin-bottom: 1rem;
        padding: 0.5rem 0;
    }
    
    .header h1 {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin-bottom: 1rem;
        text-shadow: 0 4px 20px rgba(0,0,0,0.3);
        letter-spacing: -0.02em;
    }
    
    .header p {
        font-size: 1.2rem;
        color: rgba(255,255,255,0.9);
        font-weight: 400;
        max-width: 600px;
        margin: 0 auto;
        line-height: 1.6;
    }
    
    /* 选择器样式（与背景融合的渐变玻璃效果） */
    .stSelectbox {
        margin-bottom: 0.75rem;
    }
    .stSelectbox > label {
        color: rgba(255,255,255,0.95) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.04em !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25) !important;
    }
    .stSelectbox > div > div {
        background: linear-gradient(135deg, rgba(102,126,234,0.85), rgba(118,75,162,0.85)) !important;
        border: 1px solid rgba(255, 255, 255, 0.35) !important;
        border-radius: 14px !important;
        padding: 0.6rem 0.85rem !important;
        color: #ffffff !important;
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18) !important;
        backdrop-filter: blur(8px) !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
    }
    .stSelectbox > div > div:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 10px 24px rgba(0, 0, 0, 0.22) !important;
        border-color: rgba(255,255,255,0.55) !important;
    }
    .stSelectbox > div > div:focus-within {
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.25) !important;
        border-color: rgba(255,255,255,0.65) !important;
    }
    /* BaseWeb Select 内部元素调色为浅色文本 */
    .stSelectbox [data-baseweb="select"] > div,
    .stSelectbox [data-baseweb="select"] > div > div,
    .stSelectbox [data-baseweb="select"] input {
        background: transparent !important;
        color: #ffffff !important;
    }
    .stSelectbox svg {
        fill: #ffffff !important;
        color: #ffffff !important;
    }
    /* 下拉菜单 */
    .stSelectbox [data-baseweb="select"] > div[role="listbox"] {
        background: rgba(255, 255, 255, 0.98) !important;
        border-radius: 12px !important;
        box-shadow: 0 12px 30px rgba(0,0,0,0.18) !important;
        border: 1px solid rgba(0, 0, 0, 0.06) !important;
        backdrop-filter: blur(10px) !important;
    }
    .stSelectbox [data-baseweb="select"] > div[role="listbox"] > div {
        color: #2d3748 !important;
        border-radius: 8px !important;
        margin: 2px !important;
        padding: 0.55rem 0.8rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.02em !important;
    }
    .stSelectbox [data-baseweb="select"] > div[role="listbox"] > div:hover {
        background: rgba(102, 126, 234, 0.10) !important;
    }
    /* 确保选中值与输入文字可见（BaseWeb结构覆盖）*/
    .stSelectbox [data-baseweb="select"] * {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stSelectbox [data-baseweb="select"] div[role="combobox"],
    .stSelectbox [data-baseweb="select"] div[aria-hidden="true"],
    .stSelectbox [data-baseweb="select"] span,
    .stSelectbox [data-baseweb="select"] div {
        color: #ffffff !important;
    }
    .stSelectbox input::placeholder {
        color: rgba(255,255,255,0.85) !important;
    }
    
    
    /* 对话容器 */
    .dialog-container {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
        min-height: 400px;
    }
    
    .dialog-header {
            display: flex;
        justify-content: space-between;
            align-items: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #f1f5f9;
    }
    
    .dialog-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #2d3748;
    }
    
    .dialog-meta {
        display: flex;
        gap: 1rem;
        align-items: center;
    }
    
    .meta-badge {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* 消息样式 */
    .message {
        margin: 1.5rem 0;
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        animation: fadeInUp 0.6s ease-out;
    }
    
    .message-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 600;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    .message-avatar.user {
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
    }
    
    .message-avatar.assistant {
        background: linear-gradient(135deg, #f093fb, #f5576c);
        color: white;
    }
    
    .message-content {
        flex: 1;
        background: #f8fafc;
        padding: 1.25rem 1.5rem;
        border-radius: 18px;
        border: 1px solid #e2e8f0;
        position: relative;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .message-content::before {
        content: '';
        position: absolute;
        top: 20px;
        left: -8px;
        width: 0;
        height: 0;
        border-top: 8px solid transparent;
        border-bottom: 8px solid transparent;
        border-right: 8px solid #f8fafc;
    }
    
    .message-content.user::before {
        border-right-color: #f8fafc;
    }
    
    .message-content.assistant::before {
        border-right-color: #f8fafc;
    }
    
    .message-role {
        font-weight: 600;
        color: #4a5568;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    .message-text {
        color: #2d3748;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 4rem 2rem;
        color: #718096;
    }
    
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        opacity: 0.5;
    }
    
    .empty-state h3 {
        font-size: 1.5rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #4a5568;
    }
    
    .empty-state p {
        font-size: 1rem;
        line-height: 1.6;
    }
    
    /* 动画 */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0%, 100% {
            opacity: 1;
        }
        50% {
            opacity: 0.5;
        }
    }
    
    .loading {
        animation: pulse 2s infinite;
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .main-container {
            padding: 1rem;
        }
        
        .header h1 {
            font-size: 2.5rem;
        }
        
        .control-row {
            flex-direction: column;
            gap: 1rem;
        }
        
        .control-item {
            min-width: 100%;
        }
        
        .dialog-header {
            flex-direction: column;
            gap: 1rem;
            align-items: flex-start;
        }
        
        .message {
            flex-direction: column;
            align-items: center;
            text-align: center;
        }
        
        .message-avatar {
            margin-bottom: 0.5rem;
        }
        
        .message-content::before {
            display: none;
        }
    }
    
    /* 滚动条样式 */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(135deg, #5a67d8, #6b46c1);
        }
        </style>
    """, unsafe_allow_html=True)

def load_dialog_data(dataset: str) -> List[Dict[str, Any]]:
    """加载指定数据集的对话数据"""
    file_path = f"data/{dataset}.txt"
    dialogs = []
    
    if not os.path.exists(file_path):
        st.error(f"Data file {file_path} does not exist")
        return dialogs
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 按空行分割，提取所有有效的对话
            # 每个对话是一个多行JSON对象，用空行分隔
            samples = [s.strip() for s in content.split('\n\n') if s.strip()]
            
            for sample in samples:
                try:
                    # 尝试解析JSON
                    dialog = json.loads(sample)
                    if isinstance(dialog, dict) and 'full_state' in dialog:
                        dialogs.append(dialog)
                except json.JSONDecodeError:
                    # 如果JSON解析失败，尝试eval（兼容旧格式）
                    try:
                        dialog = eval(sample)
                        if isinstance(dialog, dict) and 'full_state' in dialog:
                            dialogs.append(dialog)
                    except:
                        continue
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
    
    return dialogs

def display_dialog(dialog: Dict[str, Any], dialog_index: int, total_dialogs: int, dataset: str):
    """显示单个对话"""
    full_state = dialog.get('full_state', [])
    reward = dialog.get('reward', 0)
    
    # 过滤掉critic消息，只保留Seeker和Recommender
    filtered_messages = [msg for msg in full_state if msg.get('role', '').lower() not in ['critic']]
    
    # 对话头部
    st.markdown(f"""
    <div class="dialog-header">
        <div class="dialog-title">Dataset - {dataset}</div>
        <div class="dialog-title">Dialog - {dialog_index + 1}</div>

    </div>
    """, unsafe_allow_html=True)
        #     <div class="dialog-meta">
        #     <div class="meta-badge">Reward: {reward:.2f}</div>
        #     <div class="meta-badge">{len(filtered_messages)} Messages</div>
        # </div>
    # 显示消息
    for message in filtered_messages:
        role = message.get('role', '')
        content = message.get('content', '')
        
        # 确定角色类型
        if role.lower() in ['seeker', 'user']:
            role_class = 'user'
            avatar = '👤'
            role_name = 'User'
        elif role.lower() in ['recommender', 'assistant']:
            role_class = 'assistant'
            avatar = '🤖'
            role_name = 'Assistant'
        else:
            # 跳过其他角色类型
            continue
        
        # 渲染消息
        st.markdown(f"""
        <div class="message">
            <div class="message-avatar {role_class}">{avatar}</div>
            <div class="message-content {role_class}">
                <div class="message-role">{role_name}</div>
                <div class="message-text">{html.escape(str(content))}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    # 加载样式
    load_custom_css()
    
    # 初始化session state
    if 'dataset' not in st.session_state:
        st.session_state.dataset = "Inspired"
    if 'selected_dialog' not in st.session_state:
        st.session_state.selected_dialog = 0
    
    # 主容器
    main_container = st.container()
    
    # 头部
    with main_container:
        st.markdown("""
        <div class="header">
            <h1>RSO Dialogue Demo</h1>
            <p>Reinforced Strategy Optimization for Conversational Recommender Systems via Network-of-Experts</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 选择区域（精简：单行双列）
    with main_container:
        col1, col2 = st.columns([1, 1])
        with col1:
            dataset = st.selectbox(
                "Dataset",
                ["Inspired", "Redial"],
                index=["Inspired", "Redial"].index(st.session_state.dataset),
                key="dataset_selector",
                label_visibility="visible"
            )
            if dataset != st.session_state.dataset:
                st.session_state.dataset = dataset
                st.session_state.selected_dialog = 0

        dialogs = load_dialog_data(st.session_state.dataset)

        with col2:
            if dialogs:
                if st.session_state.selected_dialog >= len(dialogs):
                    st.session_state.selected_dialog = 0
                selected_dialog = st.selectbox(
                    "Dialog",
                    range(len(dialogs)),
                    format_func=lambda x: f"Dialog {x+1}",
                    index=st.session_state.selected_dialog,
                    key="dialog_selector",
                    label_visibility="visible"
                )
                st.session_state.selected_dialog = selected_dialog
            else:
                st.session_state.selected_dialog = 0
                st.info("No dialogs found in the selected dataset.")
    
    # 对话展示区域
    with main_container:
        if dialogs and st.session_state.selected_dialog < len(dialogs):
            display_dialog(
                dialogs[st.session_state.selected_dialog],
                st.session_state.selected_dialog,
                len(dialogs),
                dataset=st.session_state.dataset
            )
        else:
            st.markdown("""
            <div class="empty-state">
                <div class="empty-state-icon">💬</div>
                <h3>No Dialog Selected</h3>
                <p>Please select a dataset and dialog to view the conversation.</p>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
