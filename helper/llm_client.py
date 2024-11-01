import json
from openai import OpenAI

# Point to the local server
client1 = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")  # html to json
model = r"/Users/karthiknamboori/.cache/lm-studio/models/lmstudio-community/gemma-2-2b-it-GGUF"

# model = "MaziyarPanahi/Mistral-7B-Instruct-v0.3-GGUF/Mistral-7B-Instruct-v0.3.Q4_K_M.gguf:2"


def get_completion(prompt, client=client1, model=model):
    """
    given the prompt, obtain the response from LLM hosted by LM Studio as a server
    :param prompt: prompt to be sent to LLM server
    :return: response from the LLM
    """
    prompt = [
        {"role": "user", "content": prompt}
    ]
    completion = client.chat.completions.create(
        model=model,
        messages=prompt,
        temperature=0.0,
        stream=True,
    )

    new_message = {"role": "assistant", "content": ""}

    for chunk in completion:
        if chunk.choices[0].delta.content:
            # print(chunk.choices[0].delta.content, end="", flush=True)
            val = chunk.choices[0].delta.content
            new_message["content"] += val

    # print(type()
    val = new_message["content"]  # .split("<end_of_turn>")[0]

    return val


if __name__ == '__main__':
    prompt = """
    You are a political leader and your party is trying to win the general elections in India. 
    You are given an LLM that can provide you the analytics using the past historical data given to it.
    In particular the LLM has been provided data on which party won each constituency out of 545 and which assembly segment within the main constituency is more favorable.
    It also has details of votes polled by every candidate.
    Tell me 10 questions that you want to ask the LLM.
    """
    results = get_completion(prompt)
    print(results)

