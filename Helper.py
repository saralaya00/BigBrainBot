import json
import markdown
import random
import requests
from bs4 import BeautifulSoup
from datetime import date
from deprecated import deprecated


class Helper:
    EMPTY_STR = ""
    sources_to_use = ["leetcode", "sqleetcode"]
    # todo: use dict implementation instead of list
    sources = [
        {
            "name": "leetcode",  # Not required for now, since using offline source
            "problem_source": "https://leetcode-api-1d31.herokuapp.com",
            "problem_dest": "https://leetcode.com/problems/",
            "msg_template": "**Leetcode - Random daily**\n{id} - {title}\n||{tags}||\n{link}",
        },
        {
            "name": "sqleetcode",  # Not required for now, since using offline source
            "problem_source": "https://leetcode-api-1d31.herokuapp.com",
            "problem_dest": "https://leetcode.com/problems/",
            "msg_template": "**SQLeetcode - Random daily**\n{id} - {title}\n||{tags}||\n{link}",
        },
        {
            "name": "legacy-leetcode",  # md source, backup in https://github.com/saralaya00/Leetcode
            "problem_source": "https://raw.githubusercontent.com/fishercoder1534/Leetcode/master/README.md",
            "problem_dest": "https://leetcode.com/problems/",  # Not required for now
            "msg_template": "**Leetcode - Random daily**\n{id} - {title} ||**{difficulty}**||\n{link}",
        },
        {
            "name": "codeforces",  # API Source where we can get the problemset json (manually used for now)
            "problem_source": "https://codeforces.com/api/problemset.problems",
            "problem_dest": "https://codeforces.com/problemset/problem",
            "msg_template": "**Codeforces - Random daily**\n{problem_title}\n||{tags}||\n{link}",
        },
    ]

    TODO_format = f"""
** {date.today().strftime("%A %b %d %Y")} **
>>> :dart: **Target**
$targets:fire: **Done**
$done"""

    DONE_format = f"""
** {date.today().strftime("%A %b %d %Y")} **
>>> :100: **Things Done**
$targets"""

    def get_codeforces_random(self, source):
        # codeforces index to identify difficulty of the problem, lower is
        # easier
        current_index = ["A", "B"]
        with open("resources/codeforces_problemset.json") as fp:
            problemset = json.load(fp)

        filtered_problems = list(
            filter(
                lambda obj: obj["index"] in current_index,
                problemset["result"]["problems"],
            )
        )

        # Problem Schema: https://codeforces.com/apiHelp/objects#Problem
        # {'contestId': 612, 'index': 'A', 'name': 'The Text Splitting', 'type': 'PROGRAMMING', 'rating': 1300, 'tags': ['brute force', 'implementation', 'strings']}
        problem = random.choice(filtered_problems)
        problem_title = problem["name"]
        link = f"{source['problem_dest']}/{problem['contestId']}/{problem['index']}"

        return {
            "problem_title": problem_title,
            "link": link,
            "msg": source["msg_template"].format(
                problem_title=problem_title, link=link, tags=problem["tags"]
            ),
        }

    @deprecated(reason="now a legacy impl")
    def export_leetcodeMD_toJSON(self, source):
        url = source["problem_source"]
        rawMD = requests.get(url).text.split("\n")

        # A boolean that identifies that a '## Algorithms' header was
        # identified so we can start to parse the required markdown table
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
                    or "## Database"
                    in line  # '## Database' section markdown table which can also be parsed
                    or "#" in line
                    and "Video" in line
                    and "Tag" in line
                    or "|---" in line
                ):
                    # ignore headers and empty lines
                    # print(line)
                    continue

                problemset.append(line.split("|"))

        problemListJSON = []
        for problem in problemset:
            plain = markdown.markdown(problem[2].strip())
            soup = BeautifulSoup(plain, "html.parser")
            anchor = soup.find("a")

            problem_num = problem[1].strip()
            if anchor is None or not anchor.contents[0]:
                # print(problem)
                continue

            problem_title = anchor.contents[0]
            link = anchor.get("href")
            difficulty = problem[5].strip()
            tags = ""
            if len(problem) - 1 > 5:
                tags = problem[6].strip()
                # print(tags)

            problemListJSON.append(
                {
                    "id": problem_num,
                    "title": problem_title,
                    "link": link,
                    "difficulty": difficulty,
                    "tags": tags,
                }
            )

        problemListJSON.sort(key=lambda k: int(k["id"]))
        jsonStr = json.dumps(problemListJSON)

        # Display total number of problems
        # previousCount = 1465
        # print (f'\nTotal Number of Leetcode problems \nPrevious count: {previousCount} \nCurrent count: {len(problemListJSON)}')

        with open("resources/legacy_leetcode.json", "w") as file:
            file.writelines(jsonStr)
            file.close()

    @deprecated(reason="now a legacy impl")
    def get_legacy_leetcode(self, source):
        # export_leetcodeMD_toJSON(source)
        with open("resources/legacy_leetcode.json") as fp:
            problemListJSON = json.load(fp)
        problem = random.choice(problemListJSON)
        msg = source["msg_template"].format(
            id=problem["id"],
            title=problem["title"],
            difficulty=problem["difficulty"],
            link=problem["link"],
        )
        return {"problem_title": problem["title"], "link": problem["link"], "msg": msg}

    def get_leetcode_random(self, source, get_sql=False):
        with open("resources/leetcode_problems.json") as fp:
            problemListJSON = json.load(fp)

        # Filter
        problemListJSON = problemListJSON["data"]["questions"]
        problemListJSON = list(
            filter(lambda obj: obj["paidOnly"] != True, problemListJSON)
        )

        def filter_sql(problemListJSON, get_sql):
            sql_tag = "Database"
            sqlListJSON = list()
            codeListJSON = list()
            for obj in problemListJSON:
                for tag in obj["topicTags"]:
                    if sql_tag == tag["name"]:
                        sqlListJSON.append(obj)
                    else:
                        codeListJSON.append(obj)
            return sqlListJSON if get_sql else codeListJSON

        problemListJSON = filter_sql(problemListJSON, get_sql)
        # problemListJSON.sort(key=lambda k: int(k['frontendQuestionId'])) #
        # Sort based on id

        problem = random.choice(problemListJSON)
        tags = list(tag["name"] for tag in problem["topicTags"])
        tags.insert(0, problem["difficulty"])

        problem = {
            "id": problem["frontendQuestionId"],
            "title": problem["title"],
            "tags": tags,
            "link": source["problem_dest"] + problem["titleSlug"],
        }

        msg = source["msg_template"].format(
            id=problem["id"],
            title=problem["title"],
            tags=problem["tags"],
            link=problem["link"],
        )
        return {"problem_title": problem["title"], "link": problem["link"], "msg": msg}

    # todo: since we have refactored sources, just use it internally
    def get_daily_problem(self, source):
        source_name = source["name"]
        if source_name == "codeforces":
            return self.get_codeforces_random(source)

        elif source_name == "leetcode":
            return self.get_leetcode_random(source, False)

        elif source_name == "sqleetcode":
            return self.get_leetcode_random(source, True)

        elif source_name == "legacy-leetcode":
            return self.get_legacy_leetcode(source)

        else:
            return {
                "problem_title": "Bad Implementation",
                "link": "Bad Implementation",
                "msg": "Bad Implementation",
            }

    #experimental testing required
    def get_valid_counting_number(self, message_content):
        numIndex = -1 # Let's consider this as invalid index since the counting bot only considers the start to n - x as valid number
        for i in range(0,len(message_content)):
            if message_content[i].isdigit():
              numIndex = i
              continue
            else:
              print(message_content[i])
              if message_content[i] == " ":
                break
              else:
                return None
                
        if numIndex == -1:
            return None
        else:
            # print(numIndex)
            return message_content[:numIndex + 1]
          
    def create_todo(self, todos, msg_template, getrawfmt=False):
        default_todo = "Make todo"
        quote_fmt = "> "
        blquote_fmt = ">>> "
        targets = ""
        for todo in todos:
            if todo == self.EMPTY_STR:
                continue
            if todo[:2] == quote_fmt or todo[:4] == blquote_fmt:
                todo = todo.replace(blquote_fmt, self.EMPTY_STR, 1)
                todo = todo.replace(quote_fmt, self.EMPTY_STR, 1)
            targets += todo + "\n"

        todolist = msg_template
        if todos:
            todolist = todolist.replace("$targets", targets)
            todolist = todolist.replace("$done", "~~" + default_todo + "~~\n")
        else:
            todolist = todolist.replace("$targets", default_todo + "\n")
            todolist = todolist.replace("$done", "...\n")

        if getrawfmt:
            return "```" + todolist + "\n```"
        return todolist


# # For Testing
# source = {
#   "name" : "leetcode",
#   "problem_source" : "https://leetcode-api-1d31.herokuapp.com", # Not required for now, since using offline source
#   "problem_dest" : "https://leetcode.com/problems/",
#   "msg_template" : "**Leetcode - Random daily (Experimental)**\n{id} - {title}\n||**{tags}**||\n{link}"
# }

# out = get_daily_problem(source)
# print(out['msg'])

# Get JSON output for legacy implementation
# # export_leetcodeMD_toJSON(source)

# print(Helper().get_valid_counting_number("999 Hello World!"))