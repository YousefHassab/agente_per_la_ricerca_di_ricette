import streamlit as st
import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="AI Kitchen Agent", layout="wide")

# Inizializzazione stato
if "messages" not in st.session_state:
    st.session_state.messages = []
if "data_extracted" not in st.session_state:
    st.session_state.data_extracted = {"ingredienti": [], "vincoli": []}

# PROMPT OTTIMIZZATO (Capitolo 6)
SYSTEM_PROMPT = """
Sei un assistente culinario intelligente. 
REGOLE:
1. Sii conversazionale. Non proporre ricette finché non hai: quantità, scadenze e vincoli di salute.
2. Se mancano dati, fai domande gentili.
3. Quando proponi ricette, fanne sempre 3 complete.
4. FORMATO OBBLIGATORIO: Scrivi la tua risposta umana, poi scrivi ESATTAMENTE il delimitatore '---JSON_DATA---' e subito dopo il JSON con lo stato attuale.
NON scrivere la parola 'JSON:' o altri commenti dopo il delimitatore.

Esempio finale:
Certamente! Ecco le domande...
---JSON_DATA---
{"ingredienti": [{"nome": "pollo", "qta": "300g", "scadenza": "domani"}], "vincoli": ["niente sale"]}
"""

st.title("👨‍🍳 Assistente Smart Kitchen")

# SIDEBAR (Requisito fondamentale della verifica)
with st.sidebar:
    st.header("📊 Informazioni Raccolte")
    data = st.session_state.data_extracted
    
    st.subheader("🛒 Ingredienti")
    if not data["ingredienti"]: st.write("Nessun ingrediente rilevato.")
    for i in data["ingredienti"]:
        st.info(f"**{i.get('nome','')}**\n- Q.tà: {i.get('qta','?')}\n- Scad: {i.get('scadenza','-')}")
    
    st.subheader("🩺 Vincoli Salute/Gusti")
    if not data["vincoli"]: st.write("Nessun vincolo inserito.")
    for v in data["vincoli"]:
        st.warning(v)

    if st.button("Nuova Conversazione"):
        st.session_state.messages = []
        st.session_state.data_extracted = {"ingredienti": [], "vincoli": []}
        st.rerun()

# Logica Chat
for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

if prompt := st.chat_input("Cosa hai in cucina?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"): st.markdown(prompt)

    with st.chat_message("assistant"):
        history = [{"role": "system", "content": SYSTEM_PROMPT}] + \
                  [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=history,
            temperature=0.2
        )
        
        full_res = response.choices[0].message.content
        
        if "---JSON_DATA---" in full_res:
            parts = full_res.split("---JSON_DATA---")
            text_ans = parts[0].strip()
            try:
                # Carica i dati nella sidebar
                st.session_state.data_extracted = json.loads(parts[1].strip())
            except: pass
        else:
            text_ans = full_res
            
        st.markdown(text_ans)
        st.session_state.messages.append({"role": "assistant", "content": text_ans})
        st.rerun()
