# Project Setup & Run Guide

This guide explains how to set up the environment, install all required dependencies, and run the project.

---

## 1. Create a Virtual Environment

```bash
python -m venv myenv
````

---

## 2. Activate the Environment

* On **Windows (PowerShell)**:

  ```bash
  myenv\Scripts\Activate
  ```

* On **Mac/Linux**:

  ```bash
  source myenv/bin/activate
  ```

---

## 3. Install Dependencies

Run the following command inside the activated environment:

```bash
pip install flask requests gspread oauth2client pynacl opencv-python numpy matplotlib pandas torch torchvision torchaudio tensorflow
```

---
### enter your TOGGL_API_TOKEN and DISCORD_WEBHOOK_URL.
---
## 4. Run the Script

```bash
python main.py
```

---


