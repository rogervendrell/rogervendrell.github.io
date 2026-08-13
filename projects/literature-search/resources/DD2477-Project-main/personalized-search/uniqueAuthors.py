import json
import uuid
import csv
import pandas as pd
# TO DO -> convert all keywords to lowercase
input_file = "../Data/test_KTH_only.json"
output_file = "data/authors_with_pids.csv"
output_keywords_file="data/keywords_with_pids.csv"
id_to_author_file = "../coauthorsgraph/graph/id-to-author.csv"

with open(input_file, encoding="utf8") as f:
    data = json.load(f)

# Load id-to-author mapping
author_df = pd.read_csv(id_to_author_file, sep=';')
author_map = {name.strip().lower(): str(author_id) for author_id, name in zip(author_df["id"], author_df["name"])}

def get_author_id(author_name):
    if not isinstance(author_name, str):
        return str(uuid.uuid4())
    normalized_name = author_name.strip().lower()
    return author_map.get(normalized_name, str(uuid.uuid4()))


author_dict = {}
keywords_dict = {}

for entry in data:
    pid = entry["PID"]
    keywords = entry["Keywords"]
    for author in entry["Authors"]:
        if author not in author_dict:
            tempAuthorKeywords = []
            for keyword in keywords:
                if keyword not in tempAuthorKeywords and keyword:
                    tempAuthorKeywords.append(keyword.strip().lower())
        
            author_dict[author] = {
                "ID": get_author_id(author.strip().lower()),
                "PIDs": [pid],
                "Keywords": tempAuthorKeywords
            }
            
        else:
            author_dict[author]["PIDs"].append(pid)
            authorKeywords = author_dict[author]["Keywords"]
            for keyword in keywords:
                if keyword not in authorKeywords and keyword:
                    authorKeywords.append(keyword.strip().lower())
    for keyword in keywords:
        if keyword not in keywords_dict:
            keywords_dict[keyword.strip().lower()] = {
                "Keyword": keyword.strip().lower(),
                "PIDs": [pid]
            }
        else:
            keywords_dict[keyword]["PIDs"].append(pid)

# Write to CSV
with open(output_file, mode="w", encoding="utf8", newline="") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["Author", "ID", "PIDs", "Keywords"])
    for author, details in author_dict.items():
        pid_string = ",".join(details["PIDs"])
        keywords_string = ",".join(details["Keywords"])
        writer.writerow([author, details["ID"], pid_string, keywords_string])

with open(output_keywords_file, mode="w", encoding="utf8", newline="") as csvfile:
    writer = csv.writer(csvfile, delimiter=";")
    writer.writerow(["Keyword", "PID"])
    for keyword, details in keywords_dict.items():
        pid_string = ",".join(details["PIDs"])
        writer.writerow([details["Keyword"], pid_string])
    writer.writerow([details["Keyword"], pid_string])

print(f"CSV file saved to {output_file} with {len(author_dict)} authors.")
