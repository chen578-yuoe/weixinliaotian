import streamlit as st
import json
import random
import pandas as pd
from openai import OpenAI

# 设置网页的标题和图标
st.set_page_config(page_title="聊天记录分析大师", page_icon="💬", layout="wide")

st.title("💬 微信聊天记录情感分析大师")
st.markdown("上传你的微信聊天记录导出文件 (JSON格式)，让 AI 帮你做一次深度的关系体检！")

# 侧边栏配置区
st.sidebar.header("⚙️ 基础设置")
# 让用户在网页上输入 API Key，比直接写在代码里更安全
api_key = st.sidebar.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
st.sidebar.markdown("[👉 点击去 DeepSeek 获取 API Key](https://platform.deepseek.com/)")

st.sidebar.header("🛠️ 分析设置")
method = st.sidebar.radio("抽取方式", ["最新记录", "随机抽取"])
max_lines = st.sidebar.slider("抽取行数", min_value=100, max_value=2000, value=1000, step=100)

# ==========================================
# 布局：左1 右2
# ==========================================
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### 📥 数据导出指引")
    
    # 使用卡片样式 (markdown html)
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h4 style="margin-top: 0;">为什么要先导出？</h4>
        <p style="font-size: 14px; color: #555;">受限于浏览器安全机制，网页无法直接读取你的微信数据，所以需要借助第三方工具将聊天记录导出为 <b>.json</b> 文件。</p>
        <hr>
        <h4 style="margin-top: 0;">极简导出教程</h4>
        <ol style="font-size: 14px; color: #555;">
            <li>下载并运行 <b>WeChatMsg</b> 或 <b>CipherTalk</b></li>
            <li>在软件中解析你的微信数据</li>
            <li>选中要分析的单聊/群聊，点击 <b>导出为 JSON</b></li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # 提供下载按钮（这里使用链接形式模拟按钮）
    st.link_button("👉 下载 CipherTalk (推荐)", "https://miyu.aiqji.com/", use_container_width=True)

with col_right:
    st.markdown("### 🔍 主分析区")
    
    # 单聊/群聊模式选择
    chat_mode = st.selectbox(
        "我们要分析的是什么类型的聊天？",
        ["单人纯爱/撕逼 (单聊)", "多人狂欢群聊 (群聊)"]
    )
    
    # 文件上传组件
    uploaded_file = st.file_uploader("📂 请上传你的微信聊天记录文件 (.json)", type=["json"])

    # 当用户点击“开始分析”按钮时
    if st.button("🚀 开始分析", type="primary", use_container_width=True):
        # 检查是否填了必要的信息
        if not api_key:
            st.error("⚠️ 请先在左侧侧边栏输入你的 API Key！")
            st.stop()
        if not uploaded_file:
            st.error("⚠️ 请先上传聊天记录 JSON 文件！")
            st.stop()

        # 1. 读取并处理文件
        try:
            data = json.load(uploaded_file)
            messages = data.get('messages', [])
            
            # 过滤出有文字内容的聊天记录
            valid_messages = [msg for msg in messages if 'content' in msg and isinstance(msg['content'], str)]
            
            # 根据用户的选择抽取记录
            if len(valid_messages) > max_lines:
                if method == "最新记录":
                    selected_msgs = valid_messages[-max_lines:]
                else:
                    selected_msgs = random.sample(valid_messages, max_lines)
            else:
                selected_msgs = valid_messages
                
            # 转换格式
            formatted_chat = []
            for msg in selected_msgs:
                name = msg.get('accountName', '未知')
                content = msg.get('content', '')
                formatted_chat.append(f"{name}: {content}")
                
            chat_text = "\n".join(formatted_chat)
            
            st.success(f"✅ 成功读取文件！共发现 {len(messages)} 条记录，已提取 {len(selected_msgs)} 条进行分析。")
            
            # --- 真实数据统计图表 ---
            st.markdown("---")
            st.markdown("### 📈 真实数据统计图表")
            
            # 统计发言数和字数
            stats = {}
            for msg in selected_msgs:
                name = msg.get('accountName', '未知')
                content = msg.get('content', '')
                if name not in stats:
                    stats[name] = {"消息数": 0, "总字数": 0}
                stats[name]["消息数"] += 1
                stats[name]["总字数"] += len(content)
                
            # 提取前 N 名发言者 (单聊取前2，群聊取前5)
            top_n = 2 if "单聊" in chat_mode else 5
            sorted_users = sorted(stats.items(), key=lambda x: x[1]["消息数"], reverse=True)[:top_n]
            
            if len(sorted_users) > 0:
                # 准备 DataFrame
                users = [item[0] for item in sorted_users]
                msg_counts = [item[1]["消息数"] for item in sorted_users]
                word_counts = [item[1]["总字数"] for item in sorted_users]
                
                df = pd.DataFrame({
                    "用户": users,
                    "消息数量": msg_counts,
                    "总字数": word_counts
                })
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("##### 🏆 谁是话痨？(消息数对比)")
                    st.bar_chart(df.set_index("用户")["消息数量"], color="#FF4B4B")
                with col_c2:
                    st.markdown("##### ✍️ 谁爱写小作文？(总字数对比)")
                    st.bar_chart(df.set_index("用户")["总字数"], color="#0068C9")
            # ----------------------------------

        except Exception as e:
            st.error(f"❌ 读取文件失败: {e}")
            st.stop()

        # 2. 调用大模型分析
        st.markdown("---")
        st.markdown("### 🤖 情感大师分析报告")
        
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # 根据不同模式选择 Prompt
        if "单聊" in chat_mode:
            prompt = f"""你现在是一个“犀利的情感分析大师”，擅长一针见血地分析两人关系。
请阅读以下这{len(selected_msgs)}条真实的微信聊天记录，并输出一份精美的分析报告。

你的报告必须包含以下四个板块，排版要美观：
1. 【关系神级认证】：给这段关系贴上一个爆笑、精准的标签（例如：表面兄弟、深夜树洞、备胎工具人、灵魂伴侣、相爱相杀等），并用一两句话解释原因。
2. 【权力结构分析】：分析两人中谁分享欲更强？谁才是话题的掌控者？谁更容易冷场？（注意：直接用文字段落输出你的分析，绝对不要画任何 ASCII 字符图表或线条！）
3. 【趣味关键词】：总结出两人聊得最多的高频词、口头禅，或者特殊的梗。
4. 【综合亲密度分值】：给出一个百分制的亲密度打分，并附带一句犀利的总结语。

语气要求：幽默、犀利、精准、可以带点调侃但不要冒犯。

以下是聊天记录内容：
{chat_text}
"""
        else:
            prompt = f"""你现在是一个“犀利的吃瓜大师”，擅长一针见血地分析群聊生态。
请阅读以下这{len(selected_msgs)}条真实的微信群聊记录，并输出一份精美的群聊生态分析报告。

你的报告必须包含以下三个板块，排版要美观：
1. 【群内身份牌】：为群里最活跃的几个人颁发身份牌（例如：活跃气氛组、潜水复读机、话题终结者、懂王、捧哏大师等），并用幽默的语言解释为什么给ta发这个牌。
2. 【小团体雷达】：分析群里哪几个人互动最频繁、接梗最默契？有没有明显的“抱团”现象或者“CP”感？（注意：直接用文字段落输出你的分析，绝对不要画任何 ASCII 字符图表或线条！）
3. 【年度吃瓜总结】：总结这个群聊经常聚在一起聊什么主题？（八卦、工作、游戏、摸鱼等），并用一句犀利、搞笑的话总结这个群的核心气质。

语气要求：幽默、犀利、精准、可以带点调侃但不要冒犯。

以下是聊天记录内容：
{chat_text}
"""

        try:
            # 显示一个加载动画
            with st.spinner("AI 大师正在疯狂阅读聊天记录并撰写报告... (可能需要半分钟)"):
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "你是一个幽默、犀利的情感分析大师。"},
                        {"role": "user", "content": prompt}
                    ],
                    stream=True
                )
                
                # Streamlit 自带 write_stream，完美支持流式打字机效果！
                st.write_stream(response)
                
        except Exception as e:
            st.error(f"❌ 调用大模型时出错，请检查 API Key 是否正确或余额是否充足。\n详细错误：{e}")
