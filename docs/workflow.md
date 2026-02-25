日常改动
git checkout main
# 改代码
git add .
git commit -m "xxx"
git push

大改 / UI 重构 / 架构调整
git checkout -b feature/xxx
# 改一堆
git commit
git checkout main
git merge feature/xxx
git push
