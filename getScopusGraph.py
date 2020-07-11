# This script gets the relations of co-authorship and outputs a GDF file for Gephi to understand
import csv
import io
r = csv.reader(open('scopusExportedFile.csv', 'r', encoding='utf-8',newline=''), delimiter=',')
lines = list(r)
#Authors,Author(s) ID,Title,Year,Source title,Cited by,DOI,Link,Author Keywords,References,EID
#Authors = lines[i][0]
#AuthorsID = lines[i][1]
listOfAuthors = {}
papersPerAuthor = {}
totalTimesCited = {}
listOfLinks = {}
for i in range(len(lines) - 1):
    if i == 0:
        continue
    # Get the paper's Author's name and ID
    authorsNames = lines[i][0].split(";")
    authorsIDs  = lines[i][1][:-1].split(";")
    # Get the number of times the paper's been cited
    cited = int(lines[i][5]) if lines[i][5] else 0
    # Link authors and IDs
    # authorsNames[n] = nth AuthorName
    # authorsIDs[n] = nth AuthorID
    for j in range(len(authorsNames) - 1):
        #print("i: " + str(i) + " j: " + str(j))
        authorsNames[j] = authorsNames[j].strip()
        authorsIDs[j] = authorsIDs[j].strip()
    # Iterate authors of paper
    for j in range(len(authorsIDs)  - 1):
        # If author is not in list, add it, set its number of papers to 1 and the total number of times cited to the times this paper has been cited
        if authorsIDs[j] not in listOfAuthors:
            listOfAuthors[authorsIDs[j]] = authorsNames[j]
            papersPerAuthor[authorsIDs[j]] = 1
            totalTimesCited[authorsIDs[j]] = cited
        else:
            # If the author is in the list, add 1 to the total number of its papers and
            # add to the total number of times it's been cited the number of TotalTimesCited his paper has been cited
            papersPerAuthor[authorsIDs[j]] = papersPerAuthor[authorsIDs[j]] + 1
            totalTimesCited[authorsIDs[j]] = totalTimesCited[authorsIDs[j]] + cited
    # Iterate the list of authors of the paper and get the relations between them
    for authorA in range(len(authorsIDs)  - 2):
        for authorB in range(authorA + 1, len(authorsIDs)  - 1):
            # If they've co-authored before and it's stored as A <-> B, add 1 to the total number of links between them
            if (authorsIDs[authorA], authorsIDs[authorB]) in listOfLinks:
                listOfLinks[(authorsIDs[authorA], authorsIDs[authorB])] = listOfLinks[(authorsIDs[authorA], authorsIDs[authorB])] + 1
            # If they've co-authored before and it's stored as B <-> A, add 1 to the total number of links between them
            elif (authorsIDs[authorB], authorsIDs[authorA]) in listOfLinks:
                listOfLinks[(authorsIDs[authorB], authorsIDs[authorA])] = listOfLinks[(authorsIDs[authorB], authorsIDs[authorA])] + 1
            # If they have not co-authored, set to 1 to the total number of links between them
            else:
                listOfLinks[(authorsIDs[authorA], authorsIDs[authorB])] = 1
f_out = open("outputFile.gdf", 'w', encoding="utf-8")
#   NODES WRITING
f_out.write('nodedef>name VARCHAR,label VARCHAR, Npapers INT, TotalTimesCited INT\n')
for id, name in listOfAuthors.items():
    write = id + ',' + name + ',' + str(papersPerAuthor[id]) + ',' + str(totalTimesCited[id]) + '\n'
    f_out.write(write)
#   EDGES WRITING
f_out.write('edgedef>source VARCHAR,target VARCHAR,directed BOOLEAN,weight DOUBLE\n')
for tupleAuthors, weight in listOfLinks.items():
    write = tupleAuthors[0] + ',' + tupleAuthors[1] + ',False,' + str(weight) + '\n'
    f_out.write(write)
f_out.close()




#print(listOfAuthors)
#print(listOfLinks)
