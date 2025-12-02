aimport tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import re
import keyword
import builtins
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CAT'S CURSOR 2.0 - AI-POWERED NOTEPAD++ (NO EXTERNAL LLMS - LOCAL AI AGENTS)
# ══════════════════════════════════════════════════════════════════════════════

class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        try:
            result = self.tk.call((self._orig,) + args)
        except tk.TclError:
            return None
        if args[0] in ("insert", "replace", "delete") or args[0:3] == ("mark", "set", "insert"):
            self.event_generate("<<Change>>", when="tail")
        return result


# ══════════════════════════════════════════════════════════════════════════════
# LOCAL AI AGENTS (NO EXTERNAL API REQUIRED)
# ══════════════════════════════════════════════════════════════════════════════

class AIAgent:
    """Local AI Agent - Pattern-based code intelligence"""
    
    PYTHON_PATTERNS = {
        'def ': 'Function definition',
        'class ': 'Class definition', 
        'import ': 'Module import',
        'from ': 'From import',
        'if ': 'Conditional statement',
        'for ': 'For loop',
        'while ': 'While loop',
        'try:': 'Try block',
        'except': 'Exception handler',
        'with ': 'Context manager',
        'return ': 'Return statement',
        'yield ': 'Generator yield',
        'lambda ': 'Lambda function',
        'async ': 'Async definition',
        'await ': 'Await expression',
    }
    
    COMMON_FIXES = {
        r'print\s+["\']': 'print() needs parentheses in Python 3',
        r'except\s*:': 'Bare except catches all exceptions - specify exception type',
        r'==\s*None': 'Use "is None" instead of "== None"',
        r'!=\s*None': 'Use "is not None" instead of "!= None"',
        r'type\([^)]+\)\s*==': 'Use isinstance() instead of type() comparison',
        r'\[\s*\]\s*=\s*\[\s*\]': 'Mutable default argument - use None instead',
        r'except\s+Exception\s*,': 'Old except syntax - use "except Exception as e:"',
        r'range\(len\(': 'Consider using enumerate() instead of range(len())',
    }
    
    DOCSTRING_TEMPLATES = {
        'function': '''"""
    {description}
    
    Args:
{args}
    
    Returns:
        {returns}
    """''',
        'class': '''"""
    {description}
    
    Attributes:
{attrs}
    """''',
        'module': '''"""
{description}

Author: {author}
Date: {date}
"""'''
    }
    
    COMPLETIONS = {
        'def': 'def function_name(args):\n    """Docstring"""\n    pass',
        'class': 'class ClassName:\n    """Docstring"""\n    \n    def __init__(self):\n        pass',
        'if': 'if condition:\n    pass',
        'for': 'for item in iterable:\n    pass',
        'while': 'while condition:\n    pass',
        'try': 'try:\n    pass\nexcept Exception as e:\n    pass',
        'with': 'with open(filename, "r") as f:\n    content = f.read()',
        'import': 'import module_name',
        'from': 'from module import name',
        'async': 'async def async_function():\n    await something()',
        'lambda': 'lambda x: x',
        'list': '[item for item in iterable]',
        'dict': '{key: value for key, value in items}',
        'main': 'if __name__ == "__main__":\n    main()',
        'init': 'def __init__(self):\n    pass',
        'str': 'def __str__(self):\n    return f"{self.__class__.__name__}"',
        'repr': 'def __repr__(self):\n    return f"{self.__class__.__name__}()"',
        'property': '@property\ndef name(self):\n    return self._name',
        'staticmethod': '@staticmethod\ndef method():\n    pass',
        'classmethod': '@classmethod\ndef method(cls):\n    pass',
        'dataclass': '@dataclass\nclass DataClass:\n    field: type',
        'unittest': 'class TestCase(unittest.TestCase):\n    def test_something(self):\n        self.assertEqual(expected, actual)',
        'argparse': 'parser = argparse.ArgumentParser()\nparser.add_argument("--arg")\nargs = parser.parse_args()',
        'logging': 'logging.basicConfig(level=logging.INFO)\nlogger = logging.getLogger(__name__)',
        'json': 'with open("file.json", "r") as f:\n    data = json.load(f)',
        'requests': 'response = requests.get(url)\ndata = response.json()',
        'flask': '@app.route("/")\ndef index():\n    return "Hello World"',
        'tkinter': 'root = tk.Tk()\nroot.mainloop()',
        'pygame': 'pygame.init()\nscreen = pygame.display.set_mode((800, 600))',
    }
    
    @staticmethod
    def explain_code(code):
        """Analyze and explain code locally"""
        lines = code.strip().split('\n')
        explanations = []
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            for pattern, desc in AIAgent.PYTHON_PATTERNS.items():
                if stripped.startswith(pattern):
                    # Extract name if possible
                    if pattern in ('def ', 'class '):
                        match = re.match(r'(def|class)\s+(\w+)', stripped)
                        if match:
                            name = match.group(2)
                            explanations.append(f"Line {i}: {desc} '{name}'")
                    else:
                        explanations.append(f"Line {i}: {desc}")
                    break
            else:
                # Check for assignments
                if '=' in stripped and not stripped.startswith(('if', 'while', 'elif', '==')):
                    if ':=' in stripped:
                        explanations.append(f"Line {i}: Walrus operator assignment")
                    elif '+=' in stripped or '-=' in stripped or '*=' in stripped:
                        explanations.append(f"Line {i}: Augmented assignment")
                    elif '==' not in stripped and '!=' not in stripped:
                        var = stripped.split('=')[0].strip()
                        explanations.append(f"Line {i}: Variable assignment '{var}'")
        
        if not explanations:
            explanations.append("This code block contains basic Python statements.")
        
        # Add summary
        func_count = len(re.findall(r'\bdef\s+\w+', code))
        class_count = len(re.findall(r'\bclass\s+\w+', code))
        import_count = len(re.findall(r'^(?:import|from)\s+', code, re.MULTILINE))
        
        summary = f"\n📊 Summary: {func_count} functions, {class_count} classes, {import_count} imports"
        
        return '\n'.join(explanations) + summary
    
    @staticmethod
    def find_bugs(code):
        """Find potential bugs and issues"""
        issues = []
        lines = code.split('\n')
        
        # Check each pattern
        for pattern, msg in AIAgent.COMMON_FIXES.items():
            matches = list(re.finditer(pattern, code))
            for match in matches:
                # Find line number
                line_num = code[:match.start()].count('\n') + 1
                issues.append(f"⚠️ Line {line_num}: {msg}")
        
        # Check indentation
        for i, line in enumerate(lines, 1):
            if line and not line.startswith((' ', '\t', '#')) and line[0].isspace():
                issues.append(f"⚠️ Line {i}: Mixed indentation detected")
        
        # Check for common mistakes
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Missing colon
            if re.match(r'^(if|elif|else|for|while|try|except|finally|with|def|class|async)\s+.*[^:]$', stripped):
                if not stripped.endswith(':') and not stripped.endswith(','):
                    issues.append(f"⚠️ Line {i}: Possibly missing colon ':'")
            
            # Unused variable hint
            if '=' in stripped and '_' == stripped.split('=')[0].strip():
                issues.append(f"💡 Line {i}: Underscore variable (intentionally unused)")
            
            # TODO/FIXME
            if 'TODO' in stripped.upper():
                issues.append(f"📝 Line {i}: TODO comment found")
            if 'FIXME' in stripped.upper():
                issues.append(f"🔧 Line {i}: FIXME comment found")
        
        if not issues:
            issues.append("✅ No obvious issues found! Code looks clean.")
        
        return '\n'.join(issues)
    
    @staticmethod
    def generate_docstring(code):
        """Generate docstring for function/class"""
        # Detect function
        func_match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)', code.strip())
        if func_match:
            name = func_match.group(1)
            params = func_match.group(2)
            
            args_list = []
            if params.strip():
                for param in params.split(','):
                    param = param.strip()
                    if param and param != 'self' and param != 'cls':
                        # Handle type hints
                        if ':' in param:
                            pname, ptype = param.split(':')[:2]
                            ptype = ptype.split('=')[0].strip()
                            args_list.append(f"        {pname.strip()} ({ptype}): Description")
                        else:
                            pname = param.split('=')[0].strip()
                            args_list.append(f"        {pname}: Description")
            
            args_str = '\n'.join(args_list) if args_list else "        None"
            
            # Check for return
            returns = "None" if 'return' not in code else "Description of return value"
            
            docstring = f'"""\n    {name.replace("_", " ").title()}\n    \n    Args:\n{args_str}\n    \n    Returns:\n        {returns}\n    """'
            return docstring
        
        # Detect class
        class_match = re.match(r'class\s+(\w+)', code.strip())
        if class_match:
            name = class_match.group(1)
            docstring = f'"""\n    {name} class.\n    \n    Attributes:\n        attr: Description\n    """'
            return docstring
        
        return '"""Description."""'
    
    @staticmethod
    def refactor_code(code):
        """Suggest refactoring improvements"""
        suggestions = []
        lines = code.split('\n')
        
        # Long function check
        in_func = False
        func_start = 0
        func_name = ""
        
        for i, line in enumerate(lines):
            if re.match(r'\s*def\s+\w+', line):
                if in_func and i - func_start > 30:
                    suggestions.append(f"📏 Function '{func_name}' is {i - func_start} lines - consider splitting")
                in_func = True
                func_start = i
                match = re.search(r'def\s+(\w+)', line)
                func_name = match.group(1) if match else "unknown"
        
        # Check final function
        if in_func and len(lines) - func_start > 30:
            suggestions.append(f"📏 Function '{func_name}' is long - consider splitting")
        
        # Nested loops check
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent)
        
        if max_indent > 16:  # More than 4 levels
            suggestions.append("🔄 Deep nesting detected - consider extracting helper functions")
        
        # Magic numbers
        magic_nums = re.findall(r'(?<!["\'])\b(\d{2,})\b(?!["\'])', code)
        if magic_nums:
            suggestions.append(f"🔢 Magic numbers found ({', '.join(set(magic_nums)[:3])}) - consider using constants")
        
        # Duplicate code hints
        line_counts = {}
        for line in lines:
            stripped = line.strip()
            if len(stripped) > 20 and not stripped.startswith('#'):
                line_counts[stripped] = line_counts.get(stripped, 0) + 1
        
        duplicates = [l for l, c in line_counts.items() if c > 1]
        if duplicates:
            suggestions.append(f"📋 Potential duplicate code found - consider extracting to function")
        
        # List comprehension opportunity
        for i, line in enumerate(lines, 1):
            if re.search(r'for\s+\w+\s+in.*:\s*$', line.strip()):
                # Check next line for append
                if i < len(lines) and '.append(' in lines[i]:
                    suggestions.append(f"💡 Line {i}: Loop with append - could use list comprehension")
        
        if not suggestions:
            suggestions.append("✨ Code looks well-structured!")
        
        return '\n'.join(suggestions)
    
    @staticmethod
    def get_completion(prefix):
        """Get code completion suggestions"""
        prefix = prefix.strip().lower()
        
        suggestions = []
        for key, template in AIAgent.COMPLETIONS.items():
            if key.startswith(prefix):
                suggestions.append((key, template))
        
        # Also check Python keywords
        for kw in keyword.kwlist:
            if kw.startswith(prefix) and kw not in [s[0] for s in suggestions]:
                suggestions.append((kw, kw))
        
        # Check builtins
        for name in dir(builtins):
            if name.startswith(prefix) and not name.startswith('_'):
                suggestions.append((name, f"{name}()"))
        
        return suggestions[:15]  # Limit results
    
    @staticmethod
    def chat_response(message):
        """Generate chat response locally"""
        msg_lower = message.lower()
        
        # Greetings
        if any(g in msg_lower for g in ['hello', 'hi', 'hey', 'sup']):
            return "Hey! 🐱 I'm your local AI assistant. Ask me about code!"
        
        # Help
        if 'help' in msg_lower:
            return """🤖 I can help with:
• Explain code - Select code and click Explain
• Find bugs - Debug your code
• Refactor - Get improvement suggestions  
• Generate docstrings - Ctrl+/
• Code completion - Ctrl+.
• Ask me coding questions!"""
        
        # Python questions
        if 'list' in msg_lower and ('create' in msg_lower or 'make' in msg_lower):
            return "Create a list:\n```python\nmy_list = [1, 2, 3]\nmy_list = list(range(10))\nmy_list = [x**2 for x in range(10)]  # comprehension\n```"
        
        if 'dict' in msg_lower and ('create' in msg_lower or 'make' in msg_lower):
            return "Create a dict:\n```python\nmy_dict = {'key': 'value'}\nmy_dict = dict(a=1, b=2)\nmy_dict = {k: v for k, v in items}  # comprehension\n```"
        
        if 'function' in msg_lower and ('create' in msg_lower or 'make' in msg_lower or 'define' in msg_lower):
            return "Define a function:\n```python\ndef my_function(arg1, arg2='default'):\n    '''Docstring'''\n    result = arg1 + arg2\n    return result\n```"
        
        if 'class' in msg_lower and ('create' in msg_lower or 'make' in msg_lower or 'define' in msg_lower):
            return "Define a class:\n```python\nclass MyClass:\n    def __init__(self, value):\n        self.value = value\n    \n    def method(self):\n        return self.value\n```"
        
        if 'loop' in msg_lower or 'iterate' in msg_lower:
            return "Loops in Python:\n```python\n# For loop\nfor item in iterable:\n    print(item)\n\n# While loop\nwhile condition:\n    do_something()\n\n# Enumerate\nfor i, item in enumerate(items):\n    print(i, item)\n```"
        
        if 'file' in msg_lower and ('read' in msg_lower or 'open' in msg_lower):
            return "File operations:\n```python\n# Read file\nwith open('file.txt', 'r') as f:\n    content = f.read()\n\n# Write file\nwith open('file.txt', 'w') as f:\n    f.write('content')\n```"
        
        if 'error' in msg_lower or 'exception' in msg_lower:
            return "Exception handling:\n```python\ntry:\n    risky_operation()\nexcept ValueError as e:\n    print(f'Value error: {e}')\nexcept Exception as e:\n    print(f'Error: {e}')\nfinally:\n    cleanup()\n```"
        
        if 'import' in msg_lower:
            return "Import statements:\n```python\nimport module\nimport module as alias\nfrom module import function\nfrom module import *  # not recommended\n```"
        
        # Default response
        return f"🤔 I'm a local AI - I understand basic Python questions! Try asking about:\n• How to create lists/dicts/functions/classes\n• File operations\n• Loops and iteration\n• Error handling\n• Or use the AI tools on your code!"


# ══════════════════════════════════════════════════════════════════════════════
# FILE TYPES
# ══════════════════════════════════════════════════════════════════════════════

FILE_TYPES = [
    ("All types", "*.*"),
    ("Python", "*.py *.pyw"),
    ("Text", "*.txt"),
    ("C/C++", "*.c *.cpp *.h *.hpp"),
    ("Java", "*.java"),
    ("JavaScript", "*.js *.jsx *.ts *.tsx"),
    ("Web", "*.html *.css *.htm"),
    ("Data", "*.json *.xml *.yaml *.yml"),
    ("Shell", "*.sh *.bash *.bat *.cmd *.ps1"),
    ("Config", "*.ini *.cfg *.conf *.toml"),
    ("Markdown", "*.md"),
]

LANG_MODES = {
    '.py': 'Python', '.pyw': 'Python',
    '.c': 'C', '.h': 'C/C++', '.cpp': 'C++', '.hpp': 'C++',
    '.java': 'Java', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.html': 'HTML', '.css': 'CSS', '.json': 'JSON', '.xml': 'XML',
    '.sh': 'Shell', '.bat': 'Batch', '.md': 'Markdown',
    '.txt': 'Text', '.yaml': 'YAML', '.yml': 'YAML',
}


# ══════════════════════════════════════════════════════════════════════════════
# THEMES
# ══════════════════════════════════════════════════════════════════════════════

THEMES = {
    'dark': {
        'name': 'Dark',
        'text_bg': '#1e1e1e', 'text_fg': '#d4d4d4',
        'line_bg': '#252526', 'line_fg': '#858585',
        'cursor': '#ffffff', 'select_bg': '#264f78',
        'sidebar_bg': '#252526', 'sidebar_fg': '#cccccc',
        'toolbar_bg': '#333333', 'status_bg': '#007acc',
        'chat_bg': '#1e1e1e', 'chat_user': '#569cd6', 'chat_ai': '#4ec9b0',
    },
    'light': {
        'name': 'Light',
        'text_bg': '#ffffff', 'text_fg': '#000000',
        'line_bg': '#f3f3f3', 'line_fg': '#237893',
        'cursor': '#000000', 'select_bg': '#add6ff',
        'sidebar_bg': '#f3f3f3', 'sidebar_fg': '#333333',
        'toolbar_bg': '#dddddd', 'status_bg': '#007acc',
        'chat_bg': '#ffffff', 'chat_user': '#0000ff', 'chat_ai': '#008000',
    },
    'monokai': {
        'name': 'Monokai',
        'text_bg': '#272822', 'text_fg': '#f8f8f2',
        'line_bg': '#3e3d32', 'line_fg': '#90908a',
        'cursor': '#f8f8f0', 'select_bg': '#49483e',
        'sidebar_bg': '#3e3d32', 'sidebar_fg': '#f8f8f2',
        'toolbar_bg': '#414339', 'status_bg': '#75715e',
        'chat_bg': '#272822', 'chat_user': '#66d9ef', 'chat_ai': '#a6e22e',
    },
    'nord': {
        'name': 'Nord',
        'text_bg': '#2e3440', 'text_fg': '#d8dee9',
        'line_bg': '#3b4252', 'line_fg': '#616e88',
        'cursor': '#d8dee9', 'select_bg': '#434c5e',
        'sidebar_bg': '#3b4252', 'sidebar_fg': '#eceff4',
        'toolbar_bg': '#434c5e', 'status_bg': '#5e81ac',
        'chat_bg': '#2e3440', 'chat_user': '#88c0d0', 'chat_ai': '#a3be8c',
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# EDITOR TAB
# ══════════════════════════════════════════════════════════════════════════════

class EditorTab(tk.Frame):
    def __init__(self, master, theme, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.filename = None
        self.theme = theme
        self.language = 'Text'
        self.modified = False
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self, orient="vertical")
        self.v_scroll.grid(row=0, column=2, sticky="ns")
        self.h_scroll = ttk.Scrollbar(self, orient="horizontal")
        self.h_scroll.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Line numbers
        self.line_nums = tk.Text(self, width=5, padx=4, takefocus=0, border=0,
                                 bg=theme['line_bg'], fg=theme['line_fg'],
                                 state='disabled', wrap='none', font=("Consolas", 11))
        self.line_nums.grid(row=0, column=0, sticky="ns")

        # Text area
        self.text = CustomText(self, wrap="none", undo=True,
                               bg=theme['text_bg'], fg=theme['text_fg'],
                               insertbackground=theme['cursor'],
                               selectbackground=theme['select_bg'],
                               font=("Consolas", 11), tabs=("4c",))
        self.text.grid(row=0, column=1, sticky="nsew")

        # Configure scrolling
        self.text.config(yscrollcommand=self._on_yscroll, xscrollcommand=self.h_scroll.set)
        self.v_scroll.config(command=self._scroll_both)
        self.h_scroll.config(command=self.text.xview)

        # Events
        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        self.text.bind("<Key>", self._on_key)
        
        self._on_change()

    def _on_yscroll(self, first, last):
        self.v_scroll.set(first, last)
        self.line_nums.yview_moveto(first)

    def _scroll_both(self, *args):
        self.text.yview(*args)
        self.line_nums.yview(*args)

    def _on_change(self, event=None):
        self._update_line_nums()
        self.event_generate("<<CursorChange>>")

    def _on_key(self, event=None):
        if event and event.keysym not in ('Shift_L', 'Shift_R', 'Control_L', 'Control_R', 'Alt_L', 'Alt_R'):
            self.modified = True

    def _update_line_nums(self):
        line_count = int(self.text.index('end-1c').split('.')[0])
        txt = '\n'.join(str(i) for i in range(1, line_count + 1)) + '\n'
        self.line_nums.config(state='normal')
        self.line_nums.delete('1.0', 'end')
        self.line_nums.insert('1.0', txt)
        self.line_nums.yview_moveto(self.text.yview()[0])
        self.line_nums.config(state='disabled')

    def apply_theme(self, theme):
        self.theme = theme
        self.line_nums.config(bg=theme['line_bg'], fg=theme['line_fg'])
        self.text.config(bg=theme['text_bg'], fg=theme['text_fg'],
                         insertbackground=theme['cursor'], selectbackground=theme['select_bg'])

    def detect_language(self):
        if self.filename:
            _, ext = os.path.splitext(self.filename)
            self.language = LANG_MODES.get(ext.lower(), 'Text')


# ══════════════════════════════════════════════════════════════════════════════
# AI SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

class AISidebar(tk.Frame):
    def __init__(self, master, theme, get_selected_code, **kwargs):
        super().__init__(master, **kwargs)
        self.theme = theme
        self.get_selected_code = get_selected_code
        
        self.config(bg=theme['sidebar_bg'])
        
        # Title
        title = tk.Label(self, text="🤖 AI Assistant", font=("Segoe UI", 12, "bold"),
                         bg=theme['sidebar_bg'], fg=theme['sidebar_fg'])
        title.pack(pady=10, padx=10, anchor='w')
        
        # AI Tools buttons
        tools_frame = tk.Frame(self, bg=theme['sidebar_bg'])
        tools_frame.pack(fill='x', padx=10)
        
        self.btn_explain = tk.Button(tools_frame, text="📚 Explain", command=self._explain,
                                     relief='flat', bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
        self.btn_explain.pack(fill='x', pady=2)
        
        self.btn_debug = tk.Button(tools_frame, text="🐛 Debug", command=self._debug,
                                   relief='flat', bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
        self.btn_debug.pack(fill='x', pady=2)
        
        self.btn_refactor = tk.Button(tools_frame, text="🔄 Refactor", command=self._refactor,
                                      relief='flat', bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
        self.btn_refactor.pack(fill='x', pady=2)
        
        self.btn_docstring = tk.Button(tools_frame, text="📝 Docstring", command=self._docstring,
                                       relief='flat', bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
        self.btn_docstring.pack(fill='x', pady=2)
        
        # Separator
        ttk.Separator(self, orient='horizontal').pack(fill='x', pady=10, padx=10)
        
        # Chat area
        chat_label = tk.Label(self, text="💬 Chat", font=("Segoe UI", 10, "bold"),
                              bg=theme['sidebar_bg'], fg=theme['sidebar_fg'])
        chat_label.pack(anchor='w', padx=10)
        
        # Chat display
        self.chat_display = scrolledtext.ScrolledText(self, height=15, wrap='word',
                                                       bg=theme['chat_bg'], fg=theme['sidebar_fg'],
                                                       font=("Consolas", 9))
        self.chat_display.pack(fill='both', expand=True, padx=10, pady=5)
        self.chat_display.config(state='disabled')
        
        # Chat input
        input_frame = tk.Frame(self, bg=theme['sidebar_bg'])
        input_frame.pack(fill='x', padx=10, pady=5)
        
        self.chat_input = tk.Entry(input_frame, bg=theme['text_bg'], fg=theme['text_fg'],
                                   insertbackground=theme['cursor'])
        self.chat_input.pack(side='left', fill='x', expand=True)
        self.chat_input.bind('<Return>', self._send_chat)
        
        self.btn_send = tk.Button(input_frame, text="→", command=self._send_chat,
                                  bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
        self.btn_send.pack(side='right', padx=2)
        
        # Welcome message
        self._add_ai_message("🐱 Hi! I'm your local AI assistant.\nNo API needed - I work offline!\n\nSelect code and use the tools above,\nor ask me coding questions!")

    def _add_user_message(self, msg):
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', f"\n👤 You:\n{msg}\n", 'user')
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')

    def _add_ai_message(self, msg):
        self.chat_display.config(state='normal')
        self.chat_display.insert('end', f"\n🤖 AI:\n{msg}\n", 'ai')
        self.chat_display.config(state='disabled')
        self.chat_display.see('end')

    def _send_chat(self, event=None):
        msg = self.chat_input.get().strip()
        if msg:
            self._add_user_message(msg)
            response = AIAgent.chat_response(msg)
            self._add_ai_message(response)
            self.chat_input.delete(0, 'end')

    def _explain(self):
        code = self.get_selected_code()
        if code:
            self._add_user_message(f"Explain this code:\n{code[:100]}...")
            result = AIAgent.explain_code(code)
            self._add_ai_message(result)
        else:
            self._add_ai_message("⚠️ Select some code first!")

    def _debug(self):
        code = self.get_selected_code()
        if code:
            self._add_user_message(f"Debug this code:\n{code[:100]}...")
            result = AIAgent.find_bugs(code)
            self._add_ai_message(result)
        else:
            self._add_ai_message("⚠️ Select some code first!")

    def _refactor(self):
        code = self.get_selected_code()
        if code:
            self._add_user_message(f"Refactor suggestions:\n{code[:100]}...")
            result = AIAgent.refactor_code(code)
            self._add_ai_message(result)
        else:
            self._add_ai_message("⚠️ Select some code first!")

    def _docstring(self):
        code = self.get_selected_code()
        if code:
            self._add_user_message(f"Generate docstring:\n{code[:100]}...")
            result = AIAgent.generate_docstring(code)
            self._add_ai_message(f"📝 Docstring:\n{result}")
        else:
            self._add_ai_message("⚠️ Select a function or class first!")

    def apply_theme(self, theme):
        self.theme = theme
        self.config(bg=theme['sidebar_bg'])
        for widget in self.winfo_children():
            try:
                if isinstance(widget, tk.Label):
                    widget.config(bg=theme['sidebar_bg'], fg=theme['sidebar_fg'])
                elif isinstance(widget, tk.Button):
                    widget.config(bg=theme['toolbar_bg'], fg=theme['sidebar_fg'])
                elif isinstance(widget, tk.Frame):
                    widget.config(bg=theme['sidebar_bg'])
            except:
                pass
        self.chat_display.config(bg=theme['chat_bg'], fg=theme['sidebar_fg'])
        self.chat_input.config(bg=theme['text_bg'], fg=theme['text_fg'])


# ══════════════════════════════════════════════════════════════════════════════
# COMPLETION POPUP
# ══════════════════════════════════════════════════════════════════════════════

class CompletionPopup(tk.Toplevel):
    def __init__(self, master, x, y, completions, callback):
        super().__init__(master)
        self.callback = callback
        self.completions = completions
        
        self.wm_overrideredirect(True)
        self.geometry(f"+{x}+{y}")
        
        self.listbox = tk.Listbox(self, height=min(10, len(completions)), width=40,
                                   font=("Consolas", 10), selectmode='single')
        self.listbox.pack()
        
        for name, _ in completions:
            self.listbox.insert('end', name)
        
        if completions:
            self.listbox.select_set(0)
        
        self.listbox.bind('<Return>', self._select)
        self.listbox.bind('<Double-Button-1>', self._select)
        self.listbox.bind('<Escape>', lambda e: self.destroy())
        self.listbox.bind('<FocusOut>', lambda e: self.destroy())
        
        self.listbox.focus_set()

    def _select(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            idx = selection[0]
            _, template = self.completions[idx]
            self.callback(template)
        self.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

class CursorNotepad(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("🐱 Cat's Cursor 2.0 - AI Code Editor")
        self.geometry("1200x700")
        
        self.current_theme = THEMES['dark']
        self.tab_counter = 1
        self.sidebar_visible = True
        
        # Main container
        self.main_pane = tk.PanedWindow(self, orient='horizontal', sashwidth=4)
        self.main_pane.pack(fill='both', expand=True)
        
        # Editor area (left)
        self.editor_frame = tk.Frame(self.main_pane)
        self.main_pane.add(self.editor_frame, width=850)
        
        # Toolbar
        self._create_toolbar()
        
        # Notebook
        self.notebook = ttk.Notebook(self.editor_frame)
        self.notebook.pack(expand=True, fill='both')
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)
        
        # Status bar
        self._create_statusbar()
        
        # AI Sidebar (right)
        self.sidebar = AISidebar(self.main_pane, self.current_theme, self._get_selected_code)
        self.main_pane.add(self.sidebar, width=300)
        
        # Menus
        self._create_menus()
        
        # Shortcuts
        self.bind("<Control-n>", lambda e: self.new_file())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())
        self.bind("<Control-Shift-S>", lambda e: self.save_as())
        self.bind("<Control-w>", lambda e: self.close_tab())
        self.bind("<Control-period>", lambda e: self._show_completion())
        self.bind("<Control-slash>", lambda e: self._insert_docstring())
        self.bind("<Control-b>", lambda e: self._toggle_sidebar())
        self.bind("<Control-g>", lambda e: self._goto_line())
        self.bind("<Control-f>", lambda e: self._show_find())
        
        # Events
        self.bind_all("<<CursorChange>>", self._update_status)
        self.bind_all("<KeyRelease>", self._update_status)
        self.bind_all("<ButtonRelease-1>", self._update_status)
        
        # Initial tab
        self.new_file()

    def _create_toolbar(self):
        toolbar = tk.Frame(self.editor_frame, bg=self.current_theme['toolbar_bg'])
        toolbar.pack(fill='x')
        
        buttons = [
            ("📄", self.new_file, "New (Ctrl+N)"),
            ("📂", self.open_file, "Open (Ctrl+O)"),
            ("💾", self.save_file, "Save (Ctrl+S)"),
            ("|", None, None),
            ("🔍", self._show_find, "Find (Ctrl+F)"),
            ("|", None, None),
            ("✨", self._show_completion, "AI Complete (Ctrl+.)"),
            ("📝", self._insert_docstring, "Docstring (Ctrl+/)"),
            ("🐛", lambda: self.sidebar._debug(), "Debug"),
            ("🔄", lambda: self.sidebar._refactor(), "Refactor"),
            ("|", None, None),
            ("👁️", self._toggle_sidebar, "Toggle AI (Ctrl+B)"),
        ]
        
        for text, cmd, tip in buttons:
            if text == "|":
                ttk.Separator(toolbar, orient='vertical').pack(side='left', fill='y', padx=5, pady=2)
            else:
                btn = tk.Button(toolbar, text=text, command=cmd, relief='flat',
                               bg=self.current_theme['toolbar_bg'], fg='white', padx=8)
                btn.pack(side='left', padx=1)
                if tip:
                    self._create_tooltip(btn, tip)

    def _create_tooltip(self, widget, text):
        def show(event):
            tip = tk.Toplevel(widget)
            tip.wm_overrideredirect(True)
            tip.geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tip, text=text, bg='#ffffe0', relief='solid', borderwidth=1)
            label.pack()
            widget._tip = tip
            widget.after(2000, lambda: tip.destroy() if tip.winfo_exists() else None)
        def hide(event):
            if hasattr(widget, '_tip') and widget._tip.winfo_exists():
                widget._tip.destroy()
        widget.bind('<Enter>', show)
        widget.bind('<Leave>', hide)

    def _create_statusbar(self):
        status = tk.Frame(self.editor_frame, bg=self.current_theme['status_bg'])
        status.pack(fill='x', side='bottom')
        
        self.status_pos = tk.Label(status, text="Ln 1, Col 1", bg=self.current_theme['status_bg'],
                                   fg='white', padx=10)
        self.status_pos.pack(side='left')
        
        self.status_lang = tk.Label(status, text="Python", bg=self.current_theme['status_bg'],
                                    fg='white', padx=10)
        self.status_lang.pack(side='right')
        
        self.status_ai = tk.Label(status, text="🤖 AI Ready", bg=self.current_theme['status_bg'],
                                  fg='#90EE90', padx=10)
        self.status_ai.pack(side='right')

    def _create_menus(self):
        menubar = tk.Menu(self)
        
        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="New", accelerator="Ctrl+N", command=self.new_file)
        file_menu.add_command(label="Open", accelerator="Ctrl+O", command=self.open_file)
        file_menu.add_command(label="Save", accelerator="Ctrl+S", command=self.save_file)
        file_menu.add_command(label="Save As", accelerator="Ctrl+Shift+S", command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", accelerator="Ctrl+W", command=self.close_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", accelerator="Ctrl+Z",
                              command=lambda: self._get_text().edit_undo() if self._get_text() else None)
        edit_menu.add_command(label="Redo", accelerator="Ctrl+Y",
                              command=lambda: self._get_text().edit_redo() if self._get_text() else None)
        edit_menu.add_separator()
        edit_menu.add_command(label="Find", accelerator="Ctrl+F", command=self._show_find)
        edit_menu.add_command(label="Go to Line", accelerator="Ctrl+G", command=self._goto_line)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        
        # AI
        ai_menu = tk.Menu(menubar, tearoff=0)
        ai_menu.add_command(label="AI Complete", accelerator="Ctrl+.", command=self._show_completion)
        ai_menu.add_command(label="Generate Docstring", accelerator="Ctrl+/", command=self._insert_docstring)
        ai_menu.add_separator()
        ai_menu.add_command(label="Explain Code", command=lambda: self.sidebar._explain())
        ai_menu.add_command(label="Debug Code", command=lambda: self.sidebar._debug())
        ai_menu.add_command(label="Refactor Code", command=lambda: self.sidebar._refactor())
        ai_menu.add_separator()
        ai_menu.add_command(label="Toggle Sidebar", accelerator="Ctrl+B", command=self._toggle_sidebar)
        menubar.add_cascade(label="AI", menu=ai_menu)
        
        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        for theme_key, theme in THEMES.items():
            view_menu.add_command(label=f"{theme['name']} Theme",
                                  command=lambda t=theme: self._apply_theme(t))
        menubar.add_cascade(label="View", menu=view_menu)
        
        self.config(menu=menubar)

    def _get_tab(self):
        tab_name = self.notebook.select()
        return self.nametowidget(tab_name) if tab_name else None

    def _get_text(self):
        tab = self._get_tab()
        return tab.text if tab else None

    def _get_selected_code(self):
        text = self._get_text()
        if not text:
            return ""
        try:
            return text.get("sel.first", "sel.last")
        except tk.TclError:
            return text.get("1.0", "end")

    def new_file(self):
        tab = EditorTab(self.notebook, self.current_theme)
        self.notebook.add(tab, text=f"new {self.tab_counter}")
        self.tab_counter += 1
        self.notebook.select(tab)
        tab.text.focus_set()

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=FILE_TYPES)
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except:
                with open(path, 'r', encoding='latin-1') as f:
                    content = f.read()
            
            tab = EditorTab(self.notebook, self.current_theme)
            tab.text.insert('1.0', content)
            tab.filename = path
            tab.modified = False
            tab.detect_language()
            
            self.notebook.add(tab, text=os.path.basename(path))
            self.notebook.select(tab)
            tab.text.edit_reset()

    def save_file(self):
        tab = self._get_tab()
        if not tab:
            return
        if tab.filename:
            content = tab.text.get('1.0', 'end-1c')
            with open(tab.filename, 'w', encoding='utf-8') as f:
                f.write(content)
            tab.modified = False
        else:
            self.save_as()

    def save_as(self):
        tab = self._get_tab()
        if not tab:
            return
        path = filedialog.asksaveasfilename(defaultextension='.py', filetypes=FILE_TYPES)
        if path:
            content = tab.text.get('1.0', 'end-1c')
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            tab.filename = path
            tab.modified = False
            tab.detect_language()
            self.notebook.tab(tab, text=os.path.basename(path))

    def close_tab(self):
        tab = self._get_tab()
        if tab:
            if tab.modified:
                if not messagebox.askyesno("Close", "Unsaved changes. Close anyway?"):
                    return
            self.notebook.forget(tab)
            if not self.notebook.tabs():
                self.new_file()

    def _on_tab_change(self, event=None):
        tab = self._get_tab()
        if tab:
            self.title(f"🐱 Cat's Cursor 2.0 - {tab.filename or 'new'}")
            self._update_status()

    def _update_status(self, event=None):
        tab = self._get_tab()
        if not tab:
            return
        try:
            pos = tab.text.index('insert')
            line, col = pos.split('.')
            self.status_pos.config(text=f"Ln {line}, Col {int(col)+1}")
            self.status_lang.config(text=tab.language)
        except:
            pass

    def _toggle_sidebar(self):
        if self.sidebar_visible:
            self.main_pane.forget(self.sidebar)
        else:
            self.main_pane.add(self.sidebar, width=300)
        self.sidebar_visible = not self.sidebar_visible

    def _show_completion(self):
        text = self._get_text()
        if not text:
            return
        
        # Get current word
        pos = text.index('insert')
        line_start = f"{pos.split('.')[0]}.0"
        line_text = text.get(line_start, pos)
        
        # Find prefix
        match = re.search(r'(\w+)$', line_text)
        if match:
            prefix = match.group(1)
            completions = AIAgent.get_completion(prefix)
            
            if completions:
                # Get screen position
                x, y, _, h = text.bbox('insert')
                x += text.winfo_rootx()
                y += text.winfo_rooty() + h
                
                def insert_completion(template):
                    # Delete prefix
                    text.delete(f"insert-{len(prefix)}c", 'insert')
                    text.insert('insert', template)
                
                CompletionPopup(self, x, y, completions, insert_completion)

    def _insert_docstring(self):
        text = self._get_text()
        if not text:
            return
        
        # Get current line or selection
        try:
            code = text.get('sel.first', 'sel.last')
        except:
            line = text.get('insert linestart', 'insert lineend')
            code = line
        
        docstring = AIAgent.generate_docstring(code)
        
        # Insert after current line
        text.insert('insert lineend', '\n    ' + docstring)

    def _goto_line(self):
        dialog = tk.Toplevel(self)
        dialog.title("Go to Line")
        dialog.geometry("200x80")
        dialog.transient(self)
        
        tk.Label(dialog, text="Line:").pack(pady=5)
        entry = tk.Entry(dialog)
        entry.pack(pady=5)
        entry.focus_set()
        
        def go():
            try:
                line = int(entry.get())
                text = self._get_text()
                if text:
                    text.mark_set('insert', f'{line}.0')
                    text.see(f'{line}.0')
                dialog.destroy()
            except:
                pass
        
        entry.bind('<Return>', lambda e: go())
        tk.Button(dialog, text="Go", command=go).pack()

    def _show_find(self):
        dialog = tk.Toplevel(self)
        dialog.title("Find")
        dialog.geometry("300x80")
        dialog.transient(self)
        
        frame = tk.Frame(dialog)
        frame.pack(pady=10, padx=10, fill='x')
        
        tk.Label(frame, text="Find:").pack(side='left')
        entry = tk.Entry(frame, width=25)
        entry.pack(side='left', padx=5)
        entry.focus_set()
        
        def find():
            pattern = entry.get()
            text = self._get_text()
            if text and pattern:
                text.tag_remove('found', '1.0', 'end')
                pos = text.search(pattern, 'insert+1c', stopindex='end')
                if not pos:
                    pos = text.search(pattern, '1.0', stopindex='insert')
                if pos:
                    end = f"{pos}+{len(pattern)}c"
                    text.tag_add('found', pos, end)
                    text.tag_config('found', background='yellow')
                    text.mark_set('insert', end)
                    text.see(pos)
        
        entry.bind('<Return>', lambda e: find())
        tk.Button(frame, text="Find", command=find).pack(side='left')

    def _apply_theme(self, theme):
        self.current_theme = theme
        for tab_id in self.notebook.tabs():
            tab = self.nametowidget(tab_id)
            tab.apply_theme(theme)
        self.sidebar.apply_theme(theme)


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = CursorNotepad()
    app.mainloop()
