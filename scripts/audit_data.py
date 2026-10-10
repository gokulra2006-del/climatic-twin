import os
from pathlib import Path

data_dir = Path("data")
exclude_dirs = {"venv", ".venv", "__pycache__"}

print(f"{'Source':<30} | {'Files Found':<15} | {'Size (MB)':<10}")
print("-" * 60)

for root, dirs, files in os.walk(data_dir):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    # We only care about leaf directories or directories with data files
    data_files = [f for f in files if f.endswith(('.csv', '.nc', '.json', '.yaml', '.txt', '.pkl', '.tif', '.h5', '.pbf'))]
    if data_files:
        rel_path = Path(root).relative_to(data_dir)
        total_size = sum((Path(root) / f).stat().st_size for f in data_files)
        print(f"{str(rel_path):<30} | {len(data_files):<15} | {total_size / (1024*1024):.2f}")
