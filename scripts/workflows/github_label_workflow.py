#!/usr/bin/env python3

import os
import json
import requests

# github label workflow for tf-instacart
# opened            : ["requires-review"]
# reopened          : ["requires-review"]
# synchronize       : ["requires-review"]
# ready_for_review  : ["requires-review"]
# check_failure     : ["requires-review"]
# review_approved   : ["awaiting-apply"]

# Diff size configuration
SIZE_XS=10
SIZE_S=50
SIZE_M=100
SIZE_L=200

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPOSITORY = os.getenv("GITHUB_REPOSITORY", "champs/testworkflow")

PR_NUMBER = os.getenv("PR_NUMBER")

URI="https://api.github.com"
REPO_URL = f"{URI}/repos/{GITHUB_REPOSITORY}"

API_HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
    "Content-Type": "application/json"
}


# helper function

def get_pr(pr_number):
    """ getting PR data """
    r = requests.get(f"{REPO_URL}/pulls/{pr_number}", headers=API_HEADERS)
    return r.json()

def get_reviews(pr_number):
    """ getting PR reviews
    """
    r = requests.get(f"{REPO_URL}/pulls/{pr_number}/reviews", headers=API_HEADERS)
    print(json.dumps(r.json(), indent=3))
    return [reviews["state"] for reviews in r.json() if reviews["state"] != "COMMENTED"]

def get_labels(pr_number):
    """ getting PR's labels """
    r = requests.get(f"{REPO_URL}/issues/{pr_number}/labels", 
        headers=API_HEADERS)
    return [res['name'] for res in r.json()]

def add_labels(pr_number, labels):
    r = requests.post(f"{REPO_URL}/issues/{pr_number}/labels", 
        headers=API_HEADERS,
        data=json.dumps({"labels": labels}))
    print("Adding Labels", labels)
    print(r.json())

def remove_labels(pr_number, labels):
    print("Removing Labels", labels)
    for label in labels:
        r = requests.delete(f"{REPO_URL}/issues/{pr_number}/labels/{label}", 
            headers=API_HEADERS)
        print(r.json())

def manage_labels(pr_number, adding_labels, available_labels):
    """
    Adding labels
    Removing all other labels from available_labels
    """

    add_labels(pr_number, adding_labels)
    existing_labels = get_labels(pr_number)
    removing_labels = set(existing_labels) & (set(available_labels) - set(adding_labels))
    print("existing", existing_labels)
    print("removing", removing_labels)
    remove_labels(pr_number, removing_labels)



# label workflows
def label_pr_by_size(pr_number):
    """ Check PR size
    """
    all_size_labels = [        
        "size-XS",
        "size-S",
        "size-M",
        "size-L",
        "size-XL"
    ]

    data = get_pr(pr_number)
    diffsize = data.get("additions", 0) + data.get("deletions", 0)

    if diffsize < SIZE_XS:
        label = "size-XS"
    elif diffsize < SIZE_S:
        label = "size-S"
    elif diffsize < SIZE_M:
        label = "size-M"
    elif diffsize < SIZE_L:
        label = "size-L"
    else:
        label = "size-XL"
    
    manage_labels(pr_number, 
        adding_labels=[label], 
        available_labels=all_size_labels)

def label_pr_by_state(pr_number):
    """ Check PR state
    """
    state_mapping = {
        "CHANGES_REQUESTED": "changes-requested",
        "APPROVED": "awaiting-apply",
    }

    data = get_pr(pr_number)
    reviews = get_reviews(pr_number)
    print(reviews)
    draft = data["draft"]
    state = data["state"]

    all_state_labels = [
        "wip", 
        "requires-review",
        "changes-requested",
        "awaiting-apply"
    ]

    if draft:
        label = "wip"
    elif state in state_mapping:
        label = state_mapping[state]
    else:
        label = "requires-review"
    # last review activity
    if reviews:
        if reviews[-1] in state_mapping:
            label = state_mapping[reviews[-1]]
        else:
            print(reviews)

    manage_labels(pr_number, 
        adding_labels=[label], 
        available_labels=all_state_labels)

if __name__ == "__main__":
    label_pr_by_state(PR_NUMBER)
    label_pr_by_size(PR_NUMBER)
