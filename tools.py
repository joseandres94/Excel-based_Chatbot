import os
import sys
import ast
from io import StringIO
import pandas as pd
from pydantic import BaseModel
from langchain.agents import Tool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

TOOL_PROMPT = """You are an expert Pandas assistant.
Your task is to write Python code to query an ALREADY EXISTING Pandas DataFrame named 'df'.

The user will ask a question, and your job is to generate the Python code to extract the information that answers the
question.

YOU MUST NOT CREATE the df DataFrame. IT IS ALREADY AVAILABLE! I'll show it to you below:
{df_data}

Here is information about each column in the df DataFrame. IMPORTANT: Always review the meaning of each column before
generating the Python code:
{df_schema_info}

Whenever you need to see the first few rows of the DataFrame to view it completely, do so like this:
df[page].head().to_markdown()

IMPORTANT: Whenever you export a file, do so to the path:
{path} + '/' + file_name

Important rules:
- FIRST THING YOU HAVE TO DO: Check the data you have. If query cannot be answered with the DataFrame, generate code
that prints: "Request is not related to the information from the DataFrame."
- The code must be ONLY valid and executable Python code.
- Do not include any explanations, additional text, or markers like python`.
- The code must directly print the final result. If the final result is a DataFrame, print it in its entirety.
- Make sure the code is robust and handles potential data errors if relevant. If your code fails, ALWAYS check the error
and study new solutions and ways to complete the task.
- ABSOLUTELY CRITICAL! DO NOT IMPORT PANDAS (it is already available as
pd). DO NOT READ OR CREATE THE DATAFRAME (the df variable ALREADY EXISTS and is in the
environment). ONLY GENERATE PYTHON CODE THAT USES df.

Examples (the 'df' DataFrame already exists):
User question: "What is the average age of the patients?"
Python Code:
print(df['Overview']['Age'].mean())

User question: "How many patients scored more than 50 points on 'iNPH score before surgery'?"
Python Code:
print(df['Overview'][df['Overview']['iNPH score before surgery'] > 50].shape[0])

User question: "Give me a list of patients with a 'Yes' value in the 'CSF+' column"
Python Code:
print(df['Overview'][df['Overview']['CSF+'] == 'Yes'])

User question: "Give me the rows of patients with a 'Yes' value in the 'CSF+' column"
Python Code:
print(df['Overview'][df['Overview']['CSF+'] == 'Yes'].to_string())

If you need to export any data (e.g., a DataFrame to .csv)
**IMPORTANT: FORBIDDEN TO WRITE ANY OTHER INSTRUCTION AFTER 'df.to_csv()' OR 'df.to_excel()'
OTHERWISE IT WILL NOT WORK**
Python Code:
print(df.to_csv({path} + '/' + file_name))
**END OF CODE**

User question: "{user_query}"
Python Code:
"""


class ToolSchema(BaseModel):
    """
    Input schema of tool
    """

    user_query: str


def validate_expression(expression: str) -> ast.AST:
    """
    Verifies that 'expression' does not contain forbidden nodes (imports, calls to os.system, etc).
    Returns parsed AST in 'exec' mode.
    """

    PROHIBITED_MODULES = {"os", "subprocess", "shutil", "sys", "builtins", "socket"}
    PROHIBITED_FUNCTIONS = {"eval", "exec", "open", "compile", "__import__", "getattr", "input"}

    try:
        tree = ast.parse(expression, mode='exec')  # Parse expression
    except SyntaxError as e:
        raise ValueError(f'Expression not valid: {e}')

    # Check each node
    for node in ast.walk(tree):
        # Check imports
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError('Expression not valid. Import not allowed.')
        # Check modules
        if isinstance(node, ast.Name) and node.id in PROHIBITED_MODULES:
            raise ValueError('Expression not valid. Module not allowed.')
        # Check functions
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in PROHIBITED_FUNCTIONS:
                raise ValueError(f'Expression not valid. Hazardous expression detected: {node.func.id}')
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in PROHIBITED_FUNCTIONS or "__" in node.func.attr:
                    raise ValueError(f'Expression not valid. Hazardous expression detected: {node.func.attr}')
    return tree


# Tool function definition
def generate_and_execute_pandas_code(data: dict[str, pd.DataFrame],
                                     preview: str,
                                     columns_context: str,
                                     code_llm: ChatOpenAI) -> Tool:
    """
    Wrapper function for a code generation tool. Since it needs multiples inputs, it is necessary to wrap it in a
    function

    :param data: Data extracted from Excel file
    :param preview: Preview of first five columns for each page from Excel file
    :param columns_context: Description of Excel file, its pages and columns.
    :param code_llm: ChatOpenAi model dedicated to code generation
    :return: Tool for agent
    """

    def _tool(user_query: str) -> str:
        """
        Definition of a code generation tool. It generates and executes Python instructions to extract
        information from a dictionary of Pandas DataFrames.

        :param user_query: Input query from user
        :return: output from executed instruction
        """

        # Prompt instantiation
        code_prompt_templ = PromptTemplate.from_template(TOOL_PROMPT)
        prompt = code_prompt_templ.format(df_data=preview,
                                          df_schema_info=columns_context,
                                          user_query=user_query,
                                          path=os.getcwd())

        # Invoke model with prompt
        generated_code = code_llm.invoke(prompt).content

        # Adapt response
        generated_code = generated_code.replace("```python", "").replace("```", "").strip()

        try:
            # Validation of generation code
            tree = validate_expression(generated_code)
            compiled_expression = compile(tree, filename="<expr>", mode="exec")
        except ValueError as e:
            raise RuntimeError(f'Code not allowed: {e}')

        # Execute Pandas function to get information
        try:
            # Redirect stdout to catch the output of print()
            old_stdout = sys.stdout
            redirected_output = StringIO()
            sys.stdout = redirected_output

            # List of safe built-ins
            safe_builtins = {
                "print": print,
                "len": len,
                "range": range,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "set": set,
                "min": min,
                "max": max,
                "sum": sum,
                "enumerate": enumerate,
                "zip": zip,
                # Include here safe functions needed
            }

            # Set controlled namespaces
            safe_globals = {
                '__builtins__': safe_builtins,
                'df': data,
                'pd': pd
            }

            safe_locals = {}

            # Evaluate pandas instruction
            exec(compiled_expression, safe_globals, safe_locals)

            output = redirected_output.getvalue()

            # Restore stdout
            sys.stdout = old_stdout

            if not output.strip():  # If output is empty
                return "Code was executed, but it did not produced a visible output."
            return output.strip()

        except Exception as e:
            sys.stdout = old_stdout  # Restore stdout
            return f"Error executing Pandas code: {e}\nGenerated code:\n{generated_code}"

    return Tool.from_function(func=_tool,
                              name='generate and execute pandas code',
                              description='Useful to generate pandas code when you need to answer question about a '
                                          'Pandas DataFrame.',
                              args_schema=ToolSchema)
