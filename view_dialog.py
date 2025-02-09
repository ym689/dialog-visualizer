import streamlit as st
import requests
import json
import ast
import base64

def parse_dialog_data(text):
    # 分割对话数据
    dialogs = text.strip().split('\n\n')
    parsed_dialogs = []
    
    for dialog in dialogs:
        try:
            # 解析每个对话的字典格式
            dialog_dict = ast.literal_eval(dialog)
            if 'dialog' in dialog_dict:
                parsed_dialogs.append(dialog_dict)
        except:
            continue
            
    return parsed_dialogs

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
    """从 GitHub 仓库获取指定路径下的文件列表"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return [file['name'] for file in response.json() if file['type'] == 'file' and file['name'].endswith('.txt')]
    return []

def read_github_file(repo_owner, repo_name, file_path, token):
    """从 GitHub 读取文件内容"""
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    
    # 添加错误信息打印
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        st.error(f"Response: {response.text}")
        return None
        
    try:
        content = response.json()['content']
        decoded_content = base64.b64decode(content).decode('utf-8')
        return decoded_content
    except Exception as e:
        st.error(f"Error decoding content: {str(e)}")
        return None

def main():
    # 设置页面配置
    st.set_page_config(
        page_title="Dialog Visualization",
        page_icon="💬",
        layout="wide"
    )
    
    # 密码验证
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        if st.sidebar.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()
    
    if not st.session_state.authenticated:
        password = st.text_input("Enter password", type="password")
        if password:
            if password == "next2025":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password")
        return

    # GitHub 配置
    try:
        GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    except Exception as e:
        st.error(f"Error reading GitHub token: {str(e)}")
        return

    REPO_OWNER = "ym689"
    REPO_NAME = "dialog-visualizer"
    DATA_PATH = "data"

    st.title("💬 Dialog Visualization")
    st.markdown("""
    Select a dialog file to visualize.
    """)

    # 获取可用的对话文件列表
    available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
    
    if not available_files:
        st.error(f"No dialog files found in the repository at {DATA_PATH}/")
        return

    # 文件选择
    selected_file = st.selectbox(
        "Select Dialog File",
        available_files,
        format_func=lambda x: x.replace('.txt', '')
    )

    if selected_file:
        try:
            # 读取选中的文件
            file_content = read_github_file(
                REPO_OWNER, 
                REPO_NAME, 
                f"{DATA_PATH}/{selected_file}", 
                GITHUB_TOKEN
            )
            
            if file_content is None:
                st.error("Failed to read the file from GitHub.")
                return

            # 解析对话数据
            dialogs = parse_dialog_data(file_content)
            
            if not dialogs:
                st.error("No valid dialogs found in the file.")
                return
            
            # 显示对话总数
            st.success(f"Successfully loaded {len(dialogs)} dialogs!")
            
            # 添加对话选择器
            col1, col2 = st.columns([1, 3])
            with col1:
                dialog_index = st.selectbox(
                    "Select Dialog",
                    range(len(dialogs)),
                    format_func=lambda x: f"Dialog {x+1}"
                )
            
            # 显示选中的对话
            display_dialog(dialogs[dialog_index])
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()