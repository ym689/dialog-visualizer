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
    dialog_html = ""
    current_turn = []
    
    def create_popup_menu(options, content_map):
        menu_id = f"menu_{hash(str(content_map))}"
        options_html = "".join([
            f'<div onclick="showContent(\'{menu_id}_{i}\', `{html.escape(str(content))}`)">{option}</div>'
            for i, (option, content) in enumerate(zip(options, content_map))
        ])
        return f'''
            <div class="popup-menu" id="{menu_id}">
                {options_html}
            </div>
        '''

    def format_message(role, content, additional_data=None):
        class_name = role.lower()
        hover_attr = f'onmouseover="showMenu(this, \'{class_name}\')" onmouseout="hideMenu(this, \'{class_name}\')"'
        
        message_html = f'<div class="message {class_name}" {hover_attr}>{content}'
        
        if additional_data:
            if role == "Recommender":
                options = ["user_preference", "Recommender_prompt"]
                content_map = [additional_data.get("user_preference", ""), additional_data.get("Recommender_prompt", "")]
                message_html += create_popup_menu(options, content_map)
            elif role == "Seeker":
                options = ["Seeker_prompt"]
                content_map = [additional_data.get("Seeker_prompt", "")]
                message_html += create_popup_menu(options, content_map)
                
        message_html += '</div>'
        return message_html

    def format_turn_reward(turn_data):
        if not turn_data:
            return ""
        
        reward = 0
        critic_data = None
        for msg in turn_data:
            if msg["role"] == "critic":
                critic_data = msg
                reward = msg.get("reward", 0)
                break
                
        if critic_data:
            reward_id = f"reward_{hash(str(critic_data))}"
            content_list = critic_data.get("content", [])
            content_html = "<br>".join([html.escape(str(c)) for c in content_list])
            critique_prompt = critic_data.get("critic_prompt", "")
            
            return f'''
                <div class="reward" 
                    onmouseover="showMenu(this, 'reward')" 
                    onmouseout="hideMenu(this, 'reward')">
                    Reward: {reward}
                    <div class="popup-menu" id="{reward_id}">
                        <div onclick="showContent('{reward_id}_content', `{content_html}`)">content</div>
                        <div onclick="showContent('{reward_id}_prompt', `{html.escape(critique_prompt)}`)">critique_prompt</div>
                    </div>
                </div>
            '''
        return ""

    for msg in dialog_data["full_state"]:
        role = msg["role"]
        if role in ["Seeker", "Recommender"]:
            current_turn.append(msg)
            dialog_html += format_message(role, msg["content"], msg)
            
            # If we have a complete turn (both Seeker and Recommender)
            if len(current_turn) == 2:
                dialog_html += format_turn_reward(current_turn)
                current_turn = []
                
    return f'''
    <div id="dialog">
        {dialog_html}
    </div>
    
    <div id="modal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <pre id="modal-text"></pre>
        </div>
    </div>
    
    <script>
        function showMenu(element, type) {{
            const menu = element.querySelector('.popup-menu');
            if (menu) {{
                menu.style.display = 'block';
                menu.style.left = '100%';
                menu.style.top = '0';
            }}
        }}
        
        function hideMenu(element, type) {{
            const menu = element.querySelector('.popup-menu');
            if (menu) {{
                menu.style.display = 'none';
            }}
        }}
        
        function showContent(id, content) {{
            const modal = document.getElementById('modal');
            const modalText = document.getElementById('modal-text');
            modalText.textContent = content;
            modal.style.display = 'block';
        }}
        
        // Close modal when clicking on X or outside
        document.querySelector('.close').onclick = function() {{
            document.getElementById('modal').style.display = 'none';
        }}
        
        window.onclick = function(event) {{
            const modal = document.getElementById('modal');
            if (event.target == modal) {{
                modal.style.display = 'none';
            }}
        }}
    </script>
    
    <style>
        .message {{
            margin: 10px;
            padding: 10px;
            border-radius: 5px;
            position: relative;
        }}
        
        .seeker {{
            background-color: #e3f2fd;
            margin-left: 20px;
        }}
        
        .recommender {{
            background-color: #f5f5f5;
            margin-right: 20px;
        }}
        
        .reward {{
            margin: 10px;
            padding: 5px;
            background-color: #fff3e0;
            border-radius: 3px;
            position: relative;
        }}
        
        .popup-menu {{
            display: none;
            position: absolute;
            background-color: white;
            border: 1px solid #ddd;
            padding: 5px;
            box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            z-index: 1000;
        }}
        
        .popup-menu div {{
            padding: 5px;
            cursor: pointer;
        }}
        
        .popup-menu div:hover {{
            background-color: #f0f0f0;
        }}
        
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.4);
            z-index: 1001;
        }}
        
        .modal-content {{
            background-color: white;
            margin: 15% auto;
            padding: 20px;
            border: 1px solid #888;
            width: 80%;
            max-height: 70vh;
            overflow-y: auto;
        }}
        
        .close {{
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: black;
        }}
    </style>
    '''

def view_dialog(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            dialog_data = json.loads(f.read())
        return format_dialog(dialog_data)
    except Exception as e:
        return f"Error loading dialog: {str(e)}"

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