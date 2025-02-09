import streamlit as st
import requests
import json
import base64
import urllib.parse
import html

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
    
    st.write("Requesting file from:", url)  # 显示请求URL
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    response = requests.get(url, headers=headers)
    st.write("File API Response Status:", response.status_code)  # 显示响应状态码
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        st.error(f"Response: {response.text}")
        return None
        
    try:
        content = response.json()['content']
        decoded_content = base64.b64decode(content).decode('utf-8')
        
        # 显示解码后的内容预览
        st.write("File content preview (first 200 chars):", decoded_content[:200])
        
        # 显示行数统计
        lines = [line for line in decoded_content.split('\n') if line.strip()]
        st.write(f"Number of non-empty lines in file: {len(lines)}")
        
        # 尝试解析第一行
        if lines:
            try:
                first_dialog = json.loads(lines[0])
                st.write("Successfully parsed first line")
                st.write("First dialog keys:", list(first_dialog.keys()))
            except json.JSONDecodeError as e:
                st.error(f"Error parsing first line: {str(e)}")
                st.write("First line content:", lines[0][:200])
        
        return decoded_content
    except Exception as e:
        st.error(f"Error decoding content: {str(e)}")
        st.write("Full error:", str(e))
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
            cursor: pointer;
        }
        
        .popup-menu {
            display: none;
            position: absolute;
            background: white;
            border: 1px solid #ddd;
            padding: 5px;
            z-index: 1000;
        }
        
        .message:hover .popup-menu {
            display: block;
        }
        
        .reward:hover .popup-menu {
            display: block;
        }
    </style>
    """, unsafe_allow_html=True)

    current_turn = []
    turn_count = 0
    
    for msg in dialog_data["full_state"]:
        role = msg["role"]
        if role in ["Seeker", "Recommender"]:
            current_turn.append(msg)
            
            # Skip the initial "Hello" message
            if role == "Seeker" and msg["content"] == "Hello" and turn_count == 0:
                continue
                
            # Create unique keys for each message
            msg_key = f"{role}_{turn_count}_{hash(str(msg['content']))}"
            
            # Create message container
            with st.container():
                if role == "Recommender":
                    with st.expander(msg["content"], expanded=True):
                        st.write("User Preference:")
                        if st.button("Show", key=f"pref_{msg_key}"):
                            st.write(msg.get("user_preference", ""))
                        st.write("Recommender Prompt:")
                        if st.button("Show", key=f"prompt_{msg_key}"):
                            st.write(msg.get("Recommender_prompt", ""))
                else:  # Seeker
                    with st.expander(msg["content"], expanded=True):
                        st.write("Seeker Prompt:")
                        if st.button("Show", key=f"prompt_{msg_key}"):
                            st.write(msg.get("Seeker_prompt", ""))
            
            # If we have a complete turn, show reward
            if len(current_turn) == 2:
                turn_count += 1
                # Find the next critic message
                critic_data = None
                for next_msg in dialog_data["full_state"]:
                    if next_msg["role"] == "critic" and dialog_data["full_state"].index(next_msg) > dialog_data["full_state"].index(current_turn[-1]):
                        critic_data = next_msg
                        break
                
                if critic_data:
                    reward = critic_data.get("reward", 0)
                    reward_key = f"reward_{turn_count}_{hash(str(critic_data))}"
                    
                    with st.expander(f"Reward: {reward}", expanded=True):
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Content", key=f"content_{reward_key}"):
                                content_list = critic_data.get("content", [])
                                for content in content_list:
                                    st.write(content)
                        with col2:
                            if st.button("Critique Prompt", key=f"critique_{reward_key}"):
                                st.write(critic_data.get("critic_prompt", ""))
                
                current_turn = []

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
        st.write("GitHub token loaded successfully")  # 确认token已加载
    except Exception as e:
        st.error(f"Error reading GitHub token: {str(e)}")
        return

    REPO_OWNER = "ym689"
    REPO_NAME = "dialog-visualizer"
    DATA_PATH = "data/conversation_history"

    st.title("Dialog Visualization")
    
    # 显示配置信息
    st.write("Accessing repository:", f"{REPO_OWNER}/{REPO_NAME}")
    st.write("Looking for files in:", DATA_PATH)
    
    available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
    if not available_files:
        st.error("No dialog files found.")
        return

    selected_file = st.selectbox("Select Dialog File", available_files)
    
    if selected_file:
        st.write("Selected file:", selected_file)
        content = read_github_file(REPO_OWNER, REPO_NAME, f"{DATA_PATH}/{selected_file}", GITHUB_TOKEN)
        
        if content:
            st.write("File content loaded successfully")
            try:
                # 分行处理
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                st.write(f"Processing {len(lines)} lines")
                
                dialogs = []
                for i, line in enumerate(lines):
                    try:
                        dialog = json.loads(line)
                        dialogs.append(dialog)
                        if i == 0:  # 显示第一个对话的结构
                            st.write("First dialog structure:", {
                                k: type(v).__name__ for k, v in dialog.items()
                            })
                    except json.JSONDecodeError as e:
                        st.error(f"Error parsing line {i+1}: {str(e)}")
                        st.write(f"Problematic line preview: {line[:200]}")
                
                if dialogs:
                    st.write(f"Successfully parsed {len(dialogs)} dialogs")
                    dialog_index = st.selectbox(
                        "Select Dialog",
                        range(len(dialogs)),
                        format_func=lambda x: f"Dialog {x+1}"
                    )
                    format_dialog(dialogs[dialog_index])
                else:
                    st.error("No valid dialogs found in the file.")
            except Exception as e:
                st.error(f"Error processing dialogs: {str(e)}")
                st.write("Full error:", str(e))

if __name__ == "__main__":
    main()