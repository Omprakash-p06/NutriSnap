import os
import re

directories = ['src', 'scripts', 'tests', 'scratch', 'configs']
for directory in directories:
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.py', '.yaml', '.txt', '.json')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    continue
                
                # Replace 'data/...' with 'datasets/...'
                new_content = re.sub(r'([\'"])data/', r'\g<1>datasets/', content)
                # Replace 'models/checkpoints/...' with 'checkpoints/...'
                new_content = re.sub(r'([\'"])models/checkpoints/', r'\g<1>checkpoints/', new_content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")
