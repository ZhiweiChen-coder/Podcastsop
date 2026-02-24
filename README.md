## 播客文案编辑器（Streamlit）

一个面向 **播客、公众号深度访谈、社媒素材** 的文案编辑器，基于 SOP 流程分步生成并可视化编辑 A/B/C/D/E 五个模块的结果。

### 本地运行

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

### 配置 DeepSeek 模型

1. 将仓库中的 `.env.example` 复制为 `.env`
2. 在 `.env` 中填写你的 `DEEPSEEK_API_KEY`
3. DeepSeek 控制台地址：<https://platform.deepseek.com/>
4. 应用启动时会通过 `python-dotenv` 自动加载环境变量

