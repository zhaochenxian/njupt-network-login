# 贡献指南（简版）

欢迎 PR 和 Issue。

## 流程

1. Fork 并新建分支：

```bash
git checkout -b feature/xxx
```

2. 安装依赖并自测：

```bash
pip install -r requirements.txt
python src/main.py
```

3. 提交并发起 PR：

```bash
git add .
git commit -m "feat: 描述你的改动"
git push origin feature/xxx
```

## 约定

- 不要提交 `config/config.json`（敏感信息）
- 提交信息建议使用：`feat` / `fix` / `docs` / `chore`
- 保持改动小而清晰，避免无关重构

## 问题反馈

- Bug：提 Issue（附重现步骤与日志）
- 新需求：提 Feature Issue

## 📜 许可证

所有贡献都将在 [MIT License](LICENSE) 下发布。

---

感谢你的贡献！🎉
