import streamlit as st
import pandas as pd
import sqlite3
import json
from openai import OpenAI
from helper.llm_client import get_completion 

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model_path = r"D:/work/sem 7/Large Language Models/models/lmstudio-community/gemma-2-2b-it-GGUF/gemma-2-2b-it-Q4_K_M.gguf"

DB_PATH = "database/elections.db"

SAMPLE_QUESTIONS = [
    "What is the total number of votes secured by each party in the 2019 elections?",
    "Show me the top 10 candidates with highest vote share in 2024 elections",
    "How many female candidates contested in Maharashtra assembly elections?",
    "Which constituency had the highest NOTA votes in 2019?",
    "Compare the vote share of major parties between 2019 and 2024 elections",
    "List all candidates who won with more than 50% vote share in 2024",
    "What is the average age of winning candidates in Maharashtra assembly elections?",
    "Show the party-wise distribution of SC/ST candidates in Maharashtra",
    "Which constituencies had the closest margins in 2024 elections?",
    "How many candidates contested from multiple parties between 2019 and 2024?",
    "What is the state-wise distribution of female candidates?",
    "Show constituencies where NOTA votes exceeded the margin of victory",
    "List candidates who improved their vote share from 2019 to 2024",
    "What is the age distribution of candidates by party in Maharashtra?",
    "Which party had the highest success rate in converting votes to seats?",
    "Compare postal votes vs EVM votes across constituencies in 2024",
    "Show the top 5 states with highest voter turnout",
    "List constituencies where independent candidates secured more than 20% votes",
    "What is the average margin of victory by state in 2024?",
    "Show the party-wise distribution of young candidates (under 40)",
    "Which constituencies had more than 5 candidates securing over 10% votes?",
    "Compare performance of national vs regional parties in 2024",
    "List candidates who won despite being the youngest in their constituency",
    "Show constituencies where winner changed between 2019 and 2024",
    "What is the correlation between candidate age and vote share?"
]

def get_detailed_schema():
    """
    Fetches detailed schema information including CREATE TABLE statements and sample data
    from the SQLite database.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Get list of all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema_info = {}
        
        for (table_name,) in tables:
            table_info = {}
            
            # Get CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
            create_table_stmt = cursor.fetchone()[0]
            table_info['create_table'] = create_table_stmt
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            table_info['columns'] = {
                col[1]: {
                    'type': col[2],
                    'nullable': not col[3],
                    'primary_key': bool(col[5])
                } for col in columns
            }
            
            # Get sample data (first 3 rows)
            # try:
            #     cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
            #     sample_data = cursor.fetchall()
            #     column_names = [description[0] for description in cursor.description]
            #     table_info['sample_data'] = [dict(zip(column_names, row)) for row in sample_data]
            # except sqlite3.Error as e:
            #     table_info['sample_data'] = f"Error fetching sample data: {str(e)}"
            
            schema_info[table_name] = table_info
            
        return schema_info

def generate_sql_query(question):
    """
    Generate a SQL query from a natural language question using the LLM with enhanced context.
    """
    schema_info = get_detailed_schema()
    
    # Format the schema information in a more readable way for the LLM
    schema_context = "DATABASE SCHEMA:\n\n"
    for table_name, info in schema_info.items():
        schema_context += f"Table: {table_name}\n"
        schema_context += f"Creation SQL:\n{info['create_table']}\n\n"
        schema_context += "Columns:\n"
        for col_name, col_info in info['columns'].items():
            schema_context += f"- {col_name} ({col_info['type']})"
            if col_info['primary_key']:
                schema_context += " PRIMARY KEY"
            if not col_info['nullable']:
                schema_context += " NOT NULL"
            schema_context += "\n"
        
        # schema_context += "\nSample Data:\n"
        # if isinstance(info['sample_data'], list):
        #     for row in info['sample_data']:
        #         schema_context += f"{row}\n"
        schema_context += "\n---\n\n"

    prompt = f"""
    You are an expert SQL query generator that translates natural language questions into SQL queries.
    The user has asked: '{question}'
    
    Here is the detailed schema of the database, including table structures and sample data:
    
    {schema_context}
    
    Important guidelines:
    1. Use only the tables and columns shown in the schema
    2. Ensure the query is read-only (no DROP, DELETE, UPDATE, or INSERT operations)
    3. Use appropriate JOINs if multiple tables are needed
    4. Include WHERE clauses to filter data appropriately
    5. Use column names exactly as they appear in the schema
    
    Return only the SQL query in the following format:
    ```sql
    SELECT ...
    ```
    """
    
    sql_query = get_completion(prompt, client=client, model=model_path)
    
    # Extract the SQL query from between ```sql and ``` if present
    import re
    sql_match = re.search(r"```sql\n(.*?)\n```", sql_query, re.DOTALL)
    if sql_match:
        sql_query = sql_match.group(1).strip()
    else:
        sql_query = sql_query.strip()
    
    return sql_query

def execute_sql_query(query):
    """
    Execute the SQL query on the SQLite database and return the results as a DataFrame.
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

def interpret_results(results_df, original_question, sql_query):
    """
    Generate a natural language explanation of SQL results using the LLM.
    """
    prompt = f"""
    Original question: {original_question}
    SQL query used: {sql_query}
    
    The query returned the following results:
    {results_df.to_dict()}
    
    Please provide:
    1. A clear, concise summary of the results in natural language
    2. Any notable patterns or insights from the data
    3. Answer the original question directly
    
    Keep the response conversational and easy to understand for non-technical users.
    """
    summary = get_completion(prompt, client=client, model=model_path)
    return summary

def main():
    st.title("Election Data Analysis Chatbot")
    
    # Add custom CSS for question blocks
    st.markdown("""
        <style>
        .question-block {
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 0.5rem;
            background-color: white;
            color: black;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .question-block:hover {
            background-color: #f8f9fa;
            border-color: #c0c0c0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state for selected question if not exists
    if 'selected_question' not in st.session_state:
        st.session_state.selected_question = ""

    # Sample Questions Section
    st.markdown("### Browse Sample Questions")
    
    # Create a slider to navigate through questions
    selected_index = st.slider(
        "Navigate through questions",
        0, len(SAMPLE_QUESTIONS) - 1,
        key="question_slider"
    )
    
    # Display current question block
    current_question = SAMPLE_QUESTIONS[selected_index]
    st.markdown(f"""
        <div class='question-block'>
            {current_question}
        </div>
    """, unsafe_allow_html=True)
    
    # Button to use selected question
    if st.button("Use this question"):
        st.session_state.selected_question = current_question

    # Question input section
    st.markdown("### Ask Your Question")
    question = st.text_input(
        "Enter your question about the election data:",
        value=st.session_state.selected_question
    )

    # Add schema viewer in an expander
    with st.expander("Show Database Schema"):
        schema_info = get_detailed_schema()
        st.json(schema_info)

    # Process the question
    if st.button("Submit") and question:
        with st.spinner("Generating SQL query..."):
            sql_query = generate_sql_query(question)
            st.write("Generated SQL query:")
            st.code(sql_query, language="sql")

        if any(op in sql_query.upper() for op in ["DROP", "DELETE", "UPDATE", "INSERT"]):
            st.error("The generated query includes a restricted operation. Please modify your question.")
        else:
            try:
                with st.spinner("Executing query..."):
                    results_df = execute_sql_query(sql_query)
                    st.write("SQL Query Results:")
                    st.dataframe(results_df)

                with st.spinner("Interpreting results..."):
                    result_summary = interpret_results(results_df, question, sql_query)
                    st.write("Summary of Results:")
                    st.write(result_summary)

                if not results_df.empty:
                    st.write("Data Visualization:")
                    st.bar_chart(results_df)

            except Exception as e:
                st.error(f"Error executing query: {str(e)}")

    # Add footer with instructions
    st.markdown("---")
    st.markdown("""
        ### How to use:
        1. Browse through sample questions using the slider
        2. Click 'Use this question' or type your own question
        3. Submit to get SQL query, results, and analysis
    """)

if __name__ == "__main__":
    main()