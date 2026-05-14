"""
Backward compatibility: pehle tum `python app.py` se chala rahe the.

Ab recommended entry `run.py` hai, lekin purani command bhi kaam karti rahe.
"""

from expense_tracker import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
