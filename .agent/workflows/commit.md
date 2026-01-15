---
description: Create a new git commit for uncommitted changes
---

1. Analyze pending changes

```bash
git status --porcelain
```

2. Group changes into logical, atomic units.

   - Separate bug fixes, features, and refactors.
   - Do NOT include unrelated changes in the same commit.

3. For each atomic change:

   - Stage relevant files only: `git add <file1> <file2>...`
   - Use `git add -p` for partial staging if needed to split changes within a single file.

4. Write a high-quality commit message:

   - **Subject**: One-line summary (max 50 chars), imperative mood (e.g., "Add feature X", not "Fixed feature X").
   - **Body**: Detailed explanation of **why** the change was made, wrapped at 72 chars. Explain the problem and the reasoning behind the solution.

   ```text
   Subject: [feat|fix|docs|refactor|test]: Brief summary

   Detailed description of the motivation for this change.
   What problem does it solve?
   Are there any side effects?
   ```

5. Verify the commit history

```bash
git log -n 5 --oneline --graph
```
