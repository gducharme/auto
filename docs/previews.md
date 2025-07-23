# Managing Post Previews

This guide covers how Auto generates previews for scheduled posts, how to edit them, and how the scheduler publishes them.

## Generating a Preview

Previews are short templates used when a post is published to a social network. They can be generated manually or scheduled as a task.

### Immediate Generation

Run the `generate-preview` command with the post ID and network:

```bash
python -m auto.cli publish generate-preview --post-id <id> --network mastodon
```

This fetches the post from the database and generates a preview. The text sent
to the LLM is loaded from the file specified by the `PREVIEW_TEMPLATE_PATH`
environment variable or `src/auto/templates/medium_preview_prompt.txt` by default. The
template receives the post content via `{{ content }}` and the original URL as
`{{ post_id }}`. The previous preview is removed before the new one is saved. When `--use-llm` is
provided, a local LLM creates the summary using the same configuration as the
`dspy-exp` experiment (`ollama_chat/gemma3:4b` on `http://localhost:11434`).
Otherwise the post title or summary is used.

### Generating via Task

You can run the `create_preview` command to generate the preview using a network-specific template:

```bash
python -m auto.cli publish create-preview --post-id <id> --network mastodon
```

## Editing a Preview

Previews can be edited interactively before publishing:

```bash
python -m auto.cli publish edit-preview --post-id <id> --network mastodon
```

Your editor opens with the current template. Saving the file updates the `post_previews` entry for that network.

## Deleting a Preview

Remove an existing preview if you no longer want to keep it:

```bash
python -m auto.cli publish delete-preview --post-id <id> --network mastodon
```

## Scheduler Pickup

The background scheduler looks for due tasks in the `tasks` table. When it encounters a `create_preview` task it calls `auto.preview.create_preview` to generate the preview. When a `publish_post` task runs, the scheduler loads the corresponding preview, renders it with Jinja, and posts the result via the appropriate plugin.

Make sure the scheduler is running so it can process the queued tasks:

```bash
python -m auto.scheduler
```

If the scheduler reports that the `tasks` table is missing, run the migrations or ensure the database is initialized before starting it.
