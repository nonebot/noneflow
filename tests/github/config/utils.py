def generate_issue_body(
    module_name: str = "module_name",
    project_link: str = "project_link",
    config: str = "log_level=DEBUG",
):
    return f"""### PyPI 项目名\n\n{project_link}\n\n### 插件 import 包名\n\n{module_name}\n\n### 插件配置项\n\n```dotenv\n{config}\n```"""
