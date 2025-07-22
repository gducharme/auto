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
environment variable or `src/auto/templates/preview_prompt.txt` by default. The
previous preview is removed before the new one is saved. When `--use-llm` is
provided, a local LLM creates the summary; otherwise the post title or summary
is used.

### Scheduling Generation

Instead of generating the preview immediately, you can create a `create_preview` task:

```bash
python -m auto.cli publish create-preview --post-id <id> --network mastodon --when "+10m"
```

The `--when` flag accepts absolute timestamps or relative offsets. The task is saved in the `tasks` table with status `pending`.

## Editing a Preview

Previews can be edited interactively before publishing:

```bash
python -m auto.cli publish edit-preview --post-id <id> --network mastodon
```

Your editor opens with the current template. Saving the file updates the `post_previews` entry for that network.

## Scheduler Pickup

The background scheduler looks for due tasks in the `tasks` table. When it encounters a `create_preview` task it calls `auto.preview.create_preview` to generate the preview. When a `publish_post` task runs, the scheduler loads the corresponding preview, renders it with Jinja, and posts the result via the appropriate plugin.

Make sure the scheduler is running so it can process the queued tasks:

```bash
python -m auto.scheduler
```

If the scheduler reports that the `tasks` table is missing, run the migrations or ensure the database is initialized before starting it.
