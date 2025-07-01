# Project Workflow instructions

## New task planning
- First think through the problem, read the codebase for relevant files, and write 
a plan to tasks/issue-NNN (e.g. 001, 002, 003)>.md.
-  The plan should have a list of todo items that you can check off as you complete them
- Before you begin working, check in with me and I will verify the plan.

## Implementation
- Begin working on the todo items, marking them as complete as you go.
- Please every step of the way just give me a high level explanation of what changes you made
- Make every task and code change you do as simple as possible. We want to avoid making any massive or complex changes. Every change should impact as little code as possible. Everything is about simplicity.
- Finally, add a review section to the tasks file with a summary of the changes you made and any other relevant information.

## Development guidelines
- Use trunk based development. Every particular task will be one commit and push to
github repo
- All new functionality must be covered by unit tests
- Please check through all the code you just wrote and make sure it follows security best practices. make sure there are no sensitive information in the front and and there are no vulnerabilities that can be exploited