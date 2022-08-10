import json
import markdown
import random
import requests
from bs4 import BeautifulSoup
from deprecated import deprecated
from replit import db

class Util:
  def cleanup_db():
    Util.print_db()
    for key in db.keys():
      del db[key]

  def print_db():
    print("List of replit db Keys", db.keys())

def get_codechef_daily(source):
  url = source['problem_source']
  plain = requests.get(url).text
  soup = BeautifulSoup(plain, "html.parser")

  # Identifies html tags and creates the message
  div = soup.find('div', {'class': 'l-card-11'})
  problem_title = div.find('p', {'class': 'm-card-11_head-2'}).text
  anchor = div.find('a', {'class': 'm-button-1'})
  link = url + anchor.get('href')

  return {
    "problem_title" : problem_title,
    "link" : link,
    "msg" : source["msg_template"].format(problem_title = problem_title, link = link)
  }

def get_codeforces_random(source):
  current_index = ["A", "B"] # codeforces index to identify difficulty of the problem, lower is easier
  with open('resources/codeforces_problemset.json') as fp:
    problemset = json.load(fp)

  filtered_problems = list(filter(lambda obj: obj['index'] in current_index, problemset['result']['problems']))
  
  # Problem Schema: https://codeforces.com/apiHelp/objects#Problem
  # {'contestId': 612, 'index': 'A', 'name': 'The Text Splitting', 'type': 'PROGRAMMING', 'rating': 1300, 'tags': ['brute force', 'implementation', 'strings']}
  problem = random.choice(filtered_problems)
  problem_title = problem['name'] 
  link = f"{source['problem_dest']}/{problem['contestId']}/{problem['index']}"

  return {
    "problem_title" : problem_title,
    "link" : link,
    "msg" : source["msg_template"].format(problem_title = problem_title, link = link, tags = problem['tags'])
  }

@deprecated(reason="now a legacy impl")
def export_leetcodeMD_toJSON(source):
  url = source['problem_source']
  rawMD = requests.get(url).text.split('\n')

  # A boolean that identifies that a '## Algorithms' header was identified so we can start to parse the required markdown table
  isAlgo = False 
  problemset = []
  for line in rawMD:
    if "## Shell" in line:
      break
    if "## Algorithms" in line:
      isAlgo = True
      continue
    if isAlgo:
      if (
        len(line) == 0
        or '## Database' in line # '## Database' section markdown table which can also be parsed
        or '#' in line and 'Video' in line and 'Tag' in line
        or '|---' in line
      ):
        # ignore headers and empty lines  
        # print(line)
        continue
      
      problemset.append(line.split('|'))

  problemListJSON = []
  for problem in problemset:
    plain = markdown.markdown(problem[2].strip())
    soup = BeautifulSoup(plain, "html.parser")
    anchor = soup.find('a')

    problem_num = problem[1].strip()
    if (anchor is None or not anchor.contents[0]):
      # print(problem)
      continue
    
    problem_title = anchor.contents[0]
    link = anchor.get('href')
    difficulty = problem[5].strip()
    tags = ''
    if len(problem) -1 > 5:
      tags = problem[6].strip()
      # print(tags)
    
    problemListJSON.append(
      {
      "id" : problem_num, 
      "title" : problem_title, 
      "link" : link, 
      "difficulty" : difficulty,
      "tags" : tags
      }
    )
  
  problemListJSON.sort(key=lambda k: int(k['id']))
  jsonStr = json.dumps(problemListJSON)
  
  # Display total number of problems
  # previousCount = 1465
  # print (f'\nTotal Number of Leetcode problems \nPrevious count: {previousCount} \nCurrent count: {len(problemListJSON)}')

  with open('resources/legacy_leetcode.json', 'w') as file: 
    file.writelines(jsonStr)
    file.close()

@deprecated(reason="now a legacy impl")
def get_legacy_leetcode(source):
  # export_leetcodeMD_toJSON(source)
  with open('resources/legacy_leetcode.json') as fp:
    problemListJSON = json.load(fp)
  problem = random.choice(problemListJSON)
  msg = source["msg_template"].format(id = problem['id'], title = problem['title'], difficulty = problem['difficulty'], link = problem['link'])
  return {
    "problem_title" : problem['title'],
    "link" : problem['link'],
    "msg" : msg
  }

def get_leetcode_random(source):
  with open('resources/leetcode_problems.json') as fp:
    problemListJSON = json.load(fp)
  
  # Filter
  problemListJSON = problemListJSON['data']['questions']
  problemListJSON = list(filter(lambda obj: obj['paidOnly'] != True, problemListJSON))
  # problemListJSON.sort(key=lambda k: int(k['frontendQuestionId'])) # Sort based on id

  problem = random.choice(problemListJSON)
  tags = list(tag['name'] for tag in problem['topicTags'])
  tags.insert(0, problem['difficulty'])

  problem = {
    "id" : problem['frontendQuestionId'],
    "title" : problem['title'],
    "tags" : tags,
    "link" : source['problem_dest'] + problem['titleSlug']
  }

  msg = source["msg_template"].format(id = problem['id'], title = problem['title'], tags = problem['tags'], link = problem['link'])
  return {
    "problem_title" : problem['title'],
    "link" : problem['link'],
    "msg" : msg
  }

def scrape_daily_problem(source):
  source_name = source['name']
  if source_name == "codechef":
    return get_codechef_daily(source)

  elif source_name == "codeforces":
    return get_codeforces_random(source)

  elif source_name == "leetcode":
    return get_leetcode_random(source)

  elif source_name == "legacy-leetcode":
    return get_legacy_leetcode(source)

  else:
    return {
      "problem_title" : "Bad Implementation",
      "link" : "Bad Implementation",
      "msg" : "Bad Implementation"
    }

# # For Testing 
# source = {
#   "name" : "leetcode",
#   "problem_source" : "https://leetcode-api-1d31.herokuapp.com", # Not required for now, since using offline source
#   "problem_dest" : "https://leetcode.com/problems/",
#   "msg_template" : "**Leetcode - Random daily (Experimental)**\n{id} - {title}\n||**{tags}**||\n{link}"
# }

# out = scrape_daily_problem(source)
# print(out['msg'])

# Get JSON output for legacy implementation
# # export_leetcodeMD_toJSON(source)