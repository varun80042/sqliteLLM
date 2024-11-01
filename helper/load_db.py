import pandas as pd
import sqlite3

db_path = "database/elections.db"    
conn = sqlite3.connect(db_path)
    
try:
    elections_2019_df = pd.read_csv("data/final/final_details_of_assembly_segment_2019.csv")
    elections_2024_df = pd.read_csv("data/final/final_eci_data_2024.csv")
    maha_2019_df = pd.read_csv("data/final/final_maha_results_2019.csv")

    elections_2019_df.to_sql("elections_2019", conn, if_exists="replace", index=False)
    elections_2024_df.to_sql("elections_2024", conn, if_exists="replace", index=False)
    maha_2019_df.to_sql("maha_2019", conn, if_exists="replace", index=False)
        
    print("Success!")
    
except Exception as e:
    print(f"An error occurred: {e}")
    
finally:
        conn.close()


