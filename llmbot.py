from langchain_core.messages import HumanMessage, SystemMessage
from langchain_gigachat.chat_models import GigaChat
import os
from dotenv import load_dotenv


async def run_gigachat(gigachat_key, system_message_content, dialogue_messages, max_history_length=10):
    llm = GigaChat(
        credentials=gigachat_key,
        scope="GIGACHAT_API_PERS",
        model="GigaChat",
        verify_ssl_certs=False,
        streaming=False,
    )
    
    system_messages = [
        SystemMessage(
            content=system_message_content
        )
    ]
    
    if len(dialogue_messages) > max_history_length:
        dialogue_messages = dialogue_messages[-max_history_length:]
    
    messages = system_messages + dialogue_messages

    res = llm.invoke(messages)
    response_text = res.content

    #dialogue_messages.append(res)

    return response_text


#system_message_content = "Ты - "
#initial_messages = []

#user_input = "Привет, как дела?"
#initial_messages.append(HumanMessage(content=user_input))

# Вызов функции
#response_text, updated_history = run_gigachat(system_message_content, initial_messages, 20)

# Вывод результата

#print(updated_history)
