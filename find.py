import requests
import json
import time
from pathlib import Path

# ===================== 配置区 修改这里 =====================
GITHUB_TOKEN = "your-github-token，推荐细粒度token，速度更快，请求量也大"
TOKEN_TYPE = "Bearer"       # fine-grained token固定Bearer
MIN_STAR = 500
MAX_STAR = 600
OUTPUT_FILE = "./found/issuesAndcomments.json"
HEADERS = {"Authorization": f"{TOKEN_TYPE} {GITHUB_TOKEN}"}
# ==========================================================

# 全局存储
result_data = {}
seen_repos = set()  # 存储已抓取仓库全名 owner/repo

class GitHubRepoFinder:
    def __init__(self):
        pass

    def save_json(self):
        """保存数据到文件"""
        # 确保found文件夹存在
        Path("./found").mkdir(exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已持久保存至 {OUTPUT_FILE}")

    def safe_request(self, url, params=None):
        """统一请求封装，处理限流403"""
        while True:
            resp = requests.get(url, headers=HEADERS, params=params)
            if resp.status_code == 403:
                reset_ts = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait = reset_ts - time.time() + 10
                print(f"⚠️ 触发限流，等待{wait:.0f}秒")
                time.sleep(wait)
                continue
            if resp.status_code == 200:
                return resp
            print(f"❌ 请求失败 code:{resp.status_code} url:{url}")
            time.sleep(3)
            continue

    def fetch_all_open_issues(self, repo_full_name: str):
        """获取仓库全部open issue，过滤PR"""
        issue_urls = []
        page = 1
        per_page = 100
        while True:
            url = f"https://api.github.com/repos/{repo_full_name}/issues"
            params = {"state": "open", "per_page": per_page, "page": page}
            resp = self.safe_request(url, params=params)
            items = resp.json()
            if not items:
                break
            for item in items:
                if "pull_request" not in item:
                    issue_urls.append(item.get("url"))
            page += 1
            time.sleep(0.7)
            print(f"当前仓库已获取 {len(issue_urls)} 个 open issue")
        return issue_urls

    def fetch_issue_comments(self, issue_url: str):
        """获取单个issue所有评论文本"""
        comment_texts = []
        page = 1
        per_page = 100
        while True:
            url = f"{issue_url}/comments"
            params = {"per_page": per_page, "page": page}
            resp = self.safe_request(url, params=params)
            items = resp.json()
            if not items:
                break
            for c in items:
                body = c.get("body", "").strip()
                if body:
                    comment_texts.append(body)
            page += 1
            time.sleep(0.5)
        return comment_texts

    def process_repo(self, repo):
        """处理单个仓库，已抓取直接跳过"""
        full_name = repo["full_name"]
        repo_html = repo["html_url"]

        # 核心去重判断
        if full_name in seen_repos:
            print(f"已跳过已持久化仓库 {full_name}")
            return

        seen_repos.add(full_name)
        print(f"\n===== 处理仓库 {full_name} star:{repo['stargazers_count']} ====")

        issue_urls = self.fetch_all_open_issues(full_name)
        if not issue_urls:
            print(f"{full_name} 无open issues")
            result_data[repo_html] = {}
            self.save_json()
            return

        result_data[repo_html] = {}
        current_issue_count = 1
        for issue_url in issue_urls:
            comments = self.fetch_issue_comments(issue_url)
            result_data[repo_html][issue_url] = comments
            print(f"进度:{current_issue_count}/{len(issue_urls)} | {len(comments)} 条评论")
            current_issue_count += 1
        self.save_json()
        print(f"✅ {full_name} 抓取完成，已写入本地文件")

    def fetch_single_star_query(self, min_s: int, max_s: int):
        page = 1
        per_page = 100
        hit_max_page = False
        last_star = 0
        while page <= 10:
            q = f"stars:{min_s}..{max_s}"
            params = {
                "q": q,
                "sort": "stars",
                "order": "asc", # 反序用desc
                "per_page": per_page,
                "page": page
            }
            resp = self.safe_request("https://api.github.com/search/repositories", params=params)
            data = resp.json()
            items = data.get("items", [])
            if not items:
                break
            for repo in items:
                self.process_repo(repo)
            if page == 10:
                hit_max_page = True
                last_star = items[-1]["stargazers_count"]
                print(f"⚠️ 区间{min_s}~{max_s}达到1000条上限，剩余仓库star ≤ {last_star}")
            page += 1
            time.sleep(1)
        return hit_max_page, last_star

    def split_and_fetch_star_range(self, min_start: int, max_start: int):
        current_min = min_start
        current_max = max_start
        while True:
            print(f"\n开始抓取星数 {current_min} ~ {current_max}区间的仓库")
            hit_limit, last_star = self.fetch_single_star_query(current_min, current_max)
            if hit_limit and int(last_star) == max_start:
                print(f"✅ 区间 {current_min} ~ {current_max} 全部抓取完毕")
                break
            current_min = last_star

if __name__ == "__main__":
    finder = GitHubRepoFinder()
    # 加载本地持久化文件，恢复已抓取仓库列表
    if Path(OUTPUT_FILE).exists():
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            result_data = json.load(f)
        # 遍历本地仓库url，提取owner/repo存入seen_repos
        for repo_url in result_data.keys():
            # https://github/xxx/yyy -> xxx/yyy
            repo_full = repo_url.replace("https://github.com/", "")
            seen_repos.add(repo_full)
        print(f"📂 加载本地缓存，已抓取仓库总数：{len(seen_repos)} 个，重启不再重复抓取")

    print(f"\n开始抓取 stars ≥ {MIN_STAR} 仓库，自动拆分超大区间")
    finder.split_and_fetch_star_range(MIN_STAR, MAX_STAR)
    print("\n🎉 全部抓取任务结束！")
    finder.save_json()