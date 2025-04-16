"""Module for automatic Git commits."""

from datetime import datetime
import random

from colorama import Fore, Style, init
from git import Repo, exc

import lists

# Initialize colorama
init(autoreset=True)


def print_section(title, title_color, body, body_color):
    """Prints a formatted section with a title and body text in specified colors.

    Args:
        title (str): The title of the section.
        title_color (str): The color for the title.
        body (str): The body text of the section.
        body_color (str): The color for the body text.
    """
    print(title_color + f"--- {title} ---")
    print(body_color + body + "\n")


def auto_commit(repo_path, readme_path, commit_prefix):
    """Performs an automatic commit in a Git repository, updating a README file.

    Generates a commit message using random animal and gemstone names, updates
    the README file with a timestamp, commits the changes, and pushes to origin.

    Args:
        repo_path (str): The file path to the Git repository.
        readme_path (str): The file path to the README file within the repository.
        commit_prefix (str): A prefix to use in the commit message.
    """
    # Print the current timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print_section("Timestamp", Fore.MAGENTA, timestamp, Style.RESET_ALL)

    # Generate a random animal name and gemstone
    random_animal = random.choice(lists.animals)
    random_gemstone = random.choice(lists.gemstones)

    # Open the repository
    repo = Repo(repo_path)

    # Check the current status
    status = repo.git.status()
    print_section("Current Status", Fore.BLUE, status, Style.RESET_ALL)

    # Read the README.md content and replace the last update line or append a new one
    update_line = f'Updated on {timestamp}\n'

    with open(readme_path, 'r', encoding='utf-8') as readme_file:
        lines = readme_file.readlines()

    if lines and lines[-1].startswith('Updated on'):
        lines[-1] = update_line
    else:
        lines.append(update_line)

    with open(readme_path, 'w', encoding='utf-8') as readme_file:
        readme_file.writelines(lines)

    # Add README.md to the index
    repo.index.add([readme_path])

    # Create a commit
    commit_message = f'{commit_prefix} {random_gemstone} {random_animal}'
    repo.index.commit(commit_message)

    # Print commit message
    print_section("Commit Message", Fore.YELLOW, commit_message, Style.RESET_ALL)

    # Print the diff of the commit
    commit_diff = repo.git.diff('HEAD~1', 'HEAD')
    print_section("Commit Diff", Fore.CYAN, commit_diff, Style.RESET_ALL)

    # Push the changes to the remote repository
    try:
        origin = repo.remote(name='origin')
        origin.push()
        # Print push success
        print_section("Push Success", Fore.GREEN, "Push completed successfully.", Style.RESET_ALL)
    except exc.GitCommandError as e:
        print_section("Error while pushing", Fore.RED, str(e), Style.RESET_ALL)
