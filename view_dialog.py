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
    
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
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
    
    /* 主容器 */
    .main-container {
        max-width: 1200px;
        margin: 0 auto;
        padding: 2rem;
        min-height: 100vh;
    }
    
    /* 头部区域 */
    .header {
        text-align: center;
        margin-bottom: 3rem;
        padding: 2rem 0;
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
    
    /* 控制面板 */
    .control-panel {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.2);
    }
    
    .control-row {
        display: flex;
        gap: 2rem;
        align-items: center;
        flex-wrap: wrap;
    }
    
    .control-item {
        flex: 1;
        min-width: 200px;
    }
    
    .control-item label {
        display: block;
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 0.5rem;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* 选择框样式 */
    .stSelectbox > div > div {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        font-size: 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stSelectbox > div > div:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
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

def display_dialog(dialog: Dict[str, Any], dialog_index: int, total_dialogs: int):
    """显示单个对话"""
    full_state = dialog.get('full_state', [])
    reward = dialog.get('reward', 0)
    
    # 过滤掉critic消息，只保留Seeker和Recommender
    filtered_messages = [msg for msg in full_state if msg.get('role', '').lower() not in ['critic']]
    
    # 对话头部
    st.markdown(f"""
    <div class="dialog-header">
        <div class="dialog-title">Dialog #{dialog_index + 1}</div>
        <div class="dialog-meta">
            <div class="meta-badge">Reward: {reward:.2f}</div>
            <div class="meta-badge">{len(filtered_messages)} Messages</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # 主容器
    st.markdown('<div class="main-container">', unsafe_allow_html=True)
    
    # 头部
    st.markdown("""
    <div class="header">
        <h1>AI Dialog Showcase</h1>
        <p>Explore high-quality conversational AI interactions across different datasets and scenarios</p>
    </div>
    """, unsafe_allow_html=True)
    
    # 控制面板
    st.markdown('<div class="control-panel">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="control-item">', unsafe_allow_html=True)
        st.markdown('<label>Dataset</label>', unsafe_allow_html=True)
        dataset = st.selectbox(
            "Select Dataset",
            ["Inspired", "Redial"],
            key="dataset_selector",
            label_visibility="collapsed"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # 控制面板结束
    
    # 加载数据
    dialogs = load_dialog_data(dataset)
    
    # 对话选择
    if dialogs:
        selected_dialog = st.selectbox(
            "Select Dialog",
            range(len(dialogs)),
            format_func=lambda x: f"Dialog {x+1}",
            key="dialog_selector",
            label_visibility="visible"
        )
    else:
        selected_dialog = 0
        st.info("No dialogs found in the selected dataset.")
    
    # 对话展示区域
    st.markdown('<div class="dialog-container">', unsafe_allow_html=True)
    
    if dialogs and selected_dialog < len(dialogs):
        display_dialog(dialogs[selected_dialog], selected_dialog, len(dialogs))
    else:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">💬</div>
            <h3>No Dialog Selected</h3>
            <p>Please select a dataset and dialog to view the conversation.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)  # 对话容器结束
    st.markdown('</div>', unsafe_allow_html=True)  # 主容器结束

if __name__ == "__main__":
    main()
