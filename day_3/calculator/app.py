# calculator.py
# Fixed layout so operator column (orange) is fully visible.
# Same features: safe evaluation, keypad, keyboard support.

import tkinter as tk
from tkinter import ttk
import ast
import operator as op
import re

ALLOWED_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
    ast.Mod: op.mod,
}

def safe_eval(expr: str):
    expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")
    expr = re.sub(r'(\d+(\.\d+)?)\%', r'(\1/100)', expr)
    try:
        node = ast.parse(expr, mode='eval')
    except Exception:
        raise ValueError("Invalid expression")
    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Num):
            return node.n
        if hasattr(ast, "Constant") and isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Invalid constant")
        if isinstance(node, ast.BinOp):
            left = _eval(node.left)
            right = _eval(node.right)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                return ALLOWED_OPERATORS[op_type](left, right)
            raise ValueError("Operator not allowed")
        if isinstance(node, ast.UnaryOp):
            operand = _eval(node.operand)
            op_type = type(node.op)
            if op_type in ALLOWED_OPERATORS:
                return ALLOWED_OPERATORS[op_type](operand)
            raise ValueError("Unary operator not allowed")
        raise ValueError("Invalid expression")
    return _eval(node)

class Calculator:
    def __init__(self, root):
        self.root = root
        root.title("Calculator")
        root.resizable(False, False)

        # fonts and sizes
        self.font_title = ("Segoe UI", 20, "bold")
        self.font_display = ("Segoe UI", 26, "bold")
        self.font_btn = ("Segoe UI", 14, "bold")

        # outer frame with extra right padding to avoid clipping
        outer = ttk.Frame(root, padding=(12,12,16,12))  # left,top,right,bottom
        outer.grid(row=0, column=0, sticky="nsew")

        # allow root to expand minimally so buttons fit
        root.update_idletasks()
        root.geometry("420x560")       # wider than before so orange column fits
        root.minsize(420, 480)

        title = ttk.Label(outer, text="Calculator", font=self.font_title)
        title.grid(row=0, column=0, columnspan=4, pady=(0,8))

        # Display: use Entry so text is right-aligned and scrolls if long
        self.display_var = tk.StringVar(value="0")
        self.display = tk.Entry(outer, textvariable=self.display_var, font=self.font_display,
                                justify="right", bd=2, relief="sunken", bg="white", fg="#052a66",
                                insertwidth=0)
        self.display.grid(row=1, column=0, columnspan=4, sticky="we", pady=(0,10), ipady=6)

        # Configure column weights so all four columns expand equally
        for c in range(4):
            outer.grid_columnconfigure(c, weight=1, minsize=80)

        # keypad layout and appearance
        buttons = [
            [("C", self.clear_display), ("⌫", self.backspace), ("%", lambda: self.add_text("%")), ("÷", lambda: self.add_text("÷"))],
            [("7", lambda: self.add_text("7")), ("8", lambda: self.add_text("8")), ("9", lambda: self.add_text("9")), ("×", lambda: self.add_text("×"))],
            [("4", lambda: self.add_text("4")), ("5", lambda: self.add_text("5")), ("6", lambda: self.add_text("6")), ("-", lambda: self.add_text("-"))],
            [("1", lambda: self.add_text("1")), ("2", lambda: self.add_text("2")), ("3", lambda: self.add_text("3")), ("+", lambda: self.add_text("+"))],
            [("±", self.toggle_sign), ("0", lambda: self.add_text("0")), (".", lambda: self.add_text(".")), ("=", self.calculate)],
        ]

        row_index = 2
        for r in buttons:
            col_index = 0
            for (text, cmd) in r:
                btn = tk.Button(outer, text=text, command=cmd, font=self.font_btn)
                # style coloring
                if text in ("÷", "×", "-", "+", "="):
                    btn.configure(bg="#f07a24", fg="white", activebackground="#ff8f3a", bd=0)
                elif text in ("C", "⌫"):
                    btn.configure(bg="#9fb4c8", fg="white", activebackground="#b6c9d6", bd=0)
                elif text == "%":
                    btn.configure(bg="#ffd200", fg="#052a66", activebackground="#ffe55a", bd=0)
                else:
                    btn.configure(bg="#ffffff", fg="#052a66", activebackground="#e6f0f7", bd=0)

                # make sure operators are visually a little wider
                btn.grid(row=row_index, column=col_index, padx=8, pady=8, ipadx=6, ipady=14, sticky="nsew")
                col_index += 1
            row_index += 1

        # Keyboard bindings
        root.bind("<Key>", self.on_key)
        root.bind("<Return>", lambda e: self.calculate())
        root.bind("<KP_Enter>", lambda e: self.calculate())
        root.bind("<Escape>", lambda e: self.clear_display())
        root.bind("<BackSpace>", lambda e: self.backspace())

    def clear_display(self):
        self.display_var.set("0")

    def backspace(self):
        s = self.display_var.get()
        if s in ("Error", "0"):
            self.display_var.set("0")
            return
        s = s[:-1]
        if s == "" or s == "-":
            self.display_var.set("0")
        else:
            self.display_var.set(s)

    def add_text(self, txt):
        s = self.display_var.get()
        if s == "0" or s == "Error":
            s = ""
        s = s + txt
        if len(s) > 100:
            s = s[:100]
        self.display_var.set(s)

    def toggle_sign(self):
        s = self.display_var.get()
        if s in ("0", "Error"):
            return
        if s.startswith("-"):
            self.display_var.set(s[1:])
        else:
            self.display_var.set("-" + s)

    def on_key(self, event):
        ch = event.char
        if ch in "0123456789":
            self.add_text(ch)
        elif ch in "+-*/().":
            if ch == "/":
                self.add_text("÷")
            elif ch == "*":
                self.add_text("×")
            else:
                self.add_text(ch)
        elif ch == "%":
            self.add_text("%")
        elif ch == "\r":
            self.calculate()
        elif ch.lower() == "c":
            self.clear_display()
        elif event.keysym == "BackSpace":
            self.backspace()

    def calculate(self):
        expr = self.display_var.get()
        if expr in ("0", ""):
            return
        try:
            result = safe_eval(expr)
            if isinstance(result, float) and result.is_integer():
                result_text = str(int(result))
            else:
                if isinstance(result, float):
                    result_text = f"{result:.10f}".rstrip('0').rstrip('.')
                else:
                    result_text = str(result)
            self.display_var.set(result_text)
        except ZeroDivisionError:
            self.display_var.set("Error: divide by zero")
        except Exception:
            self.display_var.set("Error")

if __name__ == "__main__":
    root = tk.Tk()
    app = Calculator(root)
    root.mainloop()
