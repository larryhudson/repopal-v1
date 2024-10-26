# To dos

- Get the designed stuff up and running

- Write up a document about the 'automatic code review' use case
  - this would watch for new pull requests in a repo and do a first pass of a 'review'
  - it would do this by cloning the pull request branch, looking at the changed files, and passing these into an LLM.
  - if needed, it can automatically create a PR with recommended changes to the original PR branch.
  - if it is all ok, then it can post a comment in response to the PR saying 'this looks good to me'.
  - we need to write up a document about this use case, including a plan of what we need to get done to make this use case happen.

- Write up a document about the 'automatic Linear ticket solver' use case
  - this would watch for new Linear tickets, and try to solve them by creating a new PR and then linking it to the Linear ticket, and then creating a comment on the Linear ticket.

- Johan's idea about something that can generate diagrams, documentation about code

- Bigger idea about using API integrations for knowledge / context lookups
  - To be able to solve problems well, the LLM needs good context.
  - At work, context is spread across GitHub PRs, Linear tickets, Notion pages, Slack messages.
  - Not sure how effective these API searches will be

- Maybe something that is a starting point here is: using an API to look up the full content of mentioned Linear tickets / Slack threads / Notion pages
  - You could call this a 'Link expander' or something
