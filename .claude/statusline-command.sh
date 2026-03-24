#!/bin/bash

dir=$(basename "$PWD")
branch=$(git branch --show-current 2>/dev/null || echo "")
usage=$(npx -y ccusage 2>/dev/null | tail -1)

echo "${dir} | ${branch} | ${usage}"
