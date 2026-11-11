# AI-assisted source discovery

External provider calls are **optional**. Source discovery asks a search-enabled API for candidate organizations with an official U.S. printed-mail request **and** a published postal opt-out method. AI output is untrusted research, not proof. It is never automatically added as an enabled default.

Supported providers use their published APIs. Configure a key in the environment:

```sh
export OPENAI_API_KEY='your-api-key'
python3 spamalot.py discover --provider openai --category 'printed NGO newsletters'

export GEMINI_API_KEY='your-api-key'
python3 spamalot.py discover --provider gemini --category 'paper catalogs' --check

export PERPLEXITY_API_KEY='your-api-key'
python3 spamalot.py discover --provider perplexity --category 'printed religious periodicals'
```

Use `--model` to choose a compatible provider model. Provider APIs, model IDs, and prices can change; verify them at the provider's documentation.

Review the queue:

```sh
python3 spamalot.py candidates
python3 spamalot.py promote-candidate --id <candidate-uuid>
python3 spamalot.py check-sources --source <slug>
python3 spamalot.py enable-source --source <slug>
```

A candidate must genuinely offer free physical postal delivery, not an email newsletter, print-at-home file, paid trial, or irrelevant contact page. Review postal removal instructions, eligibility, privacy terms, and any bundled marketing channel.

**Privacy:** The research prompt does not include the recipient's private address, profile, or local history. API keys remain in local environment variables. Third-party APIs may retain requests under their own policies and may charge for usage.

See [[Sources-and-Formats]] and [[Source-Health]].