import streamlit as st
import os
from openai import OpenAI
import plotly.graph_objects as go
import json
import base64

# --- Page Config ---
st.set_page_config(
    page_title="AI Speech Coach (Adaptive)",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar: Settings ---
st.sidebar.title("⚙️ 演講情境設定")

personality = st.sidebar.radio(
    "1. 性格設定 (Personality)",
    options=["I 型 (內向/沉穩)", "E 型 (外向/熱情)"],
    index=0
)

coaching_style = st.sidebar.selectbox(
    "2. 教練風格 (Coaching Style)",
    options=["溫柔鼓勵 (Supportive)", "平衡回饋 (Balanced)", "嚴格魔鬼教練 (Strict/Critical)"],
    index=1
)

scenario = st.sidebar.selectbox(
    "3. 演講場景 (Scenario) [關鍵邏輯]",
    options=[
        "學位口試/課堂報告 (Thesis Defense/Class Report)",
        "科普演講/公眾推廣 (Public Outreach)",
        "學術研討會 (Conference Presentation)"
    ],
    index=0
)

audience = st.sidebar.text_input(
    "4. 預設聽眾 (Audience)",
    value="Professors and Graduate Students",
    help="例如: Professors, General Public, High School Students"
)

api_key = st.sidebar.text_input(
    "5. OpenAI API Key",
    type="password"
)

# --- Main Area ---
st.title("🎙️ AI 專業演講教練")
st.markdown("---")

uploaded_file = st.file_uploader("上傳您的演講錄音 (MP3, WAV, M4A)", type=["mp3", "wav", "m4a"])

# --- Analysis Logic ---

def encode_audio(file):
    return base64.b64encode(file.read()).decode("utf-8")

def analyze_audio(client, audio_base64, settings):
    # Construct System Prompt based on Settings
    
    # 1. Personality & Style
    style_instruction = ""
    if "Supportive" in settings['style']:
        style_instruction = "You are a warm, encouraging coach. Focus on potential and strengths mainly. Use gentle language."
    elif "Strict" in settings['style']:
        style_instruction = "You are a very strict, critical coach. Focus on logic holes, weak arguments, and mistakes. Be direct."
    else: # Balanced
        style_instruction = "You are a balanced professional coach. diverse feedback between pros and cons."

    # 2. Scenario specific logic
    opening_instruction = ""
    scenario_type = ""
    if "Thesis Defense" in settings['scenario']:
        scenario_type = "Defense"
        opening_instruction = "For the 'Opening Analysis', focus heavily on **Structure & Problem Statement**. Did the speaker clearly define the research gap? Is the outline logical?"
    elif "Public Outreach" in settings['scenario']:
        scenario_type = "Public"
        opening_instruction = "For the 'Opening Analysis', focus heavily on **The Hook**. Did they grab attention immediately? Was it engaging/fun?"
    else: # Conference
        scenario_type = "Conference"
        opening_instruction = "For the 'Opening Analysis', focus on professional delivery and clarity of contribution."

    # 3. Audience check
    audience_instruction = f"Check if the terminology density is appropriate for this audience: {settings['audience']}."

    system_prompt = f"""
    You are an expert Speech Coach. Output JSON only.
    Language: Traditional Chinese (繁體中文) for all user-facing content.
    
    Settings:
    - Coach Personality: {settings['personality']}
    - Style: {style_instruction}
    - Scenario: {settings['scenario']} ({opening_instruction})
    - Audience: {settings['audience']} ({audience_instruction})

    Analyze the provided audio. Return a JSON object with this exact structure:
    {{
        "summary": {{
            "score": <int 0-100>,
            "wpm": <int>,
            "confidence_level": "<string e.g. High/Medium/Low>"
        }},
        "radar_data": {{
            "professionalism": <int 0-10>,
            "logic_structure": <int 0-10>,
            "vocal_expression": <int 0-10>,
            "time_management": <int 0-10>,
            "audience_fit": <int 0-10>
        }},
        "opening_analysis": {{
            "title": "<string based on scenario e.g. 研究動機與架構清晰度 or 開場吸引力>",
            "content": "<string analysis of the first minute>"
        }},
        "feedback_tabs": {{
            "strengths": ["<string point 1>", "<string point 2>", ...],
            "improvements": ["<string point 1>", "<string point 2>", ...],
            "simulated_qa": ["<string question 1>", "<string question 2>"]
        }}
    }}
    """

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-audio-preview",
            modalities=["text"],
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        { 
                            "type": "input_audio", 
                            "input_audio": { 
                                "data": audio_base64, 
                                "format": "wav" 
                            }
                        }
                    ]
                }
            ]
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}

# --- Execution ---

if uploaded_file is not None:
    if st.button("🚀 開始全方位分析"):
        if not api_key:
            st.error("請先輸入 OpenAI API Key 🔑")
        else:
            with st.spinner("正在分析您的演講 (GPT-4o Audio)..."):
                # Prepare Client
                client = OpenAI(api_key=api_key)
                
                # Audio Processing
                # Note: For simple Streamlit file objects, we can read directly.
                # In a real app, might need to ensure format compatibility.
                # Here we assume the user uploads a compatible format or we send as is (api supports mp3, wav).
                # The format param in input_audio maps to wav/mp3. Let's assume wav for generic bytes or try to detect.
                # For this demo, let's send strictly as 'wav' or 'mp3' based on extension, defaulting to wav.
                file_ext = uploaded_file.name.split('.')[-1].lower()
                audio_format = "mp3" if file_ext == "mp3" else "wav" 
                
                # Encode
                audio_b64 = encode_audio(uploaded_file)
                
                # Analyze
                settings = {
                    "personality": personality,
                    "style": coaching_style,
                    "scenario": scenario,
                    "audience": audience
                }
                
                result = analyze_audio(client, audio_b64, settings)
                
                if "error" in result:
                    st.error(f"Analysis Failed: {result['error']}")
                else:
                    # --- Display Results ---
                    
                    # 1. Summary Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("總體評分 (Score)", result['summary']['score'])
                    c2.metric("語速 (WPM)", result['summary']['wpm'])
                    c3.metric("自信度", result['summary']['confidence_level'])
                    
                    st.markdown("---")
                    
                    # 2. Radar Chart
                    col_chart, col_opening = st.columns([1, 1])
                    
                    with col_chart:
                        st.subheader("五維雷達分析")
                        radar_data = result['radar_data']
                        categories = ['專業度', '邏輯架構', '語氣表達', '時間掌控', '聽眾適配度']
                        values = [
                            radar_data['professionalism'],
                            radar_data['logic_structure'],
                            radar_data['vocal_expression'],
                            radar_data['time_management'],
                            radar_data['audience_fit']
                        ]
                        
                        fig = go.Figure(data=go.Scatterpolar(
                            r=values,
                            theta=categories,
                            fill='toself'
                        ))
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 10]
                                )),
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                    with col_opening:
                        st.subheader(f"🔍 {result['opening_analysis']['title']}")
                        st.info(result['opening_analysis']['content'])
                    
                    st.markdown("---")
                    
                    # 3. Detailed Tabs
                    tab1, tab2, tab3 = st.tabs(["🌟 優點 (Strengths)", "💡 改進建議 (Improvements)", "❓ 模擬提問 (Simulated Q&A)"])
                    
                    with tab1:
                        for item in result['feedback_tabs']['strengths']:
                            st.success(f"✅ {item}")
                            
                    with tab2:
                        for item in result['feedback_tabs']['improvements']:
                            st.warning(f"⚠️ {item}")
                            
                    with tab3:
                        st.markdown("### 模擬教授/聽眾提問")
                        for i, q in enumerate(result['feedback_tabs']['simulated_qa'], 1):
                            st.markdown(f"**Q{i}:** {q}")
