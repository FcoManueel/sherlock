# Copyright 2015 IBM Corp. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from flask import Flask, jsonify, request, render_template
from github import Github
import pickle


def get_classifier():
    f = open('commit_msg_classifier.pickle', 'rb')
    classifier = pickle.load(f)
    f.close()
    return classifier

app = Flask(__name__)
github = None
classifier = get_classifier()
github_url = 'github.com/'


@app.route('/')
def Index():
    return render_template('main.html')


@app.route('/analyze', methods=['POST'])
def AnalyzeRepo():
    repoURL = request.form['repoUrl']
    analysis = analyzeFromUrl(repoURL)
    return render_template('analysis_results.html', analysis=analysis)


# analyzeFromUrl returns an object containing relevant data about a repository
def analyzeFromUrl(repo_url):
    repo = getRepo(repo_url)
    categories_per_file = getCategoriesDict(repo)
    analysis = {"repo_url": repo_url, "commit_categories": categories_per_file}
    return analysis


# getRepo parses a repo_url to get a repo_id and gets the repository object
def getRepo(repo_url):
    gh_url_index = repo_url.find(github_url)
    repo_id = repo_url  # e.g. 'https://github.com/go-pg/pg'
    if gh_url_index != -1:
        repo_id = repo_id[gh_url_index + len(github_url):]  # e.g. 'go-pg/pg'
    return github.get_repo(repo_id, False)


# getCategoriesDict returns a dictionary of "filename -> "
def getCategoriesDict(repo):
    categories_per_file = {}
    root_tree = repo.get_git_tree(sha="master", recursive=True).tree

    remaining_files = 5 # temporary flag to avoid github ratelimit
    for gh_file in root_tree:
        if not remaining_files:
            break
        categories_per_file[gh_file.path] = [0, 0, 0, 0]  # init commit counter
        remaining_files -= 1
    for file_path in categories_per_file:
        commits = repo.get_commits(path=file_path)
        categories_per_file[file_path] = getCategoryCount(commits)
    return categories_per_file


# getCategoryCount recieves a list of commits and returns a list with a category count, which can be interpreted as:
# [unknown_count,   new_feature_count,   refactor_count,  fix_count]
def getCategoryCount(commits):
    category_count = [0, 0, 0, 0]
    for commit in commits:
        category = getCommitCategory(commit.commit.message)
        category_count[category] += 1
    return category_count


# getCommitCategory returns an integer representing one of the following categories:
# 0: unknown        # 1: new_feature     # 2: refactor       # 3: fix
def getCommitCategory(commit_message):
    commit_categories = {
        "Unknown": 0,
        "New Feature": 1,
        "Refactor": 2,
        "Fix": 3,
    }
    words = getWordList(commit_message)
    commit_category_string = classifier.classify(words)
    return commit_categories[commit_category_string]


def getWordList(commit_message):
    commit_message = commit_message.replace("\n", "").replace(",", " ").replace("- ", "").replace("the ", " ").replace(" and", " ").replace(" from", " ")
    return commit_message.split(" ")

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
    gh_username = os.getenv('SHERLOCK_GITHUB_USERNAME', 'username')
    gh_password = os.getenv('SHERLOCK_GITHUB_PASSWORD', 'password')
    github = Github(gh_username, gh_password)
    app.run(host='0.0.0.0', port=int(port), debug=True)
