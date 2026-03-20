"""
更新现有模型的 config_schema
"""
import json
import os
import sys
import io
from database import get_db
import crud

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

db = next(get_db())

# 更新现有模型的 config_schema
models_to_update = {
    'grok-video-3': 'modelVideoConfigDemo.json',
    'nano-banana-2': 'modelPictureDemo.json'
}

for model_id, json_file in models_to_update.items():
    model = crud.get_model_by_id(db, model_id)
    if model and not model.config_schema:
        try:
            config_path = os.path.join(PROJECT_ROOT, json_file)
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            model.config_schema = config
            db.commit()
            print(f'[OK] Updated {model_id}')
        except Exception as e:
            print(f'[ERROR] Failed to update {model_id}: {e}')
    elif model and model.config_schema:
        print(f'[SKIP] {model_id} already has config_schema')
    else:
        print(f'[SKIP] {model_id} not found')

# 列出所有模型
print('\n当前所有模型:')
models = crud.get_all_models(db)
for m in models:
    schema = m.config_schema
    has_schema = 'YES' if schema else 'NO'
    print(f'  - {m.model_id}: {m.display_name} (config_schema: {has_schema})')

print('\nDone!')