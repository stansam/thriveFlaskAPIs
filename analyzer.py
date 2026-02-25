import os
import glob
import re
import json

TARGET_DIRS = [
    'app/models',
    'app/repository',
    'app/services',
    'app/dto',
    'app/auth',
    'app/admin',
    'app/client',
    'app/main',
    'app/utils',
    'app/templates/email',
    'app/sockets'
]

def analyze_codebase():
    report = {"files_scanned": 0, "findings": {}}
    
    # Also include celery_worker.py
    files_to_scan = ['celery_worker.py']
    
    for d in TARGET_DIRS:
        for root, _, files in os.walk(d):
            if '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.pyc'):
                    continue
                files_to_scan.append(os.path.join(root, f))
                
    report['total_files'] = len(files_to_scan)
    
    for filepath in files_to_scan:
        if not os.path.exists(filepath):
            continue
            
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            report['files_scanned'] += 1
            
            # Simple heuristic analysis
            has_mock = 'mock' in content.lower()
            has_todo = 'todo' in content.lower()
            todos = re.findall(r'(?i)#\s*todo.*', content)
            mocks = re.findall(r'(?i)mock.*', content)
            
            # For services/repositories, check for pass/NotImplementedError
            has_pass = re.search(r'\bpass\b', content) is not None
            has_not_impl = 'NotImplementedError' in content
            
            if has_mock or has_todo or has_pass or has_not_impl:
                report['findings'][filepath] = {
                    "has_mock": has_mock,
                    "has_todo": has_todo,
                    "todos": list(set(todos))[:5], # limit to 5
                    "has_pass": has_pass,
                    "has_not_implemented_error": has_not_impl
                }
                
    with open('/tmp/analysis_report.json', 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Analysis complete. Scanned {report['files_scanned']} / {report['total_files']} files.")
    print(f"Found {len(report['findings'])} files with potential pending work (TODOs/Mocks).")

if __name__ == '__main__':
    analyze_codebase()
