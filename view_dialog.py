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
    
    # 添加调试信息
    st.write("GitHub API Response Status:", response.status_code)
    st.write("GitHub API Response:", response.text[:200])  # 显示响应内容的前200个字符
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        return []
        
    files = [file['name'] for file in response.json() if file['type'] == 'file' and file['name'].endswith('.txt')]
    st.write("Found files:", files)  # 显示找到的文件
    return files

def read_github_file(repo_owner, repo_name, file_path, token):
    """从 GitHub 读取文件内容"""
    encoded_path = '/'.join(urllib.parse.quote(part) for part in file_path.split('/'))
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{encoded_path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
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
                st.error(f"Error parsing line: {str(e)}")
                continue
        
        return dialogs
        
    except Exception as e:
        st.error(f"Error processing content: {str(e)}")
        return None

def format_filename(filename):
    """美化文件名显示"""
    if 'epoch-' in filename:
        epoch = filename.split('epoch-')[1].split('-')[0]
        return f"Dialog Record - Epoch {epoch}"
    return filename.replace('.txt', '')

def format_dialog(dialog_data):
    st.markdown("""
    <style>
        .message {
            margin: 10px;
            padding: 10px;
            border-radius: 5px;
            position: relative;
        }
        
        .seeker {
            background-color: #e3f2fd;
            margin-left: 20px;
        }
        
        .recommender {
            background-color: #f5f5f5;
            margin-right: 20px;
        }
        
        .reward {
            margin: 10px;
            padding: 5px;
            background-color: #fff3e0;
            border-radius: 3px;
        }
        
        .hello-message {
            margin: 10px;
            padding: 10px;
            background-color: #e8eaf6;
            border-radius: 5px;
            margin-left: 20px;
            opacity: 0.8;
        }
    </style>
    """, unsafe_allow_html=True)

    messages = dialog_data["full_state"]
    
    # 确保第一条消息是 Seeker 的 Hello
    if messages and messages[0]["role"] == "Seeker" and messages[0]["content"] == "Hello":
        # 显示 Hello 消息，无需展开选项
        st.markdown(f"""
            <div class="hello-message">
                {html.escape(messages[0]["content"])}
            </div>
        """, unsafe_allow_html=True)
        
        # 处理后续的对话
        current_turn = []
        for i in range(1, len(messages)):
            msg = messages[i]
            role = msg["role"]
            
            if role == "Recommender":
                # 显示 Recommender 消息
                st.markdown(f"""
                    <div class="message recommender">
                        {html.escape(str(msg["content"]))}
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    with st.expander("User Preference"):
                        st.write(msg.get("user_preference", ""))
                with col2:
                    with st.expander("Recommender Prompt"):
                        st.write(msg.get("Recommender_prompt", ""))
                        
                current_turn = [msg]
                
            elif role == "Seeker" and current_turn:
                # 显示 Seeker 消息
                st.markdown(f"""
                    <div class="message seeker">
                        {html.escape(str(msg["content"]))}
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander("Seeker Prompt"):
                    st.write(msg.get("Seeker_prompt", ""))
                    
                current_turn.append(msg)
                
                # 寻找下一个 critic 消息
                for next_msg in messages[i+1:]:
                    if next_msg["role"] == "critic":
                        reward = next_msg.get("reward", 0)
                        st.markdown(f"""
                            <div class="reward">
                                Reward: {reward}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            with st.expander("Content"):
                                content_list = next_msg.get("content", [])
                                for idx, content in enumerate(content_list, 1):
                                    st.markdown(f"**Output {idx}:**")
                                    st.write(content)
                        with col2:
                            with st.expander("Critique Prompt"):
                                st.write(next_msg.get("critic_prompt", ""))
                        break
                
                current_turn = []
    else:
        st.error("Invalid dialog format: Dialog should start with Seeker saying 'Hello'")

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

def main():
    st.set_page_config(page_title="Dialog Visualization", layout="wide")
    
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if not st.session_state.authenticated:
        password = st.text_input("Enter password", type="password")
        if password:
            if password == "next2025":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return

    try:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    except Exception as e:
        st.error(f"Error reading GitHub token: {str(e)}")
        return

    REPO_OWNER = "ym689"
    REPO_NAME = "dialog-visualizer"
    DATA_PATH = "data/conversation_history"

    st.title("Dialog Visualization")
    
    available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
    if not available_files:
        st.error("No dialog files found.")
        return

    selected_file = st.selectbox("Select Dialog File", available_files)
    
    if selected_file:
        dialogs = read_github_file(REPO_OWNER, REPO_NAME, f"{DATA_PATH}/{selected_file}", GITHUB_TOKEN)
        
        if dialogs:
            st.success(f"Successfully loaded {len(dialogs)} dialogs")
            
            dialog_index = st.selectbox(
                "Select Dialog",
                range(len(dialogs)),
                format_func=lambda x: f"Dialog {x+1}"
            )
            
            format_dialog(dialogs[dialog_index])

if __name__ == "__main__":
    main()