import json

MaybeDemand = {}
with open ("./found/issuesAndcomments.json", "r", encoding="utf-8") as file:
    content = file.read()
    repos = json.loads(content)
    print(f'Repos: {len(repos)}')
    for repo in repos:
        issues = repos[repo]
        for issue in issues:
            comments = issues[issue]
            if len(comments) > 0:
                for comment in comments:
                    if "update" in comment.lower() or "更新" in comment or "no plan" in comment.lower():
                        url = "https://github.com/"+issue.split("/repos/")[1]
                        MaybeDemand[url] = comment
# 持久化
with open ("./found/MaybeDemand.json", "w", encoding="utf-8") as file:
    print(f'MaybeDemand: {len(MaybeDemand)}')
    json.dump(MaybeDemand, file, ensure_ascii=False, indent=4)