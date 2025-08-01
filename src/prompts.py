from langchain_core.prompts import (SystemMessagePromptTemplate,
                                    MessagesPlaceholder,
                                    HumanMessagePromptTemplate,
                                    ChatPromptTemplate)

SYSTEM_PROMPT = """You are a cordial assistant expert in '{topic}'.
Conversation history:
{chat_history}

If you deem it necessary to use them, you have access to the following tools:
{tools}

If question is not related to '{topic}', say: "I am not able to response your query."

Follow the format below when interacting with user questions:
Question: Question the user wants you to answer.
Thought: You always have to think about what you're doing.
Action: The action you take will be one of the tools ({tool_names}).
Action Input: The input for the action.
Observation: The analyze the result of the action.
... (this Thought/Action/Action Input/Observation can be repeated N times).
Thought: I know the final answer now.
Final Answer: The answer to the original question.

Start!
Question: {input}
Thought: {agent_scratchpad}"""


# Prompt definition
def build_prompt(tools: list, topic: str) -> ChatPromptTemplate:
    """
    Definition of prompt template for agent. It includes the chat history and the available tools.

    :param tools: List of tools that the model can use
    :return: Resulting prompt template
    """

    system_message = SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT)
    history_context = MessagesPlaceholder(variable_name='chat_history')
    human_message = HumanMessagePromptTemplate.from_template('Human: {input}')

    return ChatPromptTemplate.from_messages([system_message, history_context, human_message]).partial(
        topic=topic,
        tools=tools,
        tool_names=[t.name for t in tools])
