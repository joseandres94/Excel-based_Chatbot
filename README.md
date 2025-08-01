# Excel‑Based Q&A Agent
This repository provides an end‑to‑end Python pipeline that leverages OpenAI’s LLMs and Pandas to answer natural‑language queries against an Excel workbook. Users can interactively ask questions—ranging from simple statistics to multi‑sheet merges and exports—and the agent will generate, validate, and safely execute the necessary Pandas code under the hood.

The goal of this project is to help people work with large datasets stored in Excel or CSV files. While manipulating large amounts of data with Pandas is often much easier than with Excel, many users have never worked with Python or Pandas. For this reason, this project aims to bring the power of Pandas without the necessity to code.

This project was originally developed using an Excel file containing experimental results from Neuroscience research. Therefore, the sample questions below are related to this topic. However, **this project can be used with any kind of structured data in Excel or CSV format**.

## Objectives
1. **Natural‑Language Q&A**: Allow users to pose natural-language questions about tabular data stored across multiple sheets of an Excel file. 
2. **Dynamic Code Generation**: Use a dedicated LLM to write Pandas code snippets that extract, transform, and export data as requested. 
3. **Safe Execution Sandbox**: Validate and execute sandboxed code to prevent imports, system calls, or other non‑Pandas operations. 
4. **Export & Reporting**: Support exporting subsets or merged results to CSV/Excel files on demand.

## Repository Structure
  ```bash
  root/
  ├── requirements.txt                  # required dependencies
  ├── .env                              # environment variables file
  ├── main.py                           # CLI entrypoint: loads data, creates & runs the agent loop
  ├── data/                             # sample Excel and context files (gitignored if private)
  │   ├── excel_file.xlsx               # source of data to be asked about
  │   └── columns_context.txt           # information about sheets and columns from the Excel file
  └── src/
      ├── config.py                     # Global paths & model‑name configuration via .env
      ├── tools.py                      # Tool: generate, validate, and execute Pandas code safely
      └── prompts.py                    # Prompt templates for system, human, and tool orchestration 
  ```

## Main Features
* **Modular Agent Design**: Separates prompt construction, tool definition, and agent orchestration for clarity and maintainability. 
* **Secure Code Validation**: Parses AI-generated Pandas code using Python’s ast module to inspect the abstract syntax tree.\
  The validation process blocks:
  - Imports (```import```, ```__import__```)
  - Attribute access to unsafe modules or functions (```os```, ```sys```, etc.)
  - Function calls like ```eval()```, ```exec()```, and ```getattr()```
  - Any usage of double underscores (```__something__```) to prevent access to hidden methods.

* **Sandboxed Code Execution**: Executes the validated code in a controlled environment where only:
  - The preloaded Pandas DataFrames (```df```)
  - The Pandas library itself (```pd```)
  - Safe built-in functions (e.g., ```len()```, ```sum()```, ```round()```) are available.

* **Multi-Sheet Support**: Automatically loads all sheets from an Excel workbook into a dictionary of DataFrames, allowing users to interact with each sheet by name.

* **Data Export**: Enables saving query results to .csv or .xlsx through agent‑generated Pandas code (```df.to_csv()``` or ```df.to_excel()```), with output file paths automatically handled and displayed.

* **Context-Aware Prompting**: Injects column descriptions from a columns_context.txt file to provide the model with additional semantic context about the Excel data.

* **Interactive REPL (Read-Eval-Print Loop)**: Runs in an interactive command-line session where the user can ask multiple questions without restarting the script.

* **Error Feedback & Recovery**: Captures and displays any runtime errors from Pandas execution, allowing the user to refine their query or correct invalid assumptions.


## Prerequisites
- Python 3.9+
- An OpenAI API key with access to GPT models
- A local copy of your Excel file (e.g. `excel_file.xlsx`)
- A plain-text context file (`columns_context.txt`) documenting each sheet’s columns

## Installation
1. Clone the repo
   ```bash
   git clone https://github.com/joseandres94/Excel-based_Chatbot.git
   cd Excel-based_Chatbot
   ```

2. Create & activate a virtual environment
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Prepare your data
* Copy your Excel workbook into data/ and name it as specified in src/config.py (default: `excel_file.xlsx`).
* Edit or replace data/columns_context.txt with a description of each sheet and column.

5. Configure environment variables
- Create a .env file in the project root with:
  ```ini
  OPENAI_API_KEY=sk-...
  MODEL_CODE_GENERATOR=gpt-...  # OpenAI model chosen for code generation. (default: gpt-4.1-mini)
  MODEL_CHAT_LLM=gpt-...  # OpenAI model chosen for chat. (default: gpt-4.1-mini)
  ```
  
## Usage
Run the agent and start asking questions:

  ```bash
  python ./main.py
  ```

You’ll see a prompt:
  ```makefile
  Query:
  ```

Type a question, for example:
  ```
  Query: What is the average age of the patients?
  ```

The agent will:
1. Generate a pandas snippet via the code-generation model.
2. Execute it against your loaded DataFrames.
3. Return the result in natural language.
4. To exit, just press Enter on an empty line.

## Configuration
All key settings live in src/config.py:

`EXCEL_FILE_PATH` & `CONTEXT_FILE_PATH`: Paths to your data files.

`MODEL_CODE_GENERATOR` & `MODEL_CHAT_LLM`: Model names (read from environment) for code generation vs. conversational chat.

You can tweak temperature, retry logic, token limits, and agent parameters directly in src/main.py when creating the models and initializing the agent. However, they are not accessible as hyperparameters, since changing them will change the behaviour of the model and likely reduce its performance.

## Example Session
  ```sql
  $ python src/main.py
  Query: How many patients scored more than 50 on the iNPH score before surgery?
    37 patients scored more than 50 on the iNPH score before surgery.

  Query: Show me the first 10 rows of the Overview sheet
    (prints a 10-row markdown table)

  Query: List patient IDs with a Yes value in the CSF+ column
    The patient IDs with a "Yes" value in the CSF+ column are [2, 5, 9, 11, 14, 20, 23, 24, 33].
  ```
These are simple examples, but the agent can run any kind of Pandas code, including merging data across sheets and exporting the results to a CSV or Excel file.

## Contributing
Contributions welcome! Feel free to open issues for feature requests, bug reports, or submit pull requests.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
