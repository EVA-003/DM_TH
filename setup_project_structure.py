# -*- coding: utf-8 -*-
import os

directories = [
    "config",
    "src",
    "src/ingestion",
    "src/processing",
    "src/datamart",
    "src/exports",
    "data",
    "data/bronze",
    "data/silver",
    "data/gold",
    "data/outputs",
    "app",
    "notebooks"
]

for d in directories:
    os.makedirs(d, exist_ok=True)
    init_file = os.path.join(d, "__init__.py")
    if not d.startswith("data") and not d.startswith("notebooks") and not d.startswith("app"):
        if not os.path.exists(init_file):
            with open(init_file, "w", encoding="utf-8") as f:
                f.write("# -*- coding: utf-8 -*-\n")

print("Project directory structure created successfully!")
