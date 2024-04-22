#!/bin/bash

# Bash script to rename 'main' branch to 'main_bak_{today_date}' and push current branch as new 'main'

# Set the date for the backup branch name
TODAY_DATE=$(date +%Y-%m-%d)

# Automatically fetch the current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Step 1: Rename the local 'main' branch
git checkout main
git branch -m main "main_bak_${TODAY_DATE}"

# Step 2: Update remote branches
git push origin "main_bak_${TODAY_DATE}"
git push origin --delete main

# Step 3: Push the current branch as the new 'main'
git checkout $CURRENT_BRANCH
git push origin "${CURRENT_BRANCH}:main"

echo "Branch 'main' has been renamed to 'main_bak_${TODAY_DATE}' and '${CURRENT_BRANCH}' is now the new 'main'."
