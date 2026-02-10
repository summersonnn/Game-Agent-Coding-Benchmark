
import re
import os
from pathlib import Path

def setup_sim():
    # Mocking the constants
    AGENTS_DIR = Path("agents")
    GAME_NAME = "A1-Battleship"

    def load_stored_agent(model_folder: str, game: str, run: int, agent_idx: int) -> tuple[str, str]:
        agent_file = AGENTS_DIR / model_folder / f"{game}_{run}.py"
        if not agent_file.exists():
            return "FILE NOT FOUND", ""
        
        content = agent_file.read_text()
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
        class_start_idx = None
        
        for i, line in enumerate(code_lines):
            stripped = line.strip()
            if stripped.startswith("class BattleshipAgent"):
                class_start_idx = i
                break
            if stripped.startswith("import ") or stripped.startswith("from "):
                if "random" not in stripped and "collections" not in stripped:
                    imports.append(stripped)
        
        if class_start_idx is None:
            return "CLASS NOT FOUND", ""
        
        class_lines = []
        in_class = False
        base_indent = 0
        
        for i in range(class_start_idx, len(code_lines)):
            line = code_lines[i]
            stripped = line.strip()
            
            if i == class_start_idx:
                class_lines.append(line)
                in_class = True
                base_indent = len(line) - len(line.lstrip())
                continue
            
            if not stripped or stripped.startswith("#"):
                class_lines.append(line)
                continue
            
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                break
            class_lines.append(line)
        
        agent_code = "\n".join(class_lines)
        agent_code = re.sub(r"\bBattleshipAgent\b", f"BattleshipAgent_{agent_idx}", agent_code)
        return agent_code.strip(), "\n".join(imports)

    # Test Run 1
    code, imps = load_stored_agent("mistralai-mistral-large-2512", "A1-Battleship", 1, 1)
    print("RUN 1 LENGTH:", len(code.split("\n")))
    if len(code.split("\n")) < 5:
        print("RUN 1 FAILED EXTRACTION!")
        print("CODE:")
        print(code)
    
    # Test Run 2
    code, imps = load_stored_agent("mistralai-mistral-large-2512", "A1-Battleship", 2, 1)
    print("RUN 2 LENGTH:", len(code.split("\n")))

if __name__ == "__main__":
    setup_sim()
