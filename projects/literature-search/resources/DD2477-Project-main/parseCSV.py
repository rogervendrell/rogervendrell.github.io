import csv
import json
import re

fileName = "Data/export_KTH_CS_Only.csv"
jsonName = "Data/test_KTH_only.json"
genreFile = "genres/docs_with_genres.csv"
#fileName = "Data/export_2000_Test.csv"
#jsonName = "Data/test.json"

def listAuthors(authors):
    authors_list = authors.split(";")
    cleaned_authors = []
    for a in authors_list:
        # Keep only the part before the first "[" or "("
        a = re.split(r"[\[\(]", a)[0]
        cleaned = a.strip().rstrip(",")
        cleaned_authors.append(cleaned)
    return cleaned_authors

def listKeywords(keywords):
    keywords_list = keywords.split(";")
    cleaned_keywords=[]
    for k in keywords_list:
        cleaned = k.strip()
        cleaned_keywords.append(cleaned)
    return keywords_list

import re

def remove_swedish(texts):
    swedish_common_words = {'och', 'det', 'att', 'som', 'på', 'är', 'för', 'med', 'inte', 'den'}
    result = ""
    for text in texts:
        text = text.lower()
        words = set(re.findall(r'\b\w+\b', text))

        swedish_matches = len(words & swedish_common_words)
    
        if swedish_matches > 0:
            continue

        return text
    
    return result
pidToGenre = {}
with open(genreFile, encoding="utf8") as genreCSVFile:
    reader = csv.DictReader(genreCSVFile)
    for row in reader:
        pid = row["PID"]
        genre = row["Genre"]
        pidToGenre[pid] = genre



with open(fileName, encoding="utf8") as csvFile:
    reader = csv.DictReader(csvFile)
    writer = open(jsonName, mode="w", encoding="utf8")
    writer.write("[\n")
    empty = 0
    swed = 0
    noKeys = 0
    for row in reader:
        content = row["Abstract"].replace("<p>", "\n").replace("</p>", "\n\n")
        
        splitAbs = content.split(";")
        if len(splitAbs) > 1:
            swed +=1
            content = remove_swedish(splitAbs)

        if row["Keywords"] == "":
            noKeys += 1
        if content == "": 
            empty += 1
            continue


        #if is_swedish(content):
        #    swed +=1
        #    continue

        authors = listAuthors(row["Name"])
        keywords = listKeywords(row["Keywords"])

        writer.write(f'{json.dumps({'PID': row["\ufeffPID"],'Title':row['Title'], 
                                    'Keywords':keywords, 'Content':content, 'Authors':authors,
                                    'Genre': pidToGenre[row["\ufeffPID"]]})},\n')
    writer.seek(writer.tell()-3, 0) # sets position to overwrite final ','
    writer.write("\n]\n")

print(f"There were {empty} docs without an abstract")
print(f"There were {swed} docs contained Swedish")
print(f"There were {noKeys} docs without keywords")