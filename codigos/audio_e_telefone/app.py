import time
import requests
import os

import streamlit as st

from functions import make_blandai_call, get_call_info


st.header("Outbound Call") 

call_context = st.text_area(
    "Call Context", 
    "Você é a Rê da Repense.\n"
    "Você está ligando para lembrar o paciente sobre a consulta amanhã às 10:00.\n" 
    "Por favor, peça confirmação e lembre-os de trazer o cartão do convênio."
)

cols = st.columns(2, vertical_alignment='center')
x = "+XXXXXXXXX"

number = cols[0].text_input(
    "Phone Number", 
    value=x, 
    label_visibility="collapsed",
)

if cols[1].button("Call"):
    if number == x:
        number = os.getenv("PHONE_NUMBER_TO_CALL")
        
    parameters = {}
    response = make_blandai_call(call_context, number, parameters)

    if response.get("status") == "success":
        st.success("Call made successfully!")
    else:
        if "errors" in response:
            st.error("\n".join(response.get("errors", [])))
            st.stop()
        else:
            st.error(f"{response.get('message')}")
            st.stop()

    st.divider()
    status = st.empty()

    with st.spinner("Waiting the call to finish..."):
        
        while True:
            call_info = get_call_info(response['call_id'])
            status.write(f"Status: {call_info['status']}")
            
            if call_info['status'] == "completed":
                status.write("Status: completed")
                break

            time.sleep(5)

    try:
        time.sleep(10)

        record = requests.get(call_info["recording_url"])
        st.audio(record.content, format="audio/mp3")

        with st.popover("Transcription"):
            for message in call_info["transcripts"]:
                with st.chat_message(message['user']):
                    st.write(message['text'])
                    
    except Exception as e:
        st.error(f"Error: {e}")
        st.stop()
