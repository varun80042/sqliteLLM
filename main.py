import streamlit as st
import pandas as pd
import sqlite3
import json
from openai import OpenAI
from helper.llm_client import get_completion 

client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
model_path = r"D:/work/sem 7/Large Language Models/models/lmstudio-community/gemma-2-2b-it-GGUF/gemma-2-2b-it-Q4_K_M.gguf"

DB_PATH = "elections.db"

def generate_sql_query(question):
    """
    Generate a SQL query from a natural language question using the LLM.
    """
    prompt = f"""
    You are an assistant that translates natural language questions into SQL queries.
    The user has asked: '{question}'
    
    Ensure that the SQL query only reads data and does not contain any operations 
    like DROP, DELETE, or UPDATE that could alter the database.
    
    Return the SQL query in the following format:
    ```
    SELECT ...
    ```
    """
    sql_query = get_completion(prompt, client=client, model=model_path)
    return sql_query.strip()

def execute_sql_query(query):
    """
    Execute the SQL query on the SQLite database and return the results as a DataFrame.
    """
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn)

def interpret_results(results_df):
    """
    Generate a natural language explanation of SQL results using the LLM.
    """
    prompt = f"""
    The results of the SQL query are as follows: {results_df.to_dict()}
    
    Provide a concise, easy-to-understand summary of these results.
    """
    summary = get_completion(prompt, client=client, model=model_path)
    return summary

def main():
    st.title("Gemma 2 2B SQL Chatbot")

    question = st.text_input("Enter your question about the election data:")
    
    if st.button("Submit") and question:
        st.write("Generating SQL query from the question...")
        sql_query = generate_sql_query(question)
        st.write("Generated SQL query:")
        st.code(sql_query)

        if "DROP" in sql_query.upper() or "DELETE" in sql_query.upper() or "UPDATE" in sql_query.upper():
            st.error("The generated query includes a restricted operation. Please modify your question.")
        else:
            try:
                results_df = execute_sql_query(sql_query)
                st.write("SQL Query Results:")
                st.dataframe(results_df)

                result_summary = interpret_results(results_df)
                st.write("Summary of Results:")
                st.write(result_summary)

                if not results_df.empty:
                    st.write("Data Visualization:")
                    st.bar_chart(results_df)

            except Exception as e:
                st.error(f"Error executing query: {e}")

if __name__ == "__main__":
    main()
