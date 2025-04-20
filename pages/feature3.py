import streamlit as st
from openai import OpenAI
import numpy as np
import pandas as pd
import os
import openai
import requests
from pathlib import Path
import json
import re
import random
import tempfile



client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


tab1, tab2, tab3 = st.tabs(["Water Fun Facts", "Water Quality FAQ", "Water Quality Quiz"])

# Language Options
option = st.selectbox(
"Select language", ("English", "Spanish", "Vietnamese", "Mandarin", "Korean")
)
st.write("You selected:", option)

with tab1:
    st.title("🌊Water Fun Fact🌊")

    # Initialize session state
    if "fun_fact" not in st.session_state:
        st.session_state.fun_fact = ""
        st.session_state.fun_fact_audio = None

    # Fun Fact generator
    def get_completion(prompt, model="gpt-3.5-turbo"):
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert on water quality."},
                {"role": "user", "content": prompt},
            ]
        )
        return completion.choices[0].message.content

    # TTS helper
    def speak_text(text, voice="nova"):
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(response.read())
                return tmp.name
        except Exception as e:
            st.warning("TTS failed.")
            return None

    # Form for user input
    with st.form(key="chat"):
        prompt = st.text_input("Want a local fact? Enter your city:")
        submitted = st.form_submit_button("🔍 Generate a Fun Fact")

    # After form submission
    if submitted and prompt:
        fact_prompt = (
            f"Give me one short, interesting fun fact about {prompt} water quality, "
            f"translate the generated text in {option} language too. Start it with 'Did you know?'"
        )
        description = get_completion(fact_prompt)
        st.session_state.fun_fact = description
        st.session_state.fun_fact_audio = speak_text(description)

    # Display fun fact
    if st.session_state.fun_fact:
        st.write(st.session_state.fun_fact)

        if st.button("🔈 Play fun fact"):
            if st.session_state.fun_fact_audio:
                st.audio(st.session_state.fun_fact_audio)
            else:
                st.warning("Audio not available.")

                

with tab2:
    questions = [
        "What is pH in water?",
        "How can I measure water quality at home?",
        "Why is chlorine added to water?",
        "What are nitrates and why are they bad?",
        "How is my water cleaned?",
        "What are safe levels of lead in water?",
        "Where are the water treatment plants near me?"
    ]

    st.title("Water Quality FAQs")

    # TTS helper
    def speak_text(text, voice="nova"):
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(response.read())
                return tmp.name
        except Exception as e:
            st.warning("TTS failed.")
            return None

    # Session state for caching response and audio
    if "faq_answer" not in st.session_state:
        st.session_state.faq_answer = ""
        st.session_state.faq_audio = None

    selected_question = st.selectbox("Select a question:", questions)

    if selected_question:
        with st.spinner("Asking GPT..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert in water quality and environmental science. Be knowledgeable in Valley Water and its services in Santa Clara County"
                        },
                        {
                            "role": "user",
                            "content": f"Answer {selected_question} based on the location of Santa Clara County with a brief description, into bullet points and addresses if applicable, use data from the Valley Water official website, translate into {option} in the same format"
                        }
                    ],
                    temperature=0.7,
                    max_tokens=300
                )

                answer = response.choices[0].message.content
                st.session_state.faq_answer = answer
                st.session_state.faq_audio = speak_text(answer)

            except Exception as e:
                st.error(f"Something went wrong: {str(e)}")

    # Display answer and TTS button
    if st.session_state.faq_answer:
        st.markdown(f"**Answer:** {st.session_state.faq_answer}")

        if st.button("🔈 Play Explanation"):
            if st.session_state.faq_audio:
                st.audio(st.session_state.faq_audio)
            else:
                st.warning("Audio not available.")

    st.markdown(
        """
        🔗 **Learn more about water quality in Santa Clara County:**  
        [Santa Clara Valley Water - Water Quality](https://www.valleywater.org/your-water/water-quality)
        """
    )

# --- Water Quality Quiz ---
with tab3:
    st.title("💧Water Quality Quiz")
    MAX_QUESTIONS = 3

    def load_questions(filepath="questions.json"):
        with open(filepath, "r") as f:
            return json.load(f)

    def generate_explanation(question_text, correct_answer):
        prompt = (
            f"Question: {question_text}\n"
            f"Correct Answer: {correct_answer}\n"
            f"Please provide a short explanation of why this answer is correct, suitable for a general public quiz. "
            f"Respond in {option}."
        )
        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a water educator."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.5
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"❌ Could not generate explanation: {e}"

    def speak_text(text, voice="nova"):
        try:
            response = openai.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                tmp.write(response.read())
                return tmp.name
        except:
            return None

    if "all_questions" not in st.session_state:
        st.session_state.all_questions = load_questions()
        random.shuffle(st.session_state.all_questions)
        st.session_state.all_questions = st.session_state.all_questions[:MAX_QUESTIONS]
        st.session_state.answers = [None] * MAX_QUESTIONS
        st.session_state.explanations = [""] * MAX_QUESTIONS
        st.session_state.submitted_all = False
        st.session_state.audio_paths = [None] * MAX_QUESTIONS

    st.markdown("""
    🔗 **Learn more about water quality in Santa Clara County:**  
    [Santa Clara Valley Water - Water Quality](https://www.valleywater.org/your-water/water-quality)
    """)

    for idx, q in enumerate(st.session_state.all_questions):
        st.subheader(f"Q{idx + 1}: {q['question']}")
        st.session_state.answers[idx] = st.radio(
            f"Your answer for Q{idx + 1}:", q["options"],
            index=0 if not st.session_state.answers[idx] else q["options"].index(st.session_state.answers[idx]),
            key=f"q_{idx}"
        )
# --- After Submit ---
        if st.session_state.submitted_all:
            user_answer = st.session_state.answers[idx]
            correct_answer = q["answer"]
            if user_answer == correct_answer:
                st.success("✅ Correct!")
                st.session_state.explanations[idx] = generate_explanation(q["question"], correct_answer)
            else:
                st.error(f"❌ Incorrect. Your answer: {user_answer}")
                st.session_state.explanations[idx] = f"The correct answer is **{correct_answer}**.\n\n" + generate_explanation(q["question"], correct_answer)
            
            st.info(st.session_state.explanations[idx])

            if st.button(f"🔈 Play Explanation for Q{idx + 1}", key=f"tts_{idx}"):
                audio_path = speak_text(st.session_state.explanations[idx])
                if audio_path:
                    st.audio(audio_path)

    if st.button("✅ Submit All"):
        st.session_state.submitted_all = True
        st.rerun()

    if st.session_state.submitted_all:
        score = sum(
            1 for idx, q in enumerate(st.session_state.all_questions)
            if st.session_state.answers[idx] == q["answer"]
        )
        st.success(f"🎉 Your Score: {score} / {MAX_QUESTIONS}")

        if st.button("🔁 Restart Quiz"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

