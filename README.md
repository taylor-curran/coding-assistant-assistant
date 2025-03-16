## Installation 


### 1. Clone the Repository 


Clone the repository to your local machine:



```bash
git clone https://github.com/taylor-curran/coding-assistant-assistant.git
cd coding-assistant-assistant
```


### 2. Create and Activate the Virtual Environment 


Use uv to create a virtual environment. This isolates your project’s dependencies:



```bash
uv venv
```


### 3. Sync Dependencies from the Lock File 

Your repository includes a `uv.lock` file which contains the exact dependency versions. Sync your environment with the lock file by running:


```bash
uv sync
```

This command installs all the required packages as specified in the `pyproject.toml` and locked in `uv.lock`.

### 4. Install Playwright Browsers 


Playwright requires browser binaries to operate. Install these with:



```bash
playwright install
```


## **TODO: Fix the uv run command**
### 5. Running Your Application 


Once your environment is set up, you can run your application using uv. For example, to run a module:



```bash
uv run -m src.your_module
```



---