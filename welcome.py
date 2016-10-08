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
from random import randint
from IPython import embed

app = Flask(__name__)

@app.route('/')
def Welcome():
    return render_template('layout.html')

@app.route('/analyze', methods=['POST'])
def AnalyzeRepo():
    repoURL = request.form['repoUrl']
    categoriesPerFile = analyzeFromUrl(repoURL)
    categoriesPerFile["repo_base_url"] = repoURL
    return jsonify(categoriesPerFile)

def analyzeFromUrl(repo_url):
    gh_username = os.getenv('SHERLOCK_GITHUB_USERNAME', 'username')
    gh_password = os.getenv('SHERLOCK_GITHUB_PASSWORD', 'password')
    g = Github(gh_username, gh_password)
    github_url = 'github.com/'
    gh_url_index = repo_url.find(github_url)
    repo_id = repo_url # e.g. 'https://github.com/go-pg/pg'
    if gh_url_index != -1:
        repo_id = repo_id[gh_url_index+len(github_url):] # e.g. 'go-pg/pg'
    repo = g.get_repo(repo_id, False)
    root_dir = repo.get_git_tree(sha="master", recursive=True)

    fileHash = getHashFromTree(repo, root_dir.tree)
    return fileHash

def getHashFromTree(repo, tree):
    fileHash = {}
    remaining_files = 5
    for gh_file in tree:
        if not remaining_files:
            break
        fileHash[gh_file.path] = [0, 0, 0, 0]  # init commit counter
        remaining_files -= 1
    for file_path in fileHash:
        commits = repo.get_commits(path=file_path)
        for commit in commits:
            fileHash[file_path][randint(0, 3)] += 1  # Replace with model results.
    return fileHash

# @app.route('/api/people')
# def GetPeople():
#     list = [
#         {'name': 'John', 'age': 28},
#         {'name': 'Bill', 'val': 26}
#     ]
#     return jsonify(results=list)
#
# @app.route('/api/people/<name>')
# def SayHello(name):
#     message = {
#         'message': 'Hello ' + name
#     }
#     return jsonify(results=message)

port = os.getenv('PORT', '5000')
if __name__ == "__main__":
	app.run(host='0.0.0.0', port=int(port), debug=True)
