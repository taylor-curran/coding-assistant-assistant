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

## Coding Agent Requests for Web Scraping Use Case 

1. Access to Returned Data for Enhanced Code Generation

    I need the agent to have direct access to the data returned from web scraping requests. Currently, the agent writes parsing logic based solely on the source code without actually "seeing" the data. With this change, the agent would generate more precise and context-aware code, reducing the guesswork involved in handling diverse HTML structures.
2. Automated Code Cleanup Using Stack Trace Information

    After the agent generates and executes the code, it currently adds numerous lines in an attempt to cover all potential scenarios—often leading to a cluttered and inefficient codebase. By providing the agent with the stack trace, which details exactly which code paths were executed, we give it concrete evidence of what worked and what didn’t. This information is crucial for the agent to perform an effective cleanup, removing redundant lines and streamlining the final code. In essence, the stack trace acts like a roadmap, highlighting the parts of the code that are necessary and flagging the unnecessary ones, ultimately optimizing the code generated from its blind attempts.

This two-pronged approach not only enhances the initial code generation but also ensures that the final product is clean, efficient, and maintainable.
