import streamlit as st
import requests
import json
import ast
import base64
import urllib.parse  # 添加这个导入
import gradio as gr
import html

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
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        st.error(f"Response: {response.text}")
        return []
    
    return [file['name'] for file in response.json() if file['type'] == 'file' and file['name'].endswith('.txt')]

def read_github_file(repo_owner, repo_name, file_path, token):
    """从 GitHub 读取文件内容"""
    # URL 编码文件路径
    encoded_path = '/'.join(urllib.parse.quote(part) for part in file_path.split('/'))
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{encoded_path}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # 打印调试信息（不包含 token）
    st.write(f"Attempting to read file: {file_path}")
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        st.error(f"GitHub API Error: {response.status_code}")
        st.error(f"Response: {response.text}")
        st.write("Full URL (without token):", url)
        return None
        
    try:
        content = response.json()['content']
        decoded_content = base64.b64decode(content).decode('utf-8')
        return decoded_content
    except Exception as e:
        st.error(f"Error decoding content: {str(e)}")
        return None

def format_filename(filename):
    """美化文件名显示"""
    # 从文件名中提取 epoch 数字
    if 'epoch-' in filename:
        epoch = filename.split('epoch-')[1].split('-')[0]
        return f"Dialog Record - Epoch {epoch}"
    return filename.replace('.txt', '')

def display_prompt_template(content):
    """显示提示模板"""
    st.text_area("Prompt Template", value=content, height=400, disabled=True)

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
    </style>
    """, unsafe_allow_html=True)

    current_turn = []
    
    for msg in dialog_data["full_state"]:
        role = msg["role"]
        if role in ["Seeker", "Recommender"]:
            current_turn.append(msg)
            
            # Create message container
            with st.container():
                col1, col2 = st.columns([10, 2])
                
                with col1:
                    st.markdown(f"""
                        <div class="message {role.lower()}">
                            {html.escape(msg["content"])}
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if role == "Recommender":
                        if st.button("📋", key=f"rec_{hash(msg['content'])}"):
                            with st.expander("Additional Info"):
                                st.text("User Preference:")
                                st.write(msg.get("user_preference", ""))
                                st.text("Recommender Prompt:")
                                st.write(msg.get("Recommender_prompt", ""))
                    elif role == "Seeker":
                        if st.button("📋", key=f"seek_{hash(msg['content'])}"):
                            with st.expander("Additional Info"):
                                st.text("Seeker Prompt:")
                                st.write(msg.get("Seeker_prompt", ""))
            
            # If we have a complete turn, show reward
            if len(current_turn) == 2:
                critic_data = None
                for turn_msg in current_turn:
                    if turn_msg.get("role") == "critic":
                        critic_data = turn_msg
                        break
                
                if critic_data:
                    reward = critic_data.get("reward", 0)
                    st.markdown(f"""
                        <div class="reward">
                            Reward: {reward}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("📋", key=f"reward_{hash(str(current_turn))}"):
                        with st.expander("Reward Details"):
                            st.text("Content:")
                            content_list = critic_data.get("content", [])
                            for content in content_list:
                                st.write(content)
                            st.text("Critique Prompt:")
                            st.write(critic_data.get("critic_prompt", ""))
                
                current_turn = []

def view_dialog(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dialog_data = json.loads(f.read())
        format_dialog(dialog_data)
    except Exception as e:
        st.error(f"Error loading dialog: {str(e)}")

def launch_interface():
    iface = gr.Interface(
        fn=view_dialog,
        inputs=gr.Textbox(label="Dialog file path"),
        outputs=gr.HTML(),
        title="Dialog Visualizer",
        description="Enter the path to a dialog JSON file to visualize it."
    )
    iface.launch()

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
        if st.button("Logout"):
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
    DATA_PATH = "data/conversation_history"

    st.title("💬 Dialog Visualization")
    
    # 获取对话文件列表
    available_files = get_github_files(REPO_OWNER, REPO_NAME, DATA_PATH, GITHUB_TOKEN)
    
    if not available_files:
        st.error(f"No dialog files found in the repository at {DATA_PATH}/")
        return

    # 文件选择
    selected_file = st.selectbox(
        "Select Dialog File",
        available_files,
        format_func=format_filename
    )

    if selected_file:
        try:
            file_content = read_github_file(
                REPO_OWNER, 
                REPO_NAME, 
                f"{DATA_PATH}/{selected_file}", 
                GITHUB_TOKEN
            )
            
            if file_content is None:
                st.error("Failed to read the file from GitHub.")
                return

            dialogs = parse_dialog_data(file_content)
            
            if not dialogs:
                st.error("No valid dialogs found in the file.")
                return
            
            st.success(f"Successfully loaded {len(dialogs)} dialogs!")
            
            dialog_index = st.selectbox(
                "Select Dialog",
                range(len(dialogs)),
                format_func=lambda x: f"Dialog {x+1}"
            )
            
            display_dialog(dialogs[dialog_index])
            
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    main()