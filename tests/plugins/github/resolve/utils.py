def get_pr_labels(labels: list[str]):
    from githubkit.rest import PullRequestPropLabelsItems as Label

    return [
        Label.model_construct(
            **{
                "color": "2A2219",
                "default": False,
                "description": "",
                "id": 2798075966,
                "name": label,
                "node_id": "MDU6TGFiZWwyNzk4MDc1OTY2",
                "url": "https://api.github.com/repos/he0119/action-test/labels/Remove",
            }
        )
        for label in labels
    ]
