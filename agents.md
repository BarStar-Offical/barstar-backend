# Agents
- When you make changes to the development workflow, like adding environment variables or new services, document the changes in a README.md where appropriate. If one does not exist, create it and document add it to the main README.md.
- If you add or remove API routes, ensure they are documented in the relevant API documentation files.
- If you notice inconsistencies or outdated information in the README.md or other documentation files, update them to reflect the current state of the project.
- When you are finished with your changes, add a summary of what was changed to the agent-log.md file. You do not need to document every small change, just the significant ones that affect the development workflow or project structure.
- You cannot make changes directly to the alembic/versions/ files. Instead, you must modify the alembic/script.py.mako file so that future migrations will include your changes.
