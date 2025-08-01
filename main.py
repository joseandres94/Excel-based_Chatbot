#!/usr/bin/env python3

# Import dependencies
from src.config import EXCEL_FILE_PATH, CONTEXT_FILE_PATH, MODEL_CODE_GENERATOR, MODEL_CHAT_LLM
from src.tools import generate_and_execute_pandas_code
from src.prompts import build_prompt

# Import libraries
import os
import pandas as pd
from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain.memory import ConversationBufferMemory
from langchain.agents import (initialize_agent,
                              AgentType,
                              AgentExecutor)

# Load API Key
if not os.environ.get('OPENAI_API_KEY'):
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')


# Agent creation
def create_agent(data: dict[str, pd.DataFrame], preview: str, columns_context: str, topic: str) -> AgentExecutor:
    """
    Function for building a ChatOpenAI-based agent with tools, memory and prompt template.

    :param data: Data extracted from Excel file
    :param preview: Preview of first five columns for each page from Excel file
    :param columns_context: Description of Excel file, its pages and columns.
    :param topic: Topic we want the agent to be expert.
    :return: Instantiation of agent executor
    """

    # -- Load models -- #
    # Define model for code generation (tool)
    code_generator_llm = ChatOpenAI(model=MODEL_CODE_GENERATOR,
                                    temperature=0,
                                    max_retries=2)

    # Define chat model
    chat_llm = ChatOpenAI(model=MODEL_CHAT_LLM,
                          temperature=0.1,
                          max_tokens=None,
                          timeout=None,
                          max_retries=2)

    # -- Load tools -- #
    tools = load_tools([], llm=chat_llm)  # Define empty tool list
    tools.append(generate_and_execute_pandas_code(data=data,
                                                  preview=preview,
                                                  columns_context=columns_context,
                                                  code_llm=code_generator_llm))

    # -- Memory definition -- #
    memory = ConversationBufferMemory(memory_key='chat_history',
                                      return_messages=True)

    # -- Prompt definition -- #
    prompt_template = build_prompt(tools=tools, topic=topic)

    # -- Agent definition -- #
    return initialize_agent(llm=chat_llm,
                            tools=tools,
                            prompt=prompt_template,
                            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                            memory=memory,
                            verbose=True,
                            handle_parsing_errors=False,
                            max_iterations=5)


# Main function
def main():
    """
    Main function with the logic of the project
    """

    # -- Load data -- #
    data = pd.read_excel(EXCEL_FILE_PATH, sheet_name=None, header=0)
    with open(CONTEXT_FILE_PATH, encoding='utf-8') as f:
        columns_context = f.read()

    # -- Preview generation (first five columns from data) -- #
    preview_snippets = []
    for sheet_name, df in data.items():
        snippet = (
            f"### Sheet: {sheet_name}\n"
            f"{df.head().to_markdown()}"
        )
        preview_snippets.append(snippet)

    all_sheets_preview = "\n\n".join(preview_snippets)


    # -- Create agent -- #
    agent = create_agent(data=data,
                         preview = all_sheets_preview,
                         columns_context=columns_context,
                         topic='Neuroscience')

    # -- Main loop -- #
    while 1:
        try:
            user_query = input('\nQuery: ')
            if len(user_query) > 0:
                response = agent.invoke({'input': user_query})  # Invoke model and print response
                print(response['output'])

            else:
                print('Process finished.')
                break
        except Exception as e:
            print(f'\nError during execution: {e}')


if __name__ == '__main__':
    main()
