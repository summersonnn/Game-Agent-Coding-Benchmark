
import re
from pathlib import Path

# Mocking the load_stored_agent logic
def load_stored_agent(agent_path, agent_idx):
    content = Path(agent_path).read_text()
    lines = content.split("\n")
    code_start = 0
    in_docstring = False
    for i, line in enumerate(lines):
        if '"""' in line:
            if in_docstring:
                code_start = i + 1
                break
            else:
                in_docstring = True
    code_lines = lines[code_start:]
    imports = []
    for line in code_lines:
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            if "random" not in stripped:
                imports.append(stripped)
    code = "\n".join(code_lines)
    code = re.sub(r"class\s+Connect4Agent\b", f"class Connect4Agent_{agent_idx}", code)
    return code.strip(), "\n".join(imports)

# Paths
grok_path = "/home/kubilay/Projects/Competitive-LLM-Agents/agents/x-ai-grok-code-fast-1/A5-Connect4RandomStart_1.py"
gpt5_path = "/home/kubilay/Projects/Competitive-LLM-Agents/agents/openai-gpt-5-mini/A5-Connect4RandomStart_1.py"

code1, imp1 = load_stored_agent(grok_path, 1)
code2, imp2 = load_stored_agent(gpt5_path, 2)

extra_imports = "\n".join(set(imp1.split("\n") + imp2.split("\n")))

# Game Code Template (simplified for syntax check)
template = """
import sys
import random
import signal
import copy

MOVE_TIMEOUT = 1.0

{extra_imports}

{agent1_code}

{agent2_code}

def main():
    print("HELLO")

if __name__ == "__main__":
    main()
"""

game_code = template.format(
    extra_imports=extra_imports,
    agent1_code=code1,
    agent2_code=code2
)

# Check for syntax errors
try:
    compile(game_code, "<string>", "exec")
    print("Syntax OK")
except Exception as e:
    print(f"Syntax Error: {e}")
    # Print lines around the error
    lines = game_code.split("\n")
    if hasattr(e, 'lineno'):
        start = max(0, e.lineno - 5)
        end = min(len(lines), e.lineno + 5)
        for i in range(start, end):
            print(f"{i+1}: {lines[i]}")
